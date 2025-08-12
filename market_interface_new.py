# interface/market_interface_new.py
import logging
from typing import Dict, Any


class MarketInterface:
    def __init__(self, player, market, game_state=None):
        self.player = player
        self.market = market
        self.game_state = game_state  # 可选，用于状态管理
        self.logger = logging.getLogger('MarketInterface')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('game.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_market_menu(self) -> Dict[str, Any]:
        """返回市场系统菜单选项"""
        self.logger.info("Fetching market system menu")
        return {
            "status": "success",
            "title": "市场系统",
            "options": [
                {"id": 1, "text": "出售物品"},
                {"id": 2, "text": "购买物品"},
                {"id": 3, "text": "刷新市场"},
                {"id": 0, "text": "退出市场"}
            ]
        }

    def get_market_items(self) -> Dict[str, Any]:
        """返回市场物品列表"""
        self.logger.info("Fetching market items")
        items = [
            {
                "number": item.number,
                "name": item.name,
                "price": item.price,  # 假设 Market 提供价格
                "description": item.description
            }
            for item in self.market.items_for_sale
        ]
        return {
            "status": "success",
            "items": items,
            "message": "市场物品列表" if items else "市场当前无物品"
        }

    def sell_item(self, item_number: int, quantity: int) -> Dict[str, Any]:
        """出售背包中的物品"""
        self.logger.info(f"Attempting to sell item {item_number} with quantity {quantity}")
        item = self.player.get_inventory_item(item_number)
        if not item:
            self.logger.error(f"Item {item_number} not found in inventory")
            return {"error": "背包中没有该物品"}

        try:
            success, message = self.market.sell_item(self.player, item, quantity)
            if success:
                self.logger.info(f"Sold item {item.name} x{quantity}: {message}")
                return {
                    "status": "success",
                    "message": message,
                    "next_action": "bag"  # 提示更新背包
                }
            else:
                self.logger.error(f"Failed to sell item {item.name}: {message}")
                return {"error": message}
        except Exception as e:
            self.logger.error(f"Failed to sell item {item_number}: {str(e)}")
            return {"error": f"出售物品失败: {str(e)}"}

    def buy_item(self, item_number: int, quantity: int) -> Dict[str, Any]:
        """购买市场中的物品"""
        self.logger.info(f"Attempting to buy item {item_number} with quantity {quantity}")
        item = self.market.get_market_item(item_number)
        if not item:
            self.logger.error(f"Item {item_number} not found in market")
            return {"error": "市场中没有该物品"}

        try:
            success, message = self.market.buy_item(self.player, item, quantity)
            if success:
                self.logger.info(f"Bought item {item.name} x{quantity}: {message}")
                return {
                    "status": "success",
                    "message": message,
                    "next_action": "bag",  # 提示更新背包
                    "task_trigger": item.is_task_related if hasattr(item, "is_task_related") else False  # 示例：任务道具
                }
            else:
                self.logger.error(f"Failed to buy item {item.name}: {message}")
                return {"error": message}
        except Exception as e:
            self.logger.error(f"Failed to buy item {item_number}: {str(e)}")
            return {"error": f"购买物品失败: {str(e)}"}

    def refresh_market(self) -> Dict[str, Any]:
        """刷新市场物品"""
        self.logger.info("Attempting to refresh market")
        try:
            self.market.items_for_sale = self.market.refresh_market()
            items = [
                {"number": item.number, "name": item.name, "price": item.price, "description": item.description}
                for item in self.market.items_for_sale
            ]
            self.logger.info("Market refreshed successfully")
            return {
                "status": "success",
                "message": "市场已刷新",
                "items": items
            }
        except Exception as e:
            self.logger.error(f"Failed to refresh market: {str(e)}")
            return {"error": f"市场刷新失败: {str(e)}"}