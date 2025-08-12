import logging
from typing import Dict, Any


class LotteryInterface:
    def __init__(self, player, game_state=None):
        self.player = player
        self.game_state = game_state  # 可选，用于状态管理
        self.logger = logging.getLogger('LotteryInterface')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('game.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_lottery_menu(self) -> Dict[str, Any]:
        """返回抽奖系统菜单选项"""
        self.logger.info("Fetching lottery system menu")
        return {
            "status": "success",
            "title": "抽奖系统",
            "options": [
                {"id": 1, "text": "单次抽奖"},
                {"id": 2, "text": "十连抽奖"},
                {"id": 3, "text": "百连抽奖"},
                {"id": 0, "text": "退出抽奖"}
            ]
        }

    def perform_lottery(self, draw_count: int, lottery_pool) -> Dict[str, Any]:
        """执行指定数量的抽奖"""
        self.logger.info(f"Attempting to perform lottery with {draw_count} draws")
        if draw_count not in [1, 10, 100]:
            self.logger.error(f"Invalid draw count: {draw_count}")
            return {"error": "无效的抽奖数量"}

        quantity_to_use = draw_count
        material_id = 120000  # 北斗白石 ID
        if not self.player.decrease_material_quantity(material_id, quantity_to_use):
            self.logger.error(f"Insufficient materials (ID: {material_id}) for {draw_count} draws")
            return {"error": f"北斗白石不足，需要 {quantity_to_use} 个"}

        try:
            results = lottery_pool.draw(draw_count)
            rewards = []
            for reward, probability in results:
                if reward:
                    quantity = 1  # 默认数量
                    # 根据概率调整数量（保持原逻辑）
                    if probability in [0.03, 0.17, 0.2, 0.3]:
                        quantity = 1
                    rewards.append({
                        "name": reward.name,
                        "quantity": quantity,
                        "item": reward  # 传递物品对象，供后续处理
                    })

            self.logger.info(f"Lottery completed: {draw_count} draws, {len(rewards)} rewards")
            # 返回奖励列表，交由 GameEngine 或 BagInterface 处理背包更新
            return {
                "status": "success",
                "message": f"消耗了 {quantity_to_use} 个北斗白石，抽奖完成",
                "rewards": [
                    {"name": r["name"], "quantity": r["quantity"]}
                    for r in rewards
                ],
                "reward_items": [r["item"] for r in rewards],  # 用于背包更新
                "next_action": "bag"  # 提示更新背包
            }
        except Exception as e:
            self.logger.error(f"Lottery failed: {str(e)}")
            return {"error": f"抽奖失败: {str(e)}"}
