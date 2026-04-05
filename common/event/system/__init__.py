"""
common.event.system
───────────────────────────────────────────────────────────────
系統層級事件：警告、治療、傳送。
修為 / 心法相關請見 common.event.system.cultivation
"""
from __future__ import annotations
from dataclasses import dataclass
from common.event.bus import BattleEvent
from common.event.system.cultivation import (
    CultivationUpgradeEvent,
    CultivationResetEvent,
    XinfaUnlockEvent,
    XinfaResetEvent,
)
from common.event.system.task import (
    TaskAcceptedEvent,
    TaskAcceptFailedEvent,
    TaskReadyEvent,
    TaskReturnNpcEvent,
    TaskCompletedEvent,
    TaskRewardEvent,
    TaskProgressEvent,
    KillRegisteredEvent,
)
from common.event.system.npc import (
    NpcInteractEvent,
    NpcDialogueEvent,
    NpcGiftEvent,
    NpcAffectionChangedEvent,
    NpcRemovedEvent,
    NpcExchangeEvent,
    NpcInteractionEvent,
)
from common.event.system.dungeon import (
    DungeonEnteredEvent,
    DungeonFloorEnteredEvent,
    DungeonFloorClearedEvent,
    DungeonRewardEvent,
    DungeonClearedEvent,
    DungeonLostEvent,
    DungeonNpcRemovedEvent,
    DungeonProgressEvent,
)

__all__ = [
    # cultivation
    "CultivationUpgradeEvent", "CultivationResetEvent",
    "XinfaUnlockEvent", "XinfaResetEvent",
    # task
    "TaskAcceptedEvent", "TaskAcceptFailedEvent",
    "TaskReadyEvent", "TaskReturnNpcEvent",
    "TaskCompletedEvent", "TaskRewardEvent",
    "TaskProgressEvent", "KillRegisteredEvent",
    # npc
    "NpcInteractEvent", "NpcDialogueEvent",
    "NpcGiftEvent", "NpcAffectionChangedEvent",
    "NpcRemovedEvent", "NpcExchangeEvent",
    "NpcInteractionEvent",
    # dungeon
    "DungeonEnteredEvent", "DungeonFloorEnteredEvent",
    "DungeonFloorClearedEvent", "DungeonRewardEvent",
    "DungeonClearedEvent", "DungeonLostEvent",
    "DungeonNpcRemovedEvent", "DungeonProgressEvent",
]


@dataclass
class WarningEvent(BattleEvent):
    """警告 / 操作失敗訊息，取代 print。"""
    message: str = ""

@dataclass
class InfoEvent(BattleEvent):
    """
    一般提示訊息，取代 print。
    用途：選擇心法線、初始化完成、一般操作回饋等。
    """
    message: str = ""

@dataclass
class HealEvent(BattleEvent):
    """治療結算通知。"""
    source:    str   = ""
    target:    str   = ""
    amount:    float = 0.0
    heal_type: str   = "hp"   # "hp" | "mp"

@dataclass
class WarpRequestEvent(BattleEvent):
    """請求場景跳轉。"""
    source:      str = ""
    destination: str = ""