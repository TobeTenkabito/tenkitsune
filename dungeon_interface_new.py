import logging
from typing import Dict, Any
from common.interact.dungeon_interact import Dungeon, DungeonFloor
from common.module.battle import Battle


class DungeonInterface:
    def __init__(self, player, game_state=None):
        self.player = player
        self.game_state = game_state
        self.logger = logging.getLogger('DungeonInterface')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('game.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_dungeon_menu(self) -> Dict[str, Any]:
        """返回秘境选择菜单"""
        self.logger.info("Fetching dungeon menu")
        dungeons = self.game_state.get_available_dungeons()  # 假设从 game_state 获取
        return {
            "status": "success",
            "title": "秘境选择",
            "dungeons": [
                {
                    "id": dungeon.number,
                    "name": dungeon.name,
                    "description": dungeon.description,
                    "completed": dungeon.completed
                }
                for dungeon in dungeons
            ]
        }

    def enter_dungeon(self, dungeon_id: int) -> Dict[str, Any]:
        """进入指定秘境"""
        self.logger.info(f"Entering dungeon {dungeon_id}")
        dungeon = self.game_state.get_dungeon(dungeon_id)  # 假设从 game_state 获取
        if not dungeon:
            self.logger.error(f"Dungeon {dungeon_id} not found")
            return {"error": f"秘境 {dungeon_id} 不存在"}

        can_enter, message = dungeon.check_access(self.player)
        if not can_enter:
            self.logger.warning(message)
            return {"error": message}

        affection_changes = dungeon.apply_npc_affection_impact(self.player)
        return {
            "status": "success",
            "message": f"进入了秘境: {dungeon.name} - {dungeon.description}",
            "dungeon_id": dungeon_id,
            "floors": [
                {
                    "number": floor.number,
                    "description": floor.description,
                    "has_npc": bool(floor.npc and floor.npc.number not in self.player.npcs_removed),
                    "has_enemies": bool(floor.enemies)
                }
                for floor in dungeon.floors
            ],
            "affection_changes": affection_changes
        }

    def enter_floor(self, dungeon_id: int, floor_number: int) -> Dict[str, Any]:
        """进入指定楼层"""
        self.logger.info(f"Entering floor {floor_number} of dungeon {dungeon_id}")
        dungeon = self.game_state.get_dungeon(dungeon_id)
        if not dungeon:
            self.logger.error(f"Dungeon {dungeon_id} not found")
            return {"error": f"秘境 {dungeon_id} 不存在"}

        floor = next((f for f in dungeon.floors if f.number == floor_number), None)
        if not floor:
            self.logger.error(f"Floor {floor_number} not found in dungeon {dungeon_id}")
            return {"error": f"楼层 {floor_number} 不存在"}

        # 检查 NPC 是否已被移除
        if floor.npc and floor.npc.number in self.player.npcs_removed:
            floor.npc = None

        # 处理 NPC 交互
        if floor.npc:
            return {
                "status": "success",
                "message": f"遇到了 NPC: {floor.npc.name}",
                "next_action": "npc",
                "npc_id": floor.npc.number
            }

        # 应用 buff
        buffs = floor.apply_buffs(self.player)

        # 处理战斗
        if floor.enemies:
            self.logger.info(f"Starting battle on floor {floor_number}")
            battle = Battle(self.player, [], floor.enemies)
            result = battle.run_battle()
            battle_status = battle.check_battle_status()

            if battle_status == "win":
                floor.completed = True
                is_first_time = self.player.highest_floor.get(dungeon_id, 0) < floor_number
                rewards = floor.get_rewards(is_first_time)
                applied_rewards = floor.apply_rewards(self.player, rewards)
                dungeon.update_progress(self.player, floor_number)
                return {
                    "status": "success",
                    "message": f"楼层 {floor_number} 完成！战斗胜利！",
                    "battle_result": battle_status,
                    "buffs": buffs,
                    "rewards": applied_rewards,
                    "next_action": "bag",
                    "completed": dungeon.completed
                }
            else:
                loss_info = dungeon.handle_loss(self.player)
                return {
                    "status": "error",
                    "message": f"楼层 {floor_number} 战斗失败！",
                    "battle_result": battle_status,
                    "loss_info": loss_info,
                    "next_action": "map"
                }

        # 无敌人，直接完成
        is_first_time = self.player.highest_floor.get(dungeon_id, 0) < floor_number
        rewards = floor.get_rewards(is_first_time)
        applied_rewards = floor.apply_rewards(self.player, rewards)
        floor.completed = True
        dungeon.update_progress(self.player, floor_number)
        return {
            "status": "success",
            "message": f"楼层 {floor_number} 完成！",
            "buffs": buffs,
            "rewards": applied_rewards,
            "next_action": "bag",
            "completed": dungeon.completed
        }