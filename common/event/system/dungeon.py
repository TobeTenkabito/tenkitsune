"""
common.event.system.dungeon
─────────────────────────────────────────────
秘境生命週期事件。
"""

from __future__ import annotations
from dataclasses import dataclass
from common.event.bus import BattleEvent


@dataclass
class DungeonEnteredEvent(BattleEvent):
    """玩家進入秘境。"""
    player:      str       = ""
    dungeon_id:  int | str = 0
    dungeon_name: str      = ""


@dataclass
class DungeonFloorEnteredEvent(BattleEvent):
    """玩家進入某一層。"""
    player:       str       = ""
    dungeon_id:   int | str = 0
    floor_number: int       = 0
    description:  str       = ""


@dataclass
class DungeonFloorClearedEvent(BattleEvent):
    """某一層戰鬥勝利。"""
    player:       str       = ""
    dungeon_id:   int | str = 0
    floor_number: int       = 0


@dataclass
class DungeonRewardEvent(BattleEvent):
    """秘境獎勵發放（每筆）。"""
    player:       str       = ""
    dungeon_id:   int | str = 0
    floor_number: int       = 0
    reward_type:  str       = ""    # "item" | "exp" | "attribute"
    detail:       str       = ""
    is_first_time: bool     = False
    reward_kind:  str       = ""    # "first_time" | "fixed" | "random"


@dataclass
class DungeonClearedEvent(BattleEvent):
    """秘境通關。"""
    player:       str       = ""
    dungeon_id:   int | str = 0
    dungeon_name: str       = ""


@dataclass
class DungeonLostEvent(BattleEvent):
    """玩家在秘境中失敗。"""
    player:     str       = ""
    dungeon_id: int | str = 0
    exp_loss:   int       = 0


@dataclass
class DungeonNpcRemovedEvent(BattleEvent):
    """秘境某層 NPC 被移除。"""
    dungeon_id:   int | str = 0
    floor_number: int       = 0
    npc_id:       int | str = 0


@dataclass
class DungeonProgressEvent(BattleEvent):
    """秘境進度更新（向後相容，擴充欄位）。"""
    dungeon_id:   int | str = 0
    floor:        int       = 0    # -1 表示通關
    player:       str       = ""
    dungeon_name: str       = ""