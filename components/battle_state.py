"""
戰鬥狀態組件
─────────────────────────────────────────────
管理戰鬥中的臨時狀態：Buff、狀態異常、護盾等
不持久化，每場戰鬥開始時重置

與舊版的差異：
  - BuffEntry dataclass 移除，改用 Buff 類統一管理
  - apply_buff() 接收完整 Buff 物件，呼叫 on_apply() 鉤子
  - tick_buffs() 呼叫 on_tick()，到期後呼叫 on_expire()
  - 狀態異常（stunned 等）由 Buff.on_apply() 透過 StatusAppliedEvent 管理
    BattleState 本身不再直接維護 _statuses dict
    但保留 has_status() / is_blocked() 供查詢，從 _buffs 推導
"""

from __future__ import annotations
from common.event import (
    EventBus,
    BuffAppliedEvent,
    BuffTickEvent,
    BuffExpiredEvent,
    StatusExpiredEvent,
    WarningEvent,
)
from common.module.buff import Buff, _MECHANIC_ATTRIBUTES


# ══════════════════════════════════════════════
#  阻止行動的狀態集合
# ══════════════════════════════════════════════

BLOCKING_STATUSES = {"stunned", "paralyzed", "silenced", "blinded"}


class BattleState:
    def __init__(self, owner: str = "unknown"):
        self.owner  = owner
        self._buffs: dict[str, Buff] = {}   # buff_name → Buff
        self.shield: float = 0.0

    # ══════════════════════════════════════════
    #  Buff
    # ══════════════════════════════════════════

    def apply_buff(self, buff: Buff) -> None:
        """
        施加 Buff。
        同名 Buff 已存在時刷新持續時間，不重複觸發 on_apply()。
        """
        buff.target = self.owner

        if buff.name in self._buffs:
            self._buffs[buff.name].refresh()
            EventBus.emit(BuffAppliedEvent(
                target=self.owner,
                buff_name=buff.name,
                duration=self._buffs[buff.name].duration,
            ))
            return

        self._buffs[buff.name] = buff
        buff.on_apply()

    def tick_buffs(self) -> None:
        """
        每回合結束時呼叫。
        順序：on_tick() → decrement_duration() → 到期則 on_expire()。
        """
        expired = []
        for name, buff in self._buffs.items():
            buff.on_tick()
            if buff.decrement_duration():
                expired.append(name)
            else:
                EventBus.emit(BuffTickEvent(
                    target=self.owner,
                    buff_name=name,
                    duration_remaining=buff.duration,
                ))

        for name in expired:
            buff = self._buffs.pop(name)
            buff.on_expire()
            # 機制類狀態額外發送 StatusExpiredEvent
            attribute = buff.effect.get("attribute")
            if attribute in _MECHANIC_ATTRIBUTES:
                EventBus.emit(StatusExpiredEvent(
                    target=self.owner,
                    status=attribute,
                ))

    def remove_buff(self, buff_name: str) -> bool:
        """
        主動移除指定 Buff，呼叫 on_expire()。
        回傳是否成功移除。
        """
        if buff_name not in self._buffs:
            EventBus.emit(WarningEvent(
                message=f"{self.owner} 沒有 Buff【{buff_name}】"
            ))
            return False

        buff = self._buffs.pop(buff_name)
        buff.on_expire()
        attribute = buff.effect.get("attribute")
        if attribute in _MECHANIC_ATTRIBUTES:
            EventBus.emit(StatusExpiredEvent(
                target=self.owner,
                status=attribute,
            ))
        return True

    def remove_buffs_by_type(self, buff_type: str) -> int:
        """
        移除指定類型的所有 Buff（"buff" / "debuff"）。
        回傳移除數量。
        """
        targets = [
            name for name, b in self._buffs.items()
            if b.buff_type == buff_type
        ]
        for name in targets:
            self.remove_buff(name)
        return len(targets)

    def remove_all_buffs(self) -> None:
        """移除所有 Buff。"""
        for name in list(self._buffs.keys()):
            self.remove_buff(name)

    def has_buff(self, name: str) -> bool:
        return name in self._buffs

    def get_buff(self, name: str) -> Buff | None:
        return self._buffs.get(name)

    def total_buff_modifier(self, attribute: str) -> float:
        """
        加總所有 Buff 對某屬性的修正值。
        只計算非 tick 的屬性加成類 Buff。
        """
        total = 0.0
        for buff in self._buffs.values():
            if (
                buff.effect.get("attribute") == attribute
                and not buff.effect.get("tick", False)
                and attribute not in _MECHANIC_ATTRIBUTES
            ):
                total += buff.effect.get("value", 0.0)
        return total

    # ══════════════════════════════════════════
    #  狀態異常查詢（從 _buffs 推導）
    # ══════════════════════════════════════════

    def has_status(self, status: str) -> bool:
        """
        檢查是否有指定機制類狀態。
        從 _buffs 中找 effect.attribute == status 的 Buff。
        """
        return any(
            b.effect.get("attribute") == status
            for b in self._buffs.values()
        )

    def is_blocked(self, status: str | None = None) -> bool:
        """
        檢查是否被阻止行動。
        status=None → 任意阻止性狀態
        status=xxx  → 特定狀態
        """
        if status:
            return self.has_status(status)
        return any(self.has_status(s) for s in BLOCKING_STATUSES)

    def check_and_emit_blocked(self) -> bool:
        """
        若有阻止行動的狀態，發送 StatusBlockedActionEvent 並回傳 True。
        在行動前呼叫，True 表示本回合跳過。
        """
        from common.event import StatusBlockedActionEvent
        for status in BLOCKING_STATUSES:
            if self.has_status(status):
                buff = next(
                    b for b in self._buffs.values()
                    if b.effect.get("attribute") == status
                )
                EventBus.emit(StatusBlockedActionEvent(
                    target=self.owner,
                    status=status,
                    rounds_remaining=buff.duration,
                ))
                return True
        return False

    # ══════════════════════════════════════════
    #  護盾
    # ══════════════════════════════════════════

    def absorb(self, damage: float) -> float:
        """護盾吸收傷害，回傳剩餘傷害。"""
        if self.shield <= 0:
            return damage
        absorbed   = min(self.shield, damage)
        self.shield -= absorbed
        return damage - absorbed

    # ══════════════════════════════════════════
    #  重置（每場戰鬥開始）
    # ══════════════════════════════════════════

    def reset(self) -> None:
        """
        清空所有狀態，不觸發 on_expire()。
        戰鬥結束後呼叫，不需要發送還原事件。
        """
        self._buffs.clear()
        self.shield = 0.0

    # ══════════════════════════════════════════
    #  顯示
    # ══════════════════════════════════════════

    def summary(self) -> str:
        if self._buffs:
            buff_lines = "\n".join(f"  {b}" for b in self._buffs.values())
        else:
            buff_lines = "  （無）"

        statuses = [
            b.effect["attribute"]
            for b in self._buffs.values()
            if b.effect.get("attribute") in _MECHANIC_ATTRIBUTES
        ]
        status_str = "、".join(statuses) if statuses else "（無）"

        return (
            f"Buff：\n{buff_lines}\n"
            f"狀態異常：{status_str}\n"
            f"護盾：{self.shield:.0f}"
        )
