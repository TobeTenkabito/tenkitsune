"""
CombatHandler
─────────────────────────────────────────────
处理所有战斗内的 Request 事件：
  - DamageRequestEvent  → 扣血（护盾优先吸收）
  - HealRequestEvent    → 回血/回蓝
  - StatChangeRequestEvent → 修改属性

生命周期：随 BattleEngine 创建/销毁
"""
from __future__ import annotations

from common.event.bus import BattleEvent
from common.event.handlers import BattleHandler
from common.event.battle import (
    DamageRequestEvent,
    HealRequestEvent,
    StatChangeRequestEvent,
)
from common.event import EventBus, WarningEvent


class CombatHandler(BattleHandler):

    def __init__(self, engine) -> None:
        self._engine = engine

    def _resolve(self, name: str):
        """通过名字在战场内找到 Combatant 实例。"""
        for p in self._engine._all_participants():
            if p.name == name:
                return p
        return None

    # ── Damage ────────────────────────────────

    def on_damage_request_event(self, e: DamageRequestEvent) -> None:
        target = self._resolve(e.target)
        if target is None:
            EventBus.emit(WarningEvent(
                message=f"DamageRequest: 找不到目标 '{e.target}'"
            ))
            return

        # 护盾优先吸收
        remaining = target.battle_state.absorb(e.amount)

        # 实际扣血
        target.hp = max(0.0, target.hp - remaining)

    # ── Heal ──────────────────────────────────

    def on_heal_request_event(self, e: HealRequestEvent) -> None:
        target = self._resolve(e.target)
        if target is None:
            EventBus.emit(WarningEvent(
                message=f"HealRequest: 找不到目标 '{e.target}'"
            ))
            return

        if e.attr == "hp":
            target.hp = min(target.max_hp, target.hp + e.amount)
        elif e.attr == "mp":
            target.mp = min(target.max_mp, target.mp + e.amount)
        else:
            EventBus.emit(WarningEvent(
                message=f"HealRequest: 未知属性 '{e.attr}'"
            ))

    # ── StatChange ────────────────────────────

    def on_stat_change_request_event(self, e: StatChangeRequestEvent) -> None:
        target = self._resolve(e.target)
        if target is None:
            EventBus.emit(WarningEvent(
                message=f"StatChangeRequest: 找不到目标 '{e.target}'"
            ))
            return

        if not hasattr(target, e.attr):
            EventBus.emit(WarningEvent(
                message=f"StatChangeRequest: '{e.target}' 没有属性 '{e.attr}'"
            ))
            return

        current = getattr(target, e.attr)
        setattr(target, e.attr, current + e.change)
