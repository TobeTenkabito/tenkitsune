# common/interact/map_interface_new.py
import logging
from typing import Dict, Any


class MapInterface:
    def __init__(self, player, game_state=None):
        self.player = player
        self.game_state = game_state
        self.logger = logging.getLogger('MapInterface')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('game.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_map_menu(self) -> Dict[str, Any]:
        """返回地图选择菜单"""
        self.logger.info("Fetching map menu")
        maps = self.game_state.get_available_maps()
        return {
            "status": "success",
            "title": "地图选择",
            "maps": [
                {
                    "id": map_obj.number,
                    "name": map_obj.name,
                    "description": map_obj.description,
                    "adjacent_maps": [
                        {"id": map_id, "distance": info["distance"], "direction": info["direction"]}
                        for map_id, info in map_obj.adjacent_maps.items()
                    ]
                }
                for map_obj in maps
            ]
        }

    def explore_area(self, map_id: int) -> Dict[str, Any]:
        """探索指定地图"""
        self.logger.info(f"Exploring map {map_id}")
        map_obj = self.game_state.get_map(map_id)  # 假设从 game_state 获取
        if not map_obj:
            self.logger.error(f"Map {map_id} not found")
            return {"error": f"地图 {map_id} 不存在"}

        can_enter, message = map_obj.can_enter(self.player)
        if not can_enter:
            self.logger.warning(message)
            return {"error": message}

        return {
            "status": "success",
            "message": f"正在探索 {map_obj.name}: {map_obj.description}",
            "map_id": map_id,
            "npcs": map_obj.get_npcs(),
            "battles": map_obj.get_battles(),
            "collectibles": map_obj.get_collectibles(),
            "dungeons": map_obj.get_dungeons(),
            "adjacent_maps": [
                {"id": map_id, "distance": info["distance"], "direction": info["direction"]}
                for map_id, info in map_obj.adjacent_maps.items()
            ]
        }

    def interact_with_npc(self, map_id: int, npc_id: int) -> Dict[str, Any]:
        """与指定 NPC 交互"""
        self.logger.info(f"Interacting with NPC {npc_id} on map {map_id}")
        map_obj = self.game_state.get_map(map_id)
        if not map_obj:
            self.logger.error(f"Map {map_id} not found")
            return {"error": f"地图 {map_id} 不存在"}

        npc = next((npc for npc in map_obj.npcs if npc.number == npc_id), None)
        if not npc:
            self.logger.error(f"NPC {npc_id} not found on map {map_id}")
            return {"error": f"NPC {npc_id} 不存在"}

        return {
            "status": "success",
            "message": f"与 {npc.name} 交互",
            "next_action": "npc",
            "npc_id": npc_id
        }

    def collect_item(self, map_id: int, item_name: str) -> Dict[str, Any]:
        """采集指定物品"""
        self.logger.info(f"Collecting item {item_name} on map {map_id}")
        map_obj = self.game_state.get_map(map_id)
        if not map_obj:
            self.logger.error(f"Map {map_id} not found")
            return {"error": f"地图 {map_id} 不存在"}

        success, result = map_obj.collect_item(item_name, self.player)
        if not success:
            self.logger.warning(result["error"])
            return {"error": result["error"]}

        return {
            "status": "success",
            "message": f"成功采集到 {result['item']} x {result['quantity']}",
            "item": result["item"],
            "quantity": result["quantity"],
            "next_action": "bag"
        }

    def start_battle(self, map_id: int, battle_index: int) -> Dict[str, Any]:
        """开始指定战斗"""
        self.logger.info(f"Starting battle {battle_index} on map {map_id}")
        map_obj = self.game_state.get_map(map_id)
        if not map_obj:
            self.logger.error(f"Map {map_id} not found")
            return {"error": f"地图 {map_id} 不存在"}

        result = map_obj.handle_battle(battle_index, self.player)
        if "error" in result:
            self.logger.error(result["error"])
            return {"error": result["error"]}

        if result["result"] == "loss":
            return {
                "status": "error",
                "message": "战斗失败，你被野怪击晕！",
                "battle_result": result["result"],
                "loss_info": {
                    "hp": result["hp"],
                    "exp_loss": result["exp_loss"],
                    "exp_loss_percentage": result["exp_loss_percentage"]
                },
                "next_action": "map"
            }
        return {
            "status": "success",
            "message": f"{self.player.name} 战胜了敌人！",
            "battle_result": result["result"],
            "next_action": None
        }

    def enter_dungeon(self, map_id: int, dungeon_id: int) -> Dict[str, Any]:
        """进入指定秘境"""
        self.logger.info(f"Entering dungeon {dungeon_id} on map {map_id}")
        map_obj = self.game_state.get_map(map_id)
        if not map_obj:
            self.logger.error(f"Map {map_id} not found")
            return {"error": f"地图 {map_id} 不存在"}

        dungeon = next((d for d in map_obj.dungeons if d.number == dungeon_id), None)
        if not dungeon:
            self.logger.error(f"Dungeon {dungeon_id} not found on map {map_id}")
            return {"error": f"秘境 {dungeon_id} 不存在"}

        return {
            "status": "success",
            "message": f"进入秘境 {dungeon.name}",
            "next_action": "dungeon",
            "dungeon_id": dungeon_id
        }