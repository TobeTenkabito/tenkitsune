"""
戰鬥狀態組件
─────────────────────────────────────────────
管理戰鬥中的臨時狀態：Buff、狀態異常、護盾等
不持久化，每場戰鬥開始時重置
"""

from __future__ import annotations
from dataclasses import dataclass, field
from common.event import (
    EventBus,
    BuffAppliedEvent, BuffTickEvent, BuffExpiredEvent,
    StatusAppliedEvent, StatusBlockedActionEvent, StatusExpiredEvent,
    WarningEvent,
)


# ══════════════════════════════════════════════
#  Buff 條目
# ══════════════════════════════════════════════

@dataclass
class BuffEntry:
    name: str
    duration: int
    effect: dict = field(default_factory=dict)   # {"attack": 10, "defense": -5, ...}


# ══════════════════════════════════════════════
#  戰鬥狀態
# ══════════════════════════════════════════════

BLOCKING_STATUSES = {"stunned", "paralyzed", "silenced", "blinded"}

class BattleState:
    def __init__(self, owner: str = "unknown"):
        self.owner   = owner
        self._buffs:    dict[str, BuffEntry] = {}
        self._statuses: dict[str, int]       = {}   # status → rounds_remaining
        self.shield: float = 0.0

    # ══════════════════════════════════════════
    #  Buff
    # ══════════════════════════════════════════

    def apply_buff(self, name: str, duration: int, effect: dict | None = None) -> None:
        self._buffs[name] = BuffEntry(name=name, duration=duration, effect=effect or {})
        EventBus.emit(BuffAppliedEvent(target=self.owner, buff_name=name, duration=duration))

    def tick_buffs(self) -> None:
        """每回合結束時呼叫，倒數所有 Buff。"""
        expired = []
        for name, entry in self._buffs.items():
            entry.duration -= 1
            if entry.duration <= 0:
                expired.append(name)
            else:
                EventBus.emit(BuffTickEvent(
                    target=self.owner,
                    buff_name=name,
                    duration_remaining=entry.duration,
                ))
        for name in expired:
            del self._buffs[name]
            EventBus.emit(BuffExpiredEvent(target=self.owner, buff_name=name))

    def has_buff(self, name: str) -> bool:
        return name in self._buffs

    def get_buff_effect(self, name: str) -> dict:
        entry = self._buffs.get(name)
        return entry.effect if entry else {}

    def total_buff_modifier(self, attribute: str) -> float:
        """加總所有 Buff 對某屬性的修正值。"""
        return sum(
            entry.effect.get(attribute, 0.0)
            for entry in self._buffs.values()
        )

    # ══════════════════════════════════════════
    #  狀態異常
    # ══════════════════════════════════════════

    def apply_status(self, status: str, rounds: int) -> None:
        self._statuses[status] = rounds
        EventBus.emit(StatusAppliedEvent(target=self.owner, status=status, rounds=rounds))

    def tick_statuses(self) -> None:
        """每回合結束時呼叫，倒數所有狀態異常。"""
        expired = []
        for status in list(self._statuses):
            self._statuses[status] -= 1
            if self._statuses[status] <= 0:
                expired.append(status)
        for status in expired:
            del self._statuses[status]
            EventBus.emit(StatusExpiredEvent(target=self.owner, status=status))

    def is_blocked(self, status: str | None = None) -> bool:
        """
        檢查是否被阻止行動。
        status=None → 檢查任意阻止性狀態
        status=xxx  → 檢查特定狀態
        """
        if status:
            return status in self._statuses
        return bool(self._statuses.keys() & BLOCKING_STATUSES)

    def check_and_emit_blocked(self) -> bool:
        """
        若當前有阻止行動的狀態，發送事件並回傳 True。
        在行動前呼叫，True 表示本回合跳過。
        """
        for status in BLOCKING_STATUSES:
            if status in self._statuses:
                EventBus.emit(StatusBlockedActionEvent(
                    target=self.owner,
                    status=status,
                    rounds_remaining=self._statuses[status],
                ))
                return True
        return False

    def has_status(self, status: str) -> bool:
        return status in self._statuses

    # ══════════════════════════════════════════
    #  護盾
    # ══════════════════════════════════════════

    def absorb(self, damage: float) -> float:
        """護盾吸收傷害，回傳剩餘傷害。"""
        if self.shield <= 0:
            return damage
        absorbed = min(self.shield, damage)
        self.shield -= absorbed
        return damage - absorbed

    # ══════════════════════════════════════════
    #  重置（每場戰鬥開始）
    # ══════════════════════════════════════════

    def reset(self) -> None:
        self._buffs.clear()
        self._statuses.clear()
        self.shield = 0.0

    # ══════════════════════════════════════════
    #  顯示
    # ══════════════════════════════════════════

    def summary(self) -> str:
        buffs    = "、".join(self._buffs.keys())    or "（無）"
        statuses = "、".join(self._statuses.keys()) or "（無）"
        return (
            f"Buff：{buffs}\n"
            f"狀態異常：{statuses}\n"
            f"護盾：{self.shield:.0f}"
        )
