"""
common.synthesis.ui
─────────────────────────────────────────────
SynthesisUI — 合成介面（NPC 合成模組 / 獨立介面均可呼叫）。
訂閱結果事件顯示訊息，呼叫 SynthesisService 發起請求。
"""

from __future__ import annotations

from typing import Callable

from library.material_library  import material_library
from library.equipment_library import equipment_library
from library.medicine_library  import medicine_library
from library.product_library   import product_library

from common.event import EventBus, InfoEvent, WarningEvent
from common.event.system.synthesis import (
    SynthesisSucceededEvent,
    SynthesisFailedEvent,
    SynthesisListResultEvent,
)
from common.synthesis.service import SynthesisService


class SynthesisUI:
    """
    使用方式：
        ui = SynthesisUI(player_resolver=lambda: player)
        ui.open()
    """

    def __init__(self, player_resolver: Callable):
        self._get_player = player_resolver

        # 訂閱結果事件（顯示用）
        EventBus.subscribe(SynthesisSucceededEvent, self._on_success)
        EventBus.subscribe(SynthesisFailedEvent,    self._on_failed)
        EventBus.subscribe(SynthesisListResultEvent, self._on_list_result)

        self._pending_targets: list = []   # 暫存可合成清單

    # ── 主介面 ────────────────────────────────────────────

    def open(self):
        player = self._get_player()
        if not player:
            EventBus.emit(WarningEvent(message="未找到玩家對象，無法開啟合成介面。"))
            return

        while True:
            # 取得可合成清單（同步：直接呼叫 service）
            self._pending_targets = SynthesisService.get_available_targets(player)

            if not self._pending_targets:
                EventBus.emit(InfoEvent(message="目前沒有可合成的配方。"))
                return

            lines = ["可合成的物品："]
            for i, target_num in enumerate(self._pending_targets, 1):
                item = self._resolve_name(target_num)
                lines.append(f"{i}. {item}")
            lines.append("0. 返回")
            EventBus.emit(InfoEvent(message="\n".join(lines)))

            choice = input("請輸入合成目標編號: ")
            if choice == "0":
                return

            try:
                idx = int(choice) - 1
                if not (0 <= idx < len(self._pending_targets)):
                    EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))
                    continue
            except ValueError:
                EventBus.emit(WarningEvent(message="無效的輸入，請輸入數字。"))
                continue

            target_num = self._pending_targets[idx]

            qty_str = input("請輸入合成數量（預設 1）: ").strip() or "1"
            try:
                quantity = int(qty_str)
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                EventBus.emit(WarningEvent(message="無效的數量，請輸入正整數。"))
                continue

            # 發起合成請求（由 SynthesisHandler 執行副作用）
            SynthesisService.synthesize(player, target_num, quantity)

    # ── 結果事件 Handler ──────────────────────────────────

    def _on_success(self, event: SynthesisSucceededEvent):
        EventBus.emit(InfoEvent(
            message=f"合成成功！獲得 {event.result_item_name} x{event.result_quantity}。"
        ))

    def _on_failed(self, event: SynthesisFailedEvent):
        EventBus.emit(WarningEvent(
            message=f"合成失敗：{event.reason}"
        ))

    def _on_list_result(self, event: SynthesisListResultEvent):
        self._pending_targets = event.available_targets

    # ── 輔助 ─────────────────────────────────────────────

    @staticmethod
    def _resolve_name(target_num) -> str:
        for lib in (material_library, equipment_library,
                    medicine_library, product_library):
            if target_num in lib:
                return lib[target_num].name
        return str(target_num)