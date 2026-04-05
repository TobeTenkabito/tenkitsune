"""
玩家相關事件
─────────────────────────────────────────────
成長、背包、技能、裝備
"""

from __future__ import annotations
from dataclasses import dataclass
from common.event.bus import BattleEvent


# ── 成長 ──────────────────────────────────────

@dataclass
class LevelUpEvent(BattleEvent):
    player: str
    new_level: int

@dataclass
class StatChangedEvent(BattleEvent):
    player: str
    attribute: str
    delta: float
    source: str           # "task" / "dungeon" / "cultivation" / "skill"

# ── 背包 ──────────────────────────────────────

@dataclass
class ItemAddedEvent(BattleEvent):
    item_name: str
    quantity: int
    is_new: bool

@dataclass
class ItemRemovedEvent(BattleEvent):
    item_name: str
    quantity: int

# ── 技能 / 裝備 ───────────────────────────────

@dataclass
class SkillEquippedEvent(BattleEvent):
    player: str
    skill_name: str

@dataclass
class SkillRemovedEvent(BattleEvent):
    player: str
    skill_name: str

@dataclass
class EquipmentEquippedEvent(BattleEvent):
    player: str
    equipment_name: str
    category: str
