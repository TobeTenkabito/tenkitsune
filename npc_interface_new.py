# common/interact/npc_interface_new.py
import logging
from typing import Dict, Any
from common.interact.npc_interact import NPC


class NPCInterface:
    def __init__(self, player, npc: NPC, game_state=None):
        self.player = player
        self.npc = npc
        self.game_state = game_state  # 可选，用于状态管理
        self.logger = logging.getLogger('NPCInterface')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('game.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_interact_menu(self) -> Dict[str, Any]:
        """返回 NPC 交互菜单"""
        self.logger.info(f"Fetching interaction menu for NPC {self.npc.name}")
        options = [
            {"id": 1, "text": "日常对话"},
            {"id": 2, "text": "接取任务"},
            {"id": 3, "text": "任务对话"},
            {"id": 4, "text": "交付任务"},
            {"id": 5, "text": "赠送物品"},
            {"id": 6, "text": "交易、学习、打造"},
            {"id": 7, "text": "退出对话"}
        ]
        if self.npc.affection >= -25:
            options.insert(1, {"id": 8, "text": "功能模块"})
        return {
            "status": "success",
            "title": f"与 {self.npc.name} 互动",
            "options": options,
            "npc_info": {
                "name": self.npc.name,
                "affection": self.npc.affection,
                "race": self.npc.race
            }
        }

    def handle_daily_dialogue(self) -> Dict[str, Any]:
        """处理日常对话"""
        self.logger.info(f"Handling daily dialogue with NPC {self.npc.name}")
        dialogue = self.npc.get_daily_dialogue()
        return {
            "status": "success",
            "message": f"{self.npc.name}: {dialogue}",
            "options": [
                {"id": 1, "text": "继续对话"},
                {"id": 2, "text": "其它事情"},
                {"id": 3, "text": "结束对话"}
            ] if self.npc.affection >= -25 else []
        }

    def continue_dialogue(self) -> Dict[str, Any]:
        """继续日常对话"""
        self.logger.info(f"Continuing dialogue with NPC {self.npc.name}")
        dialogue = self.npc.get_daily_dialogue()
        return {
            "status": "success",
            "message": f"{self.npc.name}: {dialogue}"
        }

    def get_function_modules(self) -> Dict[str, Any]:
        """返回功能模块菜单"""
        self.logger.info(f"Fetching function modules for NPC {self.npc.name}")
        if self.npc.affection < -25:
            return {"error": f"{self.npc.name} 对你已经失去了信任，无法调用任何功能模块。"}
        options = [{"id": 4, "text": "返回"}]
        if self.npc.affection >= 0:
            options.insert(0, {"id": 1, "text": "市场"})
            options.insert(1, {"id": 2, "text": "战斗"})
            options.insert(2, {"id": 3, "text": "合成"})
        return {
            "status": "success",
            "title": "功能模块",
            "options": options
        }

    def accept_task(self, task_index: int) -> Dict[str, Any]:
        """接取任务"""
        self.logger.info(f"Attempting to accept task {task_index} from NPC {self.npc.name}")
        if self.npc.affection < -25:
            return {"error": f"{self.npc.name} 对你已经失去了信任，不愿意给你任何任务。"}
        success, message = self.npc.accept_task(task_index, self.player)
        tasks = [
            {"index": i, "name": task.name}
            for i, task in enumerate(self.npc.get_available_tasks())
        ]
        return {
            "status": "success" if success else "error",
            "message": message,
            "tasks": tasks,
            "next_action": "task" if success else None
        }

    def complete_task_dialogue(self) -> Dict[str, Any]:
        """处理任务完成对话"""
        self.logger.info(f"Handling task completion dialogue with NPC {self.npc.name}")
        success, message = self.npc.complete_task_dialogue(self.player)
        return {
            "status": "success" if success else "error",
            "message": message,
            "next_action": "task" if success else None
        }

    def deliver_task(self) -> Dict[str, Any]:
        """交付任务"""
        self.logger.info(f"Attempting to deliver task to NPC {self.npc.name}")
        success, message = self.npc.deliver_task(self.player)
        return {
            "status": "success" if success else "error",
            "message": message,
            "next_action": "task" if success else None
        }

    def get_inventory(self) -> Dict[str, Any]:
        """返回玩家背包物品列表"""
        self.logger.info(f"Fetching inventory for NPC {self.npc.name} gift")
        inventory_items = self.player.get_inventory()
        items = [
            {
                "index": i + 1,
                "name": item.name,
                "quantity": item.quantity,
                "number": item.number
            }
            for i, item in enumerate(inventory_items)
        ]
        return {
            "status": "success",
            "items": items,
            "message": "背包物品列表" if items else "你没有可以赠送的物品。"
        }

    def give_gift(self, item_index: int, quantity: int) -> Dict[str, Any]:
        """赠送物品"""
        self.logger.info(f"Attempting to give gift {item_index} x{quantity} to NPC {self.npc.name}")
        inventory_items = self.player.get_inventory()
        if not (1 <= item_index <= len(inventory_items)):
            self.logger.error(f"Invalid item index {item_index}")
            return {"error": "无效的物品编号。"}
        item = inventory_items[item_index - 1]
        if quantity < 1 or quantity > item.quantity:
            self.logger.error(f"Invalid quantity {quantity} for item {item.name}")
            return {"error": f"无效的数量 (1-{item.quantity})"}

        try:
            affection_change, message = self.npc.receive_gift(item, quantity)
            self.player.remove_from_inventory(item.number, quantity)
            self.player.give_item_to_npc(self.npc.number, item.number, quantity)
            task_updated = False
            for task in self.player.accepted_tasks:
                if task.check_completion(self.player):
                    task_updated = True
            self.logger.info(f"Gift {item.name} x{quantity} given to NPC {self.npc.name}, affection +{affection_change}")
            return {
                "status": "success",
                "message": message,
                "affection": self.npc.affection,
                "next_action": "bag",
                "task_trigger": task_updated
            }
        except Exception as e:
            self.logger.error(f"Failed to give gift to NPC {self.npc.name}: {str(e)}")
            return {"error": f"赠送物品失败: {str(e)}"}

    def handle_exchange(self, exchange_index: int) -> Dict[str, Any]:
        """处理交易"""
        self.logger.info(f"Attempting to exchange item {exchange_index} with NPC {self.npc.name}")
        success, message = self.npc.exchange_item(exchange_index, self.player)
        exchange_items = [
            {
                "index": i,
                "offered_item": offered_item.name,
                "required_item": details["item"].name,
                "required_quantity": details["quantity"]
            }
            for i, (offered_item, details) in enumerate(self.npc.exchange.items())
        ]
        return {
            "status": "success" if success else "error",
            "message": message,
            "exchange_items": exchange_items,
            "next_action": "bag" if success else None
        }

    def start_battle(self) -> Dict[str, Any]:
        """开始战斗"""
        self.logger.info(f"Starting battle with NPC {self.npc.name}")
        result = self.npc.go_battle(self.player)
        if result == "no_battle":
            return {"error": f"{self.npc.name} 没有准备战斗信息。"}
        message = (f"你战胜了 {self.npc.name}！" if result == "win" else
                   f"你被 {self.npc.name} 打败了！{self.npc.name} 说：'{self.npc.get_random_taunt()}'")
        return {
            "status": "success",
            "message": message,
            "result": result,
            "options": [{"id": 1, "text": "杀死 NPC"}, {"id": 2, "text": "放过 NPC"}] if result == "win" else []
        }

    def handle_battle_result(self, kill: bool) -> Dict[str, Any]:
        """处理战斗结果"""
        self.logger.info(f"Handling battle result for NPC {self.npc.name}, kill: {kill}")
        if kill:
            message = self.npc.remove_npc()
            return {
                "status": "success",
                "message": message,
                "npc_removed": True
            }
        return {
            "status": "success",
            "message": f"{self.npc.name} 感谢你放他一条生路。"
        }
