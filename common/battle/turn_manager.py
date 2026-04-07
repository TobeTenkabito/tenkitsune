"""
TurnManager
负责：
  1. 根据 speed 建立 / 更新回合顺序
  2. 查询参与者本回合的行动限制（从 battle_state 推导）
  3. 状态异常的计时由 BattleState.tick_buffs() 统一处理，
     TurnManager 不再直接操作任何状态字段
"""
import random

from common.event import (
    EventBus,
    TurnOrderUpdatedEvent,
)


class TurnManager:

    def __init__(self):
        self.order: list = []

    # ── 回合顺序 ──────────────────────────────────────────────

    def build_order(self, player, allies: list, enemies: list) -> list:
        """初始建立回合顺序（包含 player）。"""
        participants = (
            ([player] if player is not None else [])
            + allies
            + enemies
        )
        for p in participants:
            if not hasattr(p, "speed"):
                raise ValueError(f"{p.name} 缺少 speed 属性，无法计算回合顺序。")
        self.order = sorted(participants, key=lambda x: x.speed, reverse=True)
        EventBus.emit(TurnOrderUpdatedEvent(
            order=[p.name for p in self.order]
        ))
        return self.order

    def update_order(self, player, allies: list, enemies: list) -> list:
        """移除死亡角色后重新排序（每回合结束调用）。"""
        participants = (
            ([player] if player is not None and player.hp > 0 else [])
            + [a for a in allies  if a.hp > 0]
            + [e for e in enemies if e.hp > 0]
        )
        self.order = sorted(participants, key=lambda x: x.speed, reverse=True)
        EventBus.emit(TurnOrderUpdatedEvent(
            order=[p.name for p in self.order]
        ))
        return self.order

    # ── 状态异常查询 ──────────────────────────────────────────
    #
    #  所有状态字段（dizzy_rounds 等）已从 Combatant 移除。
    #  状态异常以 Buff 形式存储在 participant.battle_state。
    #  计时递减由 BattleState.tick_buffs() 统一处理。
    #  TurnManager 只负责「查询 + 发事件」，不修改任何字段。

    def tick_status(self, participant) -> str:
        """
        查询本回合的主要行动限制。
        - "stunned"   : 眩晕，完全无法行动
        - "paralyzed" : 麻痹，50% 概率无法行动
        - "normal"    : 正常行动

        注意：不消耗计时，计时由 BattleState.tick_buffs() 负责。
        """
        bs = participant.battle_state

        # 眩晕：直接阻断
        if bs.has_status("stunned"):
            bs.check_and_emit_blocked()
            return "stunned"

        # 麻痹：50% 概率阻断
        if bs.has_status("paralyzed"):
            if random.random() < 0.5:
                bs.check_and_emit_blocked()
                return "paralyzed"

        return "normal"

    def get_action_restrictions(self, participant) -> set:
        """
        返回本回合的行动限制集合（仅查询，不消耗计时）。
        供 action.py 判断技能 / 普攻是否可用。
        """
        bs = participant.battle_state
        restrictions = set()

        if bs.has_status("silenced"):
            restrictions.add("silenced")
        if bs.has_status("blinded"):
            restrictions.add("blinded")

        return restrictions

    # tick_minor_status 已删除：
    # 沉默 / 致盲的计时统一由 BattleState.tick_buffs() 处理，
    # BattleEngine 每回合调用一次即可，无需在行动后单独递减。
