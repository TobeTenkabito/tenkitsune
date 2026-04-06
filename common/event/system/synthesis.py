"""
common.event.system.synthesis
合成系統相關事件。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from common.event.bus import BattleEvent


@dataclass
class SynthesisRequestEvent(BattleEvent):
    """UI 發起合成請求。"""
    player_name:          str       = ""
    target_number:        int | str = 0
    quantity:             int       = 1


@dataclass
class SynthesisSucceededEvent(BattleEvent):
    """合成成功，通知 UI 顯示結果。"""
    player_name:          str       = ""
    target_number:        int | str = 0
    result_item_name:     str       = ""
    result_quantity:      int       = 0


@dataclass
class SynthesisFailedEvent(BattleEvent):
    """合成失敗，通知 UI 顯示原因。"""
    player_name:          str       = ""
    target_number:        int | str = 0
    reason:               str       = ""


@dataclass
class SynthesisListRequestEvent(BattleEvent):
    """UI 請求取得當前可合成清單。"""
    player_name:          str       = ""


@dataclass
class SynthesisListResultEvent(BattleEvent):
    """回傳可合成清單給 UI。"""
    player_name:          str       = ""
    available_targets:    list      = field(default_factory=list)