from copy import deepcopy
from all.gamestate import game_state
import random


class DungeonFloor:
    def __init__(self, number, description, enemies=None, npc=None, entry_buff=None,
                 rewards=None, first_time_rewards=None, random_rewards=None, restrictions=None):
        self.number = number
        self.description = description
        self.enemies = enemies if enemies is not None else []
        self.npc = npc
        self.entry_buff = entry_buff
        self.rewards = rewards if rewards else []
        self.first_time_rewards = first_time_rewards if first_time_rewards else []
        self.random_rewards = random_rewards if random_rewards else []
        self.restrictions = restrictions if restrictions is not None else {}
        self.completed = False

    def apply_buffs(self, player) -> list:
        """应用楼层入口 buff"""
        applied_buffs = []
        if self.entry_buff:
            buffs = self.entry_buff if isinstance(self.entry_buff, list) else [self.entry_buff]
            for buff in buffs:
                player.add_buff(deepcopy(buff))
                applied_buffs.append({"name": buff.name})
        return applied_buffs

    def get_rewards(self, is_first_time: bool) -> list:
        """获取楼层奖励"""
        rewards_list = []
        if is_first_time and self.first_time_rewards:
            rewards_list.extend(deepcopy(self.first_time_rewards))
        if self.rewards:
            rewards_list.extend(deepcopy(self.rewards))
        if self.random_rewards:
            for reward in self.random_rewards:
                if random.random() <= reward.get("chance", 1.0):
                    rewards_list.append(deepcopy(reward))
        return rewards_list

    def apply_rewards(self, player, rewards: list) -> list:
        """应用奖励到玩家"""
        applied_rewards = []
        for reward in rewards:
            if reward["type"] == "item":
                reward_item = deepcopy(reward["item"])
                reward_item.quantity = reward["quantity"]
                player.add_to_inventory(reward_item)
                applied_rewards.append({"type": "item", "name": reward_item.name, "quantity": reward["quantity"]})
            elif reward["type"] == "exp":
                player.gain_exp(reward["amount"])
                applied_rewards.append({"type": "exp", "amount": reward["amount"]})
            elif reward["type"] == "attribute":
                player.gain_dungeon_attribute(reward["attribute"], reward["value"])
                applied_rewards.append({"type": "attribute", "attribute": reward["attribute"], "value": reward["value"]})
        return applied_rewards

    def remove_npc(self) -> str:
        """移除楼层 NPC"""
        if self.npc:
            npc_name = self.npc.name
            self.npc = None
            return f"NPC {npc_name} 已从秘境的第 {self.number} 层移除。"
        return f"该楼层 {self.number} 没有 NPC 需要移除。"


class Dungeon:
    def __init__(self, name, number, description, floors, can_replay_after_completion=True, npc_affection_impact=None):
        self.name = name
        self.number = number
        self.description = description
        self.floors = floors
        self.highest_floor = 0
        self.completed = False
        self.can_replay_after_completion = can_replay_after_completion
        self.npc_affection_impact = npc_affection_impact if npc_affection_impact else {}
        self.player_restrictions = {}

    def apply_npc_affection_impact(self, player) -> list:
        """应用 NPC 好感度影响"""
        from library.npc_library import npc_library
        changes = []
        for npc_id, affection_change in self.npc_affection_impact.items():
            npc = npc_library.get(npc_id)
            if npc:
                npc.affection += affection_change
                changes.append({"npc_name": npc.name, "affection_change": affection_change})
        return changes

    def check_access(self, player) -> tuple[bool, str]:
        """检查玩家是否可以进入秘境"""
        if (self.completed or self.number in player.dungeons_cleared) and not self.can_replay_after_completion:
            return False, f"你已经通关了秘境 '{self.name}'，不能再次进入。"
        return True, "可以进入秘境。"

    def handle_loss(self, player) -> dict:
        """处理战败"""
        player.hp = 1
        exp_loss_percentage = random.uniform(0.01, 0.1)
        exp_loss = int(player.exp * exp_loss_percentage)
        player.exp = max(0, player.exp - exp_loss)
        return {
            "hp": player.hp,
            "exp_loss": exp_loss,
            "exp_loss_percentage": exp_loss_percentage
        }

    def remove_npc(self, npc_number: int) -> tuple[bool, str]:
        """从秘境中移除 NPC"""
        for floor in self.floors:
            if floor.npc and floor.npc.number == npc_number:
                message = floor.remove_npc()
                return True, message
        return False, f"未找到编号为 {npc_number} 的 NPC 在秘境 {self.name} 中。"

    def reset_progress(self):
        """重置秘境进度"""
        self.highest_floor = 0
        self.completed = False
        for floor in self.floors:
            floor.completed = False

    def update_progress(self, player, floor_number: int):
        """更新秘境和玩家进度"""
        self.highest_floor = max(self.highest_floor, floor_number)
        player.update_highest_floor(self.number, floor_number)
        if self.highest_floor == len(self.floors):
            self.completed = True
            player.mark_dungeon_cleared(self.number)
            