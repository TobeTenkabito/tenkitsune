"""
common.event 統一入口
─────────────────────────────────────────────
所有模組只需：
  from common.event import EventBus, AttackEvent, ItemAddedEvent, ...

向後相容：
  BattleEventBus = EventBus（舊 import 不會立刻爆掉）
"""

from common.event.bus import EventBus, BattleEvent, _to_snake

# 向後相容舊名稱
BattleEventBus = EventBus

from common.event.battle import (
    TurnStartEvent,
    TurnOrderUpdatedEvent,
    AttackEvent,
    SkillUsedEvent,
    MissEvent,
    StatusAppliedEvent,
    StatusBlockedActionEvent,
    StatusExpiredEvent,
    BuffAppliedEvent,
    BuffTickEvent,
    BuffExpiredEvent,
    DeathEvent,
    ExpGainedEvent,
    DropEvent,
    BattleResultEvent,
    SummonEvent,
)
from common.event.system import (
    WarningEvent,
    HealEvent,
)
from common.event.player import (
    LevelUpEvent,
    StatChangedEvent,
    ItemAddedEvent,
    ItemRemovedEvent,
    SkillEquippedEvent,
    SkillRemovedEvent,
    EquipmentEquippedEvent,
)
from common.event.quest import (
    TaskProgressEvent,
    TaskCompletedEvent,
    NpcInteractionEvent,
    DungeonProgressEvent,
)
from common.event.handlers import (
    BattleHandler,
    ConsoleBattleHandler,
    SilentBattleHandler,
    JsonCollectorHandler,
)

__all__ = [
    # Bus
    "EventBus", "BattleEventBus", "BattleEvent",
    # Battle
    "TurnStartEvent", "TurnOrderUpdatedEvent",
    "AttackEvent", "SkillUsedEvent", "MissEvent",
    "StatusAppliedEvent", "StatusBlockedActionEvent", "StatusExpiredEvent",
    "BuffAppliedEvent", "BuffTickEvent", "BuffExpiredEvent",
    "DeathEvent", "ExpGainedEvent", "DropEvent",
    "BattleResultEvent", "SummonEvent",
    # System
    "WarningEvent", "HealEvent",
    # Player
    "LevelUpEvent", "StatChangedEvent",
    "ItemAddedEvent", "ItemRemovedEvent",
    "SkillEquippedEvent", "SkillRemovedEvent", "EquipmentEquippedEvent",
    # Quest
    "TaskProgressEvent", "TaskCompletedEvent",
    "NpcInteractionEvent", "DungeonProgressEvent",
    # Handlers
    "BattleHandler", "ConsoleBattleHandler",
    "SilentBattleHandler", "JsonCollectorHandler",
]