import random
from copy import deepcopy
from all.gamestate import game_state

class Map:
    def __init__(self, number, name, description, adjacent_maps, npcs,
                 battles, collectible_items, dungeons=None, passport=None, unpasstext=None, passtext=None):
        self.number = number
        self.name = name
        self.description = description
        self.adjacent_maps = adjacent_maps
        self.npcs = npcs
        self.battles = battles
        self.collectible_items = collectible_items
        self.dungeons = dungeons or []
        self.passport = passport
        self.unpasstext = unpasstext
        self.passtext = passtext

    def add_adjacent_map(self, map_number, distance, direction="双向", map_factory=None):
        """添加邻接地图"""
        self.adjacent_maps[map_number] = {"distance": distance, "direction": direction}
        if direction == "双向" and map_factory:
            adjacent_map = map_factory(map_number)
            adjacent_map.adjacent_maps[self.number] = {"distance": distance, "direction": direction}

    def can_enter(self, player) -> tuple[bool, str]:
        """检查玩家是否可以进入地图"""
        if self.passport is None:
            return True, self.passtext or "可以进入地图"
        elif isinstance(self.passport, dict):
            if "AND" in self.passport:
                if not all(player.has_item(item) for item in self.passport["AND"]):
                    return False, self.unpasstext or "缺少必要通行证"
            elif "OR" in self.passport:
                if not any(player.has_item(item) for item in self.passport["OR"]):
                    return False, self.unpasstext or "缺少通行证"
        else:
            if not player.has_item(self.passport):
                return False, self.unpasstext or "缺少通行证"
        return True, self.passtext or "可以进入地图"

    def get_npcs(self) -> list:
        """获取地图上的 NPC 列表"""
        return [{"number": npc.number, "name": npc.name, "description": npc.description} for npc in self.npcs]

    def get_battles(self) -> list:
        """获取地图上的战斗场景"""
        return [
            {"index": i, "enemies": [enemy.name for enemy in enemy_list]}
            for i, enemy_list in enumerate(self.battles)
        ]

    def get_collectibles(self) -> list:
        """获取地图上的可采集物品"""
        return [
            {"name": item.name, "success_rate": info["success_rate"], "quantity_range": info["quantity_range"]}
            for item, info in self.collectible_items.items()
        ]

    def get_dungeons(self) -> list:
        """获取地图上的秘境"""
        return [
            {"number": dungeon.number, "name": dungeon.name, "description": dungeon.description}
            for dungeon in self.dungeons
        ]

    def collect_item(self, item_name: str, player) -> tuple[bool, dict]:
        """采集指定物品"""
        item_info = self.collectible_items.get(item_name)
        if not item_info:
            return False, {"error": f"物品 {item_name} 不存在"}
        success_rate = item_info["success_rate"]
        quantity_range = item_info["quantity_range"]
        if random.uniform(0, 1) <= success_rate:
            quantity = random.randint(quantity_range[0], quantity_range[1]) if isinstance(quantity_range, tuple) else quantity_range
            collect_item = deepcopy(item_info["item"])
            collect_item.quantity = quantity
            player.add_to_inventory(collect_item)
            return True, {"item": collect_item.name, "quantity": quantity}
        return False, {"error": f"采集 {item_name} 失败"}

    def handle_battle(self, battle_index: int, player) -> dict:
        """处理战斗"""
        from common.module.battle import Battle
        if not (0 <= battle_index < len(self.battles)):
            return {"error": "无效的战斗场景"}
        battle = Battle(player, [], self.battles[battle_index])
        result = battle.run_battle()
        if result == "loss":
            player.hp = 1
            exp_loss_percentage = random.uniform(0.01, 0.1)
            exp_loss = int(player.exp * exp_loss_percentage)
            player.exp = max(0, player.exp - exp_loss)
            return {
                "result": "loss",
                "hp": player.hp,
                "exp_loss": exp_loss,
                "exp_loss_percentage": exp_loss_percentage
            }
        return {"result": result}

    def remove_npc(self, npc_number: int) -> tuple[bool, str]:
        """从地图中移除 NPC"""
        initial_len = len(self.npcs)
        self.npcs = [npc for npc in self.npcs if npc.number != npc_number]
        if len(self.npcs) < initial_len:
            return True, f"NPC {npc_number} 已从地图 {self.name} 移除"
        return False, f"未找到 NPC {npc_number} 在地图 {self.name}"