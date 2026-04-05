"""
common.event.system.task
─────────────────────────────────────────────
Task 生命週期事件。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from common.event.bus import BattleEvent


@dataclass
class TaskAcceptedEvent(BattleEvent):
    """任務接受成功。"""
    player:      str = ""
    task_number: int = 0
    task_name:   str = ""


@dataclass
class TaskAcceptFailedEvent(BattleEvent):
    """任務無法接受。"""
    player:      str = ""
    task_number: int = 0
    task_name:   str = ""
    reason:      str = ""   # "not_repeatable" | "prerequisite" | "condition"


@dataclass
class TaskReadyEvent(BattleEvent):
    """完成條件達成，可交付。"""
    player:      str = ""
    task_number: int = 0
    task_name:   str = ""


@dataclass
class TaskReturnNpcEvent(BattleEvent):
    """需回 NPC 處領獎。"""
    player:      str      = ""
    task_number: int      = 0
    task_name:   str      = ""
    npc_id:      int | str = 0
    npc_name:    str      = ""


@dataclass
class TaskCompletedEvent(BattleEvent):
    """任務完成結算。"""
    player:      str = ""
    task_number: int = 0
    task_name:   str = ""


@dataclass
class TaskRewardEvent(BattleEvent):
    """獎勵發放（每筆）。"""
    player:      str = ""
    task_number: int = 0
    reward_type: str = ""   # "item" | "exp" | "attribute"
    detail:      str = ""   # 人類可讀描述


@dataclass
class TaskProgressEvent(BattleEvent):
    """進度描述更新。"""
    task_name:   str = ""
    description: str = ""


@dataclass
class KillRegisteredEvent(BattleEvent):
    """擊殺計數更新。"""
    task_name:     str = ""
    enemy_id:      str = ""
    current_count: int = 0