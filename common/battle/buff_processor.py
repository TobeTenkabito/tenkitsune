"""
BuffProcessor
負責每回合開始時統一處理所有參與者的 Buff 生命週期：
  1. 觸發 buff 的持續效果
  2. 計時遞減
  3. 到期移除並恢復屬性
"""

from common.battle.event import (
    BattleEventBus,
    BuffTickEvent,
    BuffExpiredEvent,
    WarningEvent,
)


class BuffProcessor:

    @staticmethod
    def apply_buffs(participants: list) -> None:
        """
        對所有參與者執行一輪 buff 處理。
        participants: 戰場上所有角色（player + allies + enemies）
        """
        for participant in participants:
            if not hasattr(participant, "buffs"):
                continue
            BuffProcessor._process_participant(participant)

    @staticmethod
    def _process_participant(participant) -> None:
        for buff in participant.buffs[:]:
            if buff.target is None:
                BattleEventBus.emit(WarningEvent(
                    message=f"Buff '{buff.name}' 沒有目標，跳過。"
                ))
                continue

            # 1. 觸發持續效果
            buff.apply_effect()

            # 2. 計時遞減
            expired = buff.decrement_duration()

            # 3. 到期處理
            if expired or buff.is_expired():
                buff.remove_effect()
                participant.buffs.remove(buff)
                BattleEventBus.emit(BuffExpiredEvent(
                    target=participant.name,
                    buff_name=buff.name,
                ))
            else:
                BattleEventBus.emit(BuffTickEvent(
                    target=participant.name,
                    buff_name=buff.name,
                    duration_remaining=buff.duration,
                ))

    @staticmethod
    def clear_all(participants: list) -> None:
        """戰鬥結束後強制清除所有 buff。"""
        for participant in participants:
            if hasattr(participant, "remove_all_buffs"):
                participant.remove_all_buffs()
                BattleEventBus.emit(BuffExpiredEvent(
                    target=participant.name,
                    buff_name="（全部）",
                ))
