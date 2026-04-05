"""
任務 / NPC / 秘境事件
"""

from __future__ import annotations
from dataclasses import dataclass, field
from common.event.bus import BattleEvent


# ── 任務 ──────────────────────────────────────

@dataclass
class TaskProgressEvent(BattleEvent):
    task_name: str
    description: str

@dataclass
class TaskCompletedEvent(BattleEvent):
    task_name: str

# ── NPC ───────────────────────────────────────

@dataclass
class NpcInteractionEvent(BattleEvent):
    npc_id: str | int
    action: str           # "talk" / "give_item" / "remove"
    detail: str = ""

# ── 秘境 ──────────────────────────────────────

@dataclass
class DungeonProgressEvent(BattleEvent):
    dungeon_id: str | int
    floor: int            # -1 表示通關
    