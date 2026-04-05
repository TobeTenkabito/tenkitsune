"""
common.event 統一入口
─────────────────────────────────────────────
所有模組只需：
  from common.event import EventBus, AttackEvent, TaskAcceptedEvent, ...

向後相容：
  BattleEventBus = EventBus
"""

from common.event.bus import EventBus, BattleEvent, _to_snake

# 向後相容舊名稱
BattleEventBus = EventBus

# ── Battle ────────────────────────────────────
from common.event.battle import (
    TurnStartEvent,
    TurnOrderUpdatedEvent,
    AttackEvent,
    SkillUsedEvent,
    MissEvent,
    DamageRequestEvent,
    HealRequestEvent,
    StatChangeRequestEvent,
    BuffRequestEvent,
    BuffRemoveRequestEvent,
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

# ── System (base) ─────────────────────────────
from common.event.system import (
    WarningEvent,
    InfoEvent,
    HealEvent,
    WarpRequestEvent,
)

# ── System (cultivation) ──────────────────────
from common.event.system.cultivation import (
    CultivationUpgradeEvent,
    CultivationResetEvent,
    XinfaUnlockEvent,
    XinfaResetEvent,
)

# ── System (task) ─────────────────────────────
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

# ── System (npc) ──────────────────────────────
from common.event.system.npc import (
    NpcInteractEvent,
    NpcDialogueEvent,
    NpcGiftEvent,
    NpcAffectionChangedEvent,
    NpcRemovedEvent,
    NpcExchangeEvent,
    NpcInteractionEvent,
)

# ── System (dungeon) ──────────────────────────
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

# ── Player ────────────────────────────────────
from common.event.player import (
    LevelUpEvent,
    StatChangedEvent,
    ItemAddedEvent,
    ItemRemovedEvent,
    SkillEquippedEvent,
    SkillRemovedEvent,
    EquipmentEquippedEvent,
)

# ── Handlers ──────────────────────────────────
from common.event.handlers import (
    BattleHandler,
    ConsoleBattleHandler,
    SilentBattleHandler,
    JsonCollectorHandler,
)
from common.event.system.map import (
    MapWarpRequestEvent,
)

__all__ = [
    # Bus
    "EventBus", "BattleEventBus", "BattleEvent",
    # Battle
    "TurnStartEvent", "TurnOrderUpdatedEvent",
    "AttackEvent", "SkillUsedEvent", "MissEvent",
    "DamageRequestEvent", "HealRequestEvent", "StatChangeRequestEvent",
    "BuffRequestEvent", "BuffRemoveRequestEvent",
    "StatusAppliedEvent", "StatusBlockedActionEvent", "StatusExpiredEvent",
    "BuffAppliedEvent", "BuffTickEvent", "BuffExpiredEvent",
    "DeathEvent", "ExpGainedEvent", "DropEvent",
    "BattleResultEvent", "SummonEvent",
    # System base
    "WarningEvent", "InfoEvent", "HealEvent", "WarpRequestEvent",
    # Cultivation
    "CultivationUpgradeEvent", "CultivationResetEvent",
    "XinfaUnlockEvent", "XinfaResetEvent",
    # Task
    "TaskAcceptedEvent", "TaskAcceptFailedEvent",
    "TaskReadyEvent", "TaskReturnNpcEvent",
    "TaskCompletedEvent", "TaskRewardEvent",
    "TaskProgressEvent", "KillRegisteredEvent",
    # NPC
    "NpcInteractEvent", "NpcDialogueEvent",
    "NpcGiftEvent", "NpcAffectionChangedEvent",
    "NpcRemovedEvent", "NpcExchangeEvent",
    "NpcInteractionEvent",
    # Dungeon
    "DungeonEnteredEvent", "DungeonFloorEnteredEvent",
    "DungeonFloorClearedEvent", "DungeonRewardEvent",
    "DungeonClearedEvent", "DungeonLostEvent",
    "DungeonNpcRemovedEvent", "DungeonProgressEvent",
    # Player
    "LevelUpEvent", "StatChangedEvent",
    "ItemAddedEvent", "ItemRemovedEvent",
    "SkillEquippedEvent", "SkillRemovedEvent", "EquipmentEquippedEvent",
    # Handlers
    "BattleHandler", "ConsoleBattleHandler",
    "SilentBattleHandler", "JsonCollectorHandler",
    "MapWarpRequestEvent",
]