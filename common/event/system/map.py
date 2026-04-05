"""
common.event.system.map
─────────────────────────────────────────────
地圖相關事件。
"""

from __future__ import annotations
from dataclasses import dataclass
from common.event.bus import BattleEvent


@dataclass
class MapWarpRequestEvent(BattleEvent):
    """請求跳轉地圖（失敗離開秘境 / 其他傳送）。"""
    player_location: int | str = 0
    reason:          str       = ""   # "dungeon_loss" | "other"