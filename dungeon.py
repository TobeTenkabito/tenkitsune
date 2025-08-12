from .battle import Battle
from copy import deepcopy
from all.gamestate import game_state
from unittest.mock import patch
import random


class DungeonFloor:
    def __init__(self, number, description, enemies=None, npc=None, entry_buff=None,
                 rewards=None, first_time_rewards=None, random_rewards=None, restrictions=None,):
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

    def enter(self, player, is_first_time=False):
        print(f"你进入了秘境的第 {self.number} 层: {self.description}")

        if self.npc is not None and self.npc.number in player.npcs_removed:
            print(f"1")
            self.npc = None

        if self.npc:
            print(f"2")
            self.npc.interact(player)

        if self.entry_buff:
            if isinstance(self.entry_buff, list):
                for buff in self.entry_buff:
                    print(f"玩家获得了 {buff.name} buff.")
                    player.add_buff(deepcopy(buff))
            else:
                print(f"玩家获得了 {self.entry_buff.name} buff.")
                player.add_buff(deepcopy(self.entry_buff))

        # 战斗
        if self.enemies:
            print(f"开始战斗，敌人: {[enemy.name for enemy in self.enemies]}")
            battle = Battle(player, [], self.enemies)
            battle.run_battle()

            battle_status = battle.check_battle_status()
            print(f"战斗结果: {battle_status}")

            if battle.check_battle_status() == "win":
                self.completed = True
                self.give_rewards(player, is_first_time)
                return True
            else:
                print("玩家未能通过这一层。")
                return False
        else:
            self.completed = True
            self.give_rewards(player, is_first_time)
            return True

    def give_rewards(self, player, is_first_time):
        print(f"开始发放奖励: 首通状态: {is_first_time}")
        # 首通奖励
        if is_first_time and self.first_time_rewards:
            for reward in self.first_time_rewards:
                self._apply_reward(player, reward)
                print(f"玩家获得了首通奖励: {reward['item'].name} x {reward['quantity']}")

        # 固定奖励
        if self.rewards:
            for reward in self.rewards:
                self._apply_reward(player, reward)
                print(f"玩家获得了固定奖励: {reward['item'].name} x {reward['quantity']}")

        # 随机奖励
        if self.random_rewards:
            for reward in self.random_rewards:
                if random.random() <= reward.get("chance", 1.0):  # 默认概率为 100%
                    self._apply_reward(player, reward)
                    print(f"玩家获得了随机奖励: {reward['item'].name} x {reward['quantity']}")
                else:
                    print(f"未能获得随机奖励: {reward['item'].name}")

    def _apply_reward(self, player, reward):
        if reward["type"] == "item":
            reward_item = deepcopy(reward["item"])
            reward_item.quantity = reward["quantity"]
            player.add_to_inventory(reward_item)
            print(f"玩家获得了 {reward_item.name} x {reward_item.quantity}")
        elif reward["type"] == "exp":
            player.gain_exp(reward["amount"])
            print(f"玩家获得了 {reward['amount']} 点经验值。")
        elif reward["type"] == "attribute":
            attr = reward["attribute"]
            value = reward["value"]
            player.gain_dungeon_attribute(attr, value)

    def remove_npc_dungeon_floor(self):
        if self.npc:
            print(f"NPC {self.npc.name} 已从秘境的第 {self.number} 层移除。")
            self.npc = None  # 清空该层的 NPC
        else:
            print(f"该楼层 {self.number} 没有 NPC 需要移除。")


class Dungeon:
    def __init__(self, name, number, description, floors, can_replay_after_completion=True, npc_affection_impact=None):
        self.name = name
        self.number = number
        self.description = description
        self.floors = floors  # 存储 DungeonFloor 对象的列表
        self.highest_floor = 0  # 玩家通过的最高层数
        self.completed = False  # 是否通关
        self.player_restrictions = {}
        self.can_replay_after_completion = can_replay_after_completion  # 是否可以重复通关
        self.npc_affection_impact = npc_affection_impact if npc_affection_impact else {}

    def enter_dungeon(self, player):
        if (self.completed or self.number in player.dungeons_cleared) and not self.can_replay_after_completion:
            print(f"你已经通关了秘境 '{self.name}'，不能再次进入。")
            return

        self.apply_npc_affection_impact(player)

        print(f"玩家进入了秘境: {self.name} - {self.description}")

        for floor in self.floors:
            print(f"进入 {floor.description}")
            # 移除已标记为移除的 NPC
            if floor.npc is not None and floor.npc.number in player.npcs_removed:
                print(f"NPC {floor.npc.name} 已被你杀死，不再出现在本秘境楼层 {floor.number}。")
                floor.npc = None  # 移除 NPC

            # 检查是否是第一次通过这一层（只给首通奖励）
            is_first_time = player.highest_floor.get(self.number, 0) < floor.number
            print(f"当前层是否是首次通关: {is_first_time}, 玩家最高层数: {player.highest_floor.get(self.number, 0)}")

            # 进入当前层，处理层逻辑
            floor_success = floor.enter(player, is_first_time)

            # 战败处理
            if not floor_success:
                self.handle_loss_explore(player)
                break

            # 如果战斗胜利，更新玩家通过的最高层
            print(f"战斗胜利！更新最高层数: {floor.number}")
            self.highest_floor = max(self.highest_floor, floor.number)
            player.update_highest_floor(self.number, floor.number)

        if self.highest_floor == len(self.floors):
            self.completed = True
            player.mark_dungeon_cleared(self.number)
            print(f"\n恭喜！玩家已经通关秘境 {self.name}！")
        else:
            print(f"你未能通关秘境 '{self.name}'，当前最高层: {self.highest_floor}请再接再厉！")

        player.display_inventory()

    def apply_npc_affection_impact(self, player):
        from library.npc_library import npc_library
        for npc_id, affection_change in self.npc_affection_impact.items():
            npc = npc_library.get(npc_id)
            if npc:
                npc.affection += affection_change
                print(f"进入秘境 '{self.name}' 使 {npc.name} 对你的好感度发生了变化: {affection_change} 点。")

    def handle_loss_explore(self, player):
        print("你实力不佳，迷失在了秘境中。")
        player.hp = 1
        print(f"{player.name} 出了秘境后不断休息，生命值已恢复至 1。")
        exp_loss_percentage = random.uniform(0.01, 0.1)
        exp_loss = int(player.exp * exp_loss_percentage)
        player.exp = max(0, player.exp - exp_loss)
        print(f"因为战败，沾染了因果，心魔悄然积累。{player.name} 损失了 {exp_loss} 点经验 ({int(exp_loss_percentage * 100)}%)。")
        print("等你醒来时，不知为何已经在秘境之外。在此地休整了一下，你决定继续出发。")
        current_map = game_state.get_map(player.map_location)
        if current_map:
            # 避免阻塞ui
            try:
                with patch('builtins.input', return_value="0"):
                    current_map.explore_dungeon()
            except Exception as e:
                print(f"再次探索秘境时发生错误: {e}")
        else:
            print("无法获取当前地图。")
        return f"等你醒来时，不知为何已经在秘境之外。在此地休整了一下，你决定继续出发。"

    def check_completion(self):
        return self.completed

    def finish(self, player):
        self.completed = True
        player.dungeon_clears[self.number] = self.completed
        player.mark_dungeon_cleared(self.number)
        player.display_inventory()
        player.update_stats()
        if self.number not in player.dungeons_cleared:
            player.dungeons_cleared.add(self.number)

    # 移除秘境npc
    def remove_npc_from_dungeon(self, npc_number):
        for floor in self.floors:
            if floor.npc and floor.npc.number == npc_number:
                floor.remove_npc_dungeon_floor()  # 调用楼层的 NPC 移除方法
                print(f"NPC {npc_number} 已从秘境 {self.name} 中的第 {floor.number} 层移除。")
                return True
        print(f"未找到编号为 {npc_number} 的 NPC 在秘境 {self.name} 中。")
        return False

    def add_restrictions(self, restrictions):
        self.player_restrictions = restrictions

    def reset_progress(self):
        self.highest_floor = 0
        self.completed = False
        for floor in self.floors:
            floor.completed = False

    def run_dungeon(self, player):
        dungeon_id = self.number
        print(f"玩家进入了秘境: {self.name}")
        for floor in self.floors:
            print(f"进入 {floor.description}")

            is_first_time = player.highest_floor.get(dungeon_id, 0) < floor.number

            if floor.npc:
                floor.npc.interact(player)

            if floor.entry_buff:
                for buff in floor.entry_buff:
                    player.add_buff(buff)

            if floor.enemies:
                battle = Battle(player, [], floor.enemies)
                battle.run_battle()
                results = battle.check_battle_status()

                if results == "win":
                    floor.give_rewards(player, is_first_time)
                    player.update_highest_floor(dungeon_id, floor.number)
                elif results == "loss":
                    self.handle_loss_explore(player)

            else:
                floor.give_rewards(player, is_first_time)
                player.update_highest_floor(dungeon_id, floor.number)

        # 检查是否通关
        if player.highest_floor[dungeon_id] == len(self.floors):
            player.mark_dungeon_cleared(dungeon_id)
            print(f"\n恭喜！玩家已经通关秘境 {self.name}！")
        player.display_inventory()
