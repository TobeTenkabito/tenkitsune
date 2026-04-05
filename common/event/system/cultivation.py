"""
common.event.system.cultivation
───────────────────────────────────────────────────────────────
修為（五行）與心法相關事件。
"""

from __future__ import annotations
from dataclasses import dataclass
from common.event.bus import BattleEvent


# ══════════════════════════════════════════════════════════════
#  修為（五行）
# ══════════════════════════════════════════════════════════════

@dataclass
class CultivationUpgradeEvent(BattleEvent):
    """
    五行修為升級成功時發送。
    供 UI 顯示升級結果、記錄 log 等。
    """
    player:           str = ""
    element:          str = ""    # "金" | "木" | "水" | "火" | "土"
    new_level:        int = 0
    cost:             int = 0
    remaining_points: int = 0

@dataclass
class CultivationResetEvent(BattleEvent):
    """
    五行修為全部重置時發送。
    供 UI 顯示返還點數、刷新面板等。
    """
    player:          str = ""
    returned_points: int = 0


# ══════════════════════════════════════════════════════════════
#  心法
# ══════════════════════════════════════════════════════════════

@dataclass
class XinfaUnlockEvent(BattleEvent):
    """
    心法技能成功解鎖時發送。
    供 UI 顯示解鎖動畫、更新技能欄等。
    """
    player:     str = ""
    xinfa_name: str = ""    # 心法線名稱，如「重陽功」
    level:      int = 0     # 解鎖的心法等級（1-based）
    skill_name: str = ""

@dataclass
class XinfaResetEvent(BattleEvent):
    """
    心法技能被移除時發送（重置修為時逐級觸發）。
    removed=True 表示背包移除成功，False 表示背包中找不到。
    """
    player:     str  = ""
    xinfa_name: str  = ""
    level:      int  = 0
    skill_name: str  = ""
    removed:    bool = False