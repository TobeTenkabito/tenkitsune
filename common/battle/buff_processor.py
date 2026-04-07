"""
BuffProcessor
負責每回合開始時統一處理所有參與者的 Buff 生命週期：
  1. 觸發 buff 的持續效果
  2. 計時遞減
  3. 到期移除並恢復屬性
"""

from common.event import (
    EventBus,
    BuffTickEvent,
    BuffExpiredEvent,
    WarningEvent,
)


class BuffProcessor:

    @staticmethod
    def apply_buffs(participants: list) -> None:
        """
        對所有參與者執行一輪 buff 處理。
        直接委托給 BattleState.tick_buffs()，避免重複邏輯。
        """
        for participant in participants:
            if hasattr(participant, "battle_state"):
                participant.battle_state.tick_buffs()

    @staticmethod
    def clear_all(participants: list) -> None:
        """戰鬥結束後強制清除所有 buff。"""
        for participant in participants:
            if hasattr(participant, "battle_state"):
                participant.battle_state.remove_all_buffs()
                EventBus.emit(BuffExpiredEvent(
                    target=participant.name,
                    buff_name="（全部）",
                ))
