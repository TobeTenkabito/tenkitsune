"""
Buff 類
─────────────────────────────────────────────
設計原則：
  - Buff 本身只描述「效果是什麼」，不直接修改任何實例屬性
  - 所有實際修改透過 EventBus 發送 Request Event，由監聽器執行
  - 機制類 Buff（眩暈、麻痹等）繼承 Buff，覆寫 on_apply / on_expire
  - BattleState 統一用 dict[str, Buff] 儲存，Player / Combatant 共用同一套接口

Buff 生命週期：
  on_apply()      ← BattleState.apply_buff() 時呼叫，發送初始效果
  on_tick()       ← 每回合結束 tick_buffs() 時呼叫，發送持續效果（DoT/HoT）
  on_expire()     ← 持續時間歸零或被移除時呼叫，發送還原效果
"""

from __future__ import annotations
from dataclasses import dataclass, field
from common.event import (
    EventBus,
    BuffAppliedEvent,
    BuffTickEvent,
    BuffExpiredEvent,
    DamageRequestEvent,
    HealRequestEvent,
    StatChangeRequestEvent,
    StatusAppliedEvent,
)


# ══════════════════════════════════════════════
#  effect dict 規格說明（供資料填寫參考）
# ══════════════════════════════════════════════
#
#  屬性加成類（apply 時生效，expire 時還原）：
#    {"attribute": "attack",  "value": 50}
#    {"attribute": "defense", "value": -20}
#
#  每回合 DoT / HoT（tick 時生效，不還原）：
#    {"attribute": "hp",  "value": -30,  "tick": True}
#    {"attribute": "mp",  "value":  10,  "tick": True}
#
#  機制類（無 value，由子類處理）：
#    {"attribute": "stunned"}
#    {"attribute": "paralyzed"}
#    {"attribute": "silenced"}
#    {"attribute": "blinded"}
#
# ══════════════════════════════════════════════


# ── 機制類狀態對應表 ──────────────────────────
_MECHANIC_ATTRIBUTES = {"stunned", "paralyzed", "silenced", "blinded"}


class Buff:
    """
    通用 Buff 基類。

    參數
    ────
    name         : Buff 名稱（唯一鍵）
    buff_type    : "buff" | "debuff"
    source       : 施加者名稱
    target       : 目標名稱（str，不持有實例引用）
    duration     : 持續回合數（-1 表示永久）
    effect       : 效果描述 dict，格式見上方規格說明
    """

    def __init__(
        self,
        name: str,
        buff_type: str,
        source: str,
        target: str,
        duration: int,
        effect: dict,
    ):
        self.name             = name
        self.buff_type        = buff_type
        self.source           = source
        self.target           = target
        self.duration         = duration
        self.original_duration = duration
        self.effect           = effect

        # 記錄 apply 時發出的 change，供 expire 還原用
        # key: attribute, value: 當時發出的 change 量
        self._applied_changes: dict[str, float] = {}

    # ══════════════════════════════════════════
    #  生命週期鉤子
    # ══════════════════════════════════════════

    def on_apply(self) -> None:
        """
        Buff 施加時呼叫。
        屬性加成類：emit StatChangeRequestEvent。
        機制類：emit StatusAppliedEvent。
        DoT/HoT：apply 時不觸發，等 on_tick。
        """
        attribute = self.effect.get("attribute")
        if attribute is None:
            return

        if attribute in _MECHANIC_ATTRIBUTES:
            # 機制類交給 StatusAppliedEvent 處理
            EventBus.emit(StatusAppliedEvent(
                target=self.target,
                status=attribute,
                rounds=self.duration,
            ))
            return

        # DoT/HoT 在 tick 處理，apply 時跳過
        if self.effect.get("tick", False):
            return

        value = self.effect.get("value")
        if value is None:
            return

        if attribute in ("hp", "mp"):
            # hp/mp 的非 tick 加成視為立即治療/傷害
            self._emit_hp_mp(attribute, value)
        else:
            # 屬性加成
            self._applied_changes[attribute] = value
            EventBus.emit(StatChangeRequestEvent(
                source=self.source,
                target=self.target,
                attr=attribute,
                change=value,
                scope="battle",
            ))

        EventBus.emit(BuffAppliedEvent(
            target=self.target,
            buff_name=self.name,
            duration=self.duration,
        ))

    def on_tick(self) -> None:
        """
        每回合結束時呼叫。
        只處理 tick=True 的 DoT / HoT 效果。
        """
        if not self.effect.get("tick", False):
            return

        attribute = self.effect.get("attribute")
        value     = self.effect.get("value")
        if attribute is None or value is None:
            return

        self._emit_hp_mp(attribute, value)

        EventBus.emit(BuffTickEvent(
            target=self.target,
            buff_name=self.name,
            duration_remaining=self.duration,
        ))

    def on_expire(self) -> None:
        """
        Buff 到期或被移除時呼叫。
        還原 apply 時發出的屬性加成（取反值）。
        機制類 / DoT 不需還原。
        """
        attribute = self.effect.get("attribute")

        # 機制類由 StatusExpiredEvent 處理，不在這裡還原
        if attribute in _MECHANIC_ATTRIBUTES:
            EventBus.emit(BuffExpiredEvent(
                target=self.target,
                buff_name=self.name,
            ))
            return

        # 還原屬性加成
        for attr, applied_value in self._applied_changes.items():
            EventBus.emit(StatChangeRequestEvent(
                source="buff_expire",
                target=self.target,
                attr=attr,
                change=-applied_value,
                scope="battle",
            ))

        self._applied_changes.clear()

        EventBus.emit(BuffExpiredEvent(
            target=self.target,
            buff_name=self.name,
        ))

    # ══════════════════════════════════════════
    #  工具
    # ══════════════════════════════════════════

    def _emit_hp_mp(self, attribute: str, value: float) -> None:
        """統一處理 hp/mp 的增減，正值治療，負值傷害。"""
        if value >= 0:
            EventBus.emit(HealRequestEvent(
                source=self.source,
                target=self.target,
                amount=value,
                attr=attribute,
            ))
        else:
            EventBus.emit(DamageRequestEvent(
                source=self.source,
                target=self.target,
                amount=-value,
                damage_type="true",
            ))

    def decrement_duration(self) -> bool:
        """
        回合結束時倒數持續時間。
        回傳 True 表示已到期，BattleState 應呼叫 on_expire()。
        永久 Buff（duration == -1）永不到期。
        """
        if self.duration == -1:
            return False
        self.duration -= 1
        return self.duration <= 0

    def refresh(self) -> None:
        """刷新持續時間（同名 Buff 重複施加時）。"""
        self.duration = self.original_duration

    def is_expired(self) -> bool:
        return self.duration == 0

    # ══════════════════════════════════════════
    #  顯示
    # ══════════════════════════════════════════

    def __str__(self) -> str:
        dur = "永久" if self.duration == -1 else f"{self.duration}/{self.original_duration} 回合"
        return f"[{self.buff_type}] {self.name}（{dur}）效果：{self.effect}"

    def __repr__(self) -> str:
        return f"<Buff {self.name} target={self.target} duration={self.duration}>"


# ══════════════════════════════════════════════
#  機制類子類（可選，資料驅動時不需要實例化子類）
# ══════════════════════════════════════════════

class StunBuff(Buff):
    """眩暈：目標無法行動。"""
    def __init__(self, source: str, target: str, duration: int):
        super().__init__(
            name="stunned",
            buff_type="debuff",
            source=source,
            target=target,
            duration=duration,
            effect={"attribute": "stunned"},
        )


class ParalysisBuff(Buff):
    """麻痹：目標有機率無法行動。"""
    def __init__(self, source: str, target: str, duration: int):
        super().__init__(
            name="paralyzed",
            buff_type="debuff",
            source=source,
            target=target,
            duration=duration,
            effect={"attribute": "paralyzed"},
        )


class SilenceBuff(Buff):
    """沉默：目標無法使用技能。"""
    def __init__(self, source: str, target: str, duration: int):
        super().__init__(
            name="silenced",
            buff_type="debuff",
            source=source,
            target=target,
            duration=duration,
            effect={"attribute": "silenced"},
        )


class BlindBuff(Buff):
    """致盲：目標攻擊必定落空。"""
    def __init__(self, source: str, target: str, duration: int):
        super().__init__(
            name="blinded",
            buff_type="debuff",
            source=source,
            target=target,
            duration=duration,
            effect={"attribute": "blinded"},
        )
