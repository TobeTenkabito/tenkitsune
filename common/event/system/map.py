"""
common.event.system.map
地圖 / 移動相關事件。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from common.event.bus import BattleEvent


@dataclass
class MapWarpRequestEvent(BattleEvent):
    """請求離開當前地圖（戰敗 / 秘境失敗 / 傳送）。"""
    player_location: int | str = 0
    reason: str = ""          # "monster_defeat" | "dungeon_loss" | "other"
    exp_loss: int = 0         # 已計算好的扣除量，由 handler 執行


@dataclass
class ShowAdjacentMapsEvent(BattleEvent):
    """請求顯示並選擇相鄰地圖。"""
    player_location: int | str = 0
    