"""
DropProcessor
負責處理敵人死亡後的掉落物邏輯：
  1. 合併必掉 + 機率掉落
  2. 透過 Registry 查找物品原型
  3. 加入玩家背包
"""
import copy
import random

from common.module.item import Equipment, Material, Product, Medicine, Warp, Skill
from core.registry import registry
from common.battle.event import (
    BattleEventBus,
    DropEvent,
    WarningEvent,
)


class DropProcessor:

    @staticmethod
    def process(player, enemy) -> list:
        """
        處理 enemy 的掉落，加入 player 背包。
        返回 [(item_name, quantity), ...] 供戰鬥日誌顯示。
        """
        drop_summary = DropProcessor._resolve_drops(enemy)
        result = []

        for item_id, total_quantity in drop_summary.items():
            prototype = DropProcessor._get_item(item_id)
            if prototype is None:
                BattleEventBus.emit(WarningEvent(
                    message=f"無法識別的掉落物 ID: {item_id}"
                ))
                continue

            new_item = copy.deepcopy(prototype)
            result.extend(
                DropProcessor._add_to_player(player, new_item, total_quantity)
            )

        if result:
            BattleEventBus.emit(DropEvent(
                enemy=enemy.name,
                items=[{"name": name, "quantity": qty} for name, qty in result],
            ))

        return result

    # ── 私有方法 ──────────────────────────────────────────────

    @staticmethod
    def _resolve_drops(enemy) -> dict:
        """合併必掉 + 機率掉落，返回 {item_id: total_quantity}。"""
        summary = {}
        for item_id, quantity in getattr(enemy, "drops", []):
            summary[item_id] = summary.get(item_id, 0) + quantity
        for item_id, quantity, chance in getattr(enemy, "chance_drops", []):
            if random.random() < chance:
                summary[item_id] = summary.get(item_id, 0) + quantity
        return summary

    @staticmethod
    def _get_item(item_id):
        """透過 Registry 查找物品原型。"""
        for category in ("material", "equipment", "product", "warp", "medicine", "skill"):
            item = registry.get(category, item_id)
            if item is not None:
                return item
        return None

    @staticmethod
    def _add_to_player(player, item, total_quantity) -> list:
        """根據物品類型決定加入方式，返回日誌列表。"""
        logs = []

        if isinstance(item, (Material, Product)):
            item.quantity = total_quantity
            player.add_to_inventory(item)
            logs.append((item.name, total_quantity))

        elif isinstance(item, Equipment):
            for _ in range(total_quantity):
                player.add_to_inventory(copy.copy(item))
                logs.append((item.name, 1))

        elif isinstance(item, (Medicine, Warp, Skill)):
            for _ in range(total_quantity):
                player.add_to_inventory(copy.copy(item))
                logs.append((item.name, 1))

        return logs
