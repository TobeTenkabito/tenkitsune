"""
common.event.system.npc
─────────────────────────────────────────────
NPC 互動事件。
"""

from __future__ import annotations
from dataclasses import dataclass
from common.event.bus import BattleEvent


@dataclass
class NpcInteractEvent(BattleEvent):
    """進入 NPC 互動介面。"""
    npc_id:   int | str = 0
    npc_name: str       = ""


@dataclass
class NpcDialogueEvent(BattleEvent):
    """NPC 說出一句對話。"""
    npc_id:   int | str = 0
    npc_name: str       = ""
    dialogue: str       = ""


@dataclass
class NpcGiftEvent(BattleEvent):
    """玩家贈送物品給 NPC。"""
    npc_id:          int | str = 0
    npc_name:        str       = ""
    item_name:       str       = ""
    quantity:        int       = 1
    affection_delta: int       = 0
    affection_total: int       = 0


@dataclass
class NpcAffectionChangedEvent(BattleEvent):
    """NPC 好感度變動（贈禮 / 秘境進入 / 其他）。"""
    npc_id:   int | str = 0
    npc_name: str       = ""
    delta:    int       = 0
    total:    int       = 0
    reason:   str       = ""   # "gift" | "dungeon_enter" | "other"


@dataclass
class NpcRemovedEvent(BattleEvent):
    """NPC 被玩家殺死，本周目移除。"""
    npc_id:   int | str = 0
    npc_name: str       = ""


@dataclass
class NpcExchangeEvent(BattleEvent):
    """NPC 交易成功。"""
    npc_id:        int | str = 0
    npc_name:      str       = ""
    offered_item:  str       = ""
    required_item: str       = ""
    quantity:      int       = 0


@dataclass
class NpcInteractionEvent(BattleEvent):
    """通用 NPC 互動（向後相容）。"""
    npc_id: int | str = 0
    action: str       = ""   # "talk" | "give_item" | "remove"
    detail: str       = ""