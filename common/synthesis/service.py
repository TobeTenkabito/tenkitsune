"""
common.synthesis.service
─────────────────────────────────────────────
SynthesisService — 純邏輯層，不直接修改玩家狀態。
所有有副作用的操作透過 EventBus emit 事件，
由 SynthesisHandler 執行。
"""

from __future__ import annotations

from library.material_library  import material_library
from library.equipment_library import equipment_library
from library.medicine_library  import medicine_library
from library.product_library   import product_library
from all.synthesis_recipes     import synthesis_recipes

from common.event import EventBus
from common.event.system.synthesis import (
    SynthesisRequestEvent,
    SynthesisListRequestEvent,
)


class SynthesisService:
    """
    對外 API（UI / NPC 合成模組呼叫此類）。
    """

    # ── 純查詢 ────────────────────────────────────────────

    @staticmethod
    def can_synthesize(player, target_number, quantity: int = 1) -> tuple[bool, str]:
        """
        檢查玩家材料是否足夠。
        回傳 (ok: bool, message: str)。
        """
        if target_number not in synthesis_recipes:
            return False, "無此合成配方"

        required = synthesis_recipes[target_number]["materials"]
        for mat_num, req_qty in required.items():
            if player.get_material_quantity(mat_num) < req_qty * quantity:
                return False, "材料不足或配方不正確"

        return True, "可以合成"

    @staticmethod
    def get_result_item(target_number):
        """
        從各 library 查詢合成結果物品原型。
        回傳物品物件（未複製）。
        """
        for lib in (material_library, equipment_library,
                    medicine_library, product_library):
            if target_number in lib:
                return lib[target_number]
        raise KeyError(f"合成目標 {target_number} 不存在於已知庫中")

    @staticmethod
    def get_available_targets(player) -> list:
        """
        回傳當前玩家可合成的目標編號清單。
        """
        result = []
        for target_number, recipe in synthesis_recipes.items():
            required = recipe["materials"]
            if all(
                player.get_material_quantity(mat_num) >= req_qty
                for mat_num, req_qty in required.items()
            ):
                result.append(target_number)
        return result

    # ── 有副作用的操作（emit 事件） ───────────────────────

    @staticmethod
    def synthesize(player, target_number, quantity: int = 1):
        """
        發起合成請求。
        實際扣材料 / 加背包由 SynthesisHandler 執行。
        """
        EventBus.emit(SynthesisRequestEvent(
            player_name=getattr(player, "name", ""),
            target_number=target_number,
            quantity=quantity,
        ))

    @staticmethod
    def request_list(player):
        """
        請求可合成清單（由 SynthesisHandler 回傳 SynthesisListResultEvent）。
        """
        EventBus.emit(SynthesisListRequestEvent(
            player_name=getattr(player, "name", ""),
        ))