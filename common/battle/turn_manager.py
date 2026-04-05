"""
TurnManager
負責：
  1. 根據 speed 建立 / 更新回合順序
  2. 每輪對參與者的狀態異常（眩暈 / 麻痹 / 沉默 / 致盲）進行計時遞減
  3. 提供「本回合能否行動」的查詢接口
"""
import random

from common.battle.event import (
    BattleEventBus,
    TurnOrderUpdatedEvent,
    StatusBlockedActionEvent,
    StatusExpiredEvent,
)


class TurnManager:

    def __init__(self):
        self.order: list = []

    # ── 回合順序 ──────────────────────────────────────────────

    def build_order(self, player, allies: list, enemies: list) -> list:
        """初始建立回合順序（包含 player）。"""
        participants = (
            ([player] if player is not None else [])
            + allies
            + enemies
        )
        for p in participants:
            if not hasattr(p, "speed"):
                raise ValueError(f"{p.name} 缺少 speed 屬性，無法計算回合順序。")
        self.order = sorted(participants, key=lambda x: x.speed, reverse=True)
        BattleEventBus.emit(TurnOrderUpdatedEvent(
            order=[p.name for p in self.order]
        ))
        return self.order

    def update_order(self, player, allies: list, enemies: list) -> list:
        """移除死亡角色後重新排序（每回合結束呼叫）。"""
        participants = (
            ([player] if player is not None and player.hp > 0 else [])
            + [a for a in allies  if a.hp > 0]
            + [e for e in enemies if e.hp > 0]
        )
        self.order = sorted(participants, key=lambda x: x.speed, reverse=True)
        BattleEventBus.emit(TurnOrderUpdatedEvent(
            order=[p.name for p in self.order]
        ))
        return self.order

    # ── 狀態異常 ──────────────────────────────────────────────

    def tick_status(self, participant) -> str:
        """
        對單個參與者執行狀態異常計時遞減。
        返回本回合的行動限制：
          "stunned"   - 眩暈，完全無法行動
          "paralyzed" - 麻痹，50% 機率無法行動
          "normal"    - 正常行動
        """
        # 眩暈
        if getattr(participant, "dizzy_rounds", 0) > 0:
            participant.dizzy_rounds -= 1
            BattleEventBus.emit(StatusBlockedActionEvent(
                target=participant.name,
                status="stunned",
                rounds_remaining=participant.dizzy_rounds,
            ))
            if participant.dizzy_rounds == 0:
                BattleEventBus.emit(StatusExpiredEvent(
                    target=participant.name,
                    status="stunned",
                ))
            return "stunned"

        # 麻痹（50% 觸發）
        if getattr(participant, "paralysis_rounds", 0) > 0:
            participant.paralysis_rounds -= 1
            if random.random() < 0.5:
                BattleEventBus.emit(StatusBlockedActionEvent(
                    target=participant.name,
                    status="paralyzed",
                    rounds_remaining=participant.paralysis_rounds,
                ))
                if participant.paralysis_rounds == 0:
                    BattleEventBus.emit(StatusExpiredEvent(
                        target=participant.name,
                        status="paralyzed",
                    ))
                return "paralyzed"

        return "normal"

    def get_action_restrictions(self, participant) -> set:
        """
        返回本回合的行動限制集合（不消耗計時，僅查詢）。
        供 action.py 判斷技能 / 普攻是否可用。
        """
        restrictions = set()
        if getattr(participant, "silence_rounds", 0) > 0:
            restrictions.add("silenced")
        if getattr(participant, "blind_rounds", 0) > 0:
            restrictions.add("blinded")
        return restrictions

    def tick_minor_status(self, participant) -> None:
        """對沉默 / 致盲進行計時遞減（每回合行動後呼叫）。"""
        if getattr(participant, "silence_rounds", 0) > 0:
            participant.silence_rounds -= 1
            if participant.silence_rounds == 0:
                BattleEventBus.emit(StatusExpiredEvent(
                    target=participant.name,
                    status="silenced",
                ))

        if getattr(participant, "blind_rounds", 0) > 0:
            participant.blind_rounds -= 1
            if participant.blind_rounds == 0:
                BattleEventBus.emit(StatusExpiredEvent(
                    target=participant.name,
                    status="blinded",
                ))
