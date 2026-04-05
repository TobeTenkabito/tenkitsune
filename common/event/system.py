"""
通用系統事件
─────────────────────────────────────────────
WarningEvent、HealEvent 等跨模組通用事件
"""

from __future__ import annotations
from dataclasses import dataclass
from common.event.bus import BattleEvent


@dataclass
class WarningEvent(BattleEvent):
    message: str

@dataclass
class HealEvent(BattleEvent):
    target: str
    amount: float
    source: str
    