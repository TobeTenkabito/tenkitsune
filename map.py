import random
import copy
from all.gamestate import game_state
from unittest.mock import patch


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
        self.adjacent_maps[map_number] = {"distance": distance, "direction": direction}
        if direction == "双向" and map_factory:
            adjacent_map = map_factory(map_number)
            adjacent_map.adjacent_maps[self.number] = {"distance": distance, "direction": direction}

    def can_enter(self, player):
        # 没有通行证限制，允许进入
        if self.passport is None:
            print(f"{self.passtext}")
            return True

        # 处理布尔逻辑通行证 (AND/OR)
        elif isinstance(self.passport, dict):
            if "AND" in self.passport:
                if not all(player.has_item(item) for item in self.passport["AND"]):
                    print(f"{self.unpasstext}")
                    return False
            elif "OR" in self.passport:
                if not any(player.has_item(item) for item in self.passport["OR"]):
                    print(f"{self.unpasstext}")
                    return False

        # 处理单一通行证情况
        else:
            if not player.has_item(self.passport):
                print(f"{self.unpasstext}")
                return False

        print(f"{self.passtext}")
        return True

    def explore(self):
        player = game_state.get_player()
        if not player:
            print("错误：未找到玩家对象。")
            return

        if not self.can_enter(player):
            return

        print(f"你正在探索 {self.name}")
        print(self.description)
        self.show_npcs()
        self.show_battles()
        self.show_collectibles()

        while True:
            print("\n请选择你的行动：")
            print("1. 谈天说地")
            print("2. 采集材料")
            print("3. 清理野怪")
            print("4. 探索秘境")
            print("5. 离开此地")
            print("6. 返回上一级")

            choice = input("请输入选项编号: ")

            if choice == '1':
                self.interact_with_npc()
            elif choice == '2':
                self.collect_materials()
            elif choice == '3':
                self.clean_monsters()
            elif choice == '4':
                self.explore_dungeon()
            elif choice == '5':
                game_state.show_adjacent_maps()
            elif choice == '6':
                print("若想回到主界面请多次尝试")
                return
            elif choice == '7':
                break
            else:
                print("无效的选择，请重试。")

    def show_npcs(self):
        if self.npcs:
            print("此地图上的 NPC:")
            for npc in self.npcs:
                print(f"- {npc.name}: {npc.description}")
        else:
            print("此地图上没有 NPC。")

    def show_battles(self):
        if self.battles:
            print("此地图上的战斗场景:")
            for i, enemy_list in enumerate(self.battles):
                enemies = ', '.join([enemy.name for enemy in enemy_list])
                print(f"{i + 1}. 敌人: {enemies}")
        else:
            print("此地图上没有战斗场景。")

    def show_collectibles(self):
        if self.collectible_items:
            print("此地图上可采集的物品:")
            for item in self.collectible_items:
                print(f"- {item.name}")
        else:
            print("此地图上没有可采集的物品。")

    def interact_with_npc(self):
        player = game_state.get_player()
        if not player:
            print("错误：未找到玩家对象。")  # 调试输出
            return

        if not self.npcs:
            print("此地图上没有 NPC 供你互动。")
            return

        print("你可以与以下 NPC 互动:")
        for i, npc in enumerate(self.npcs):
            print(f"{i + 1}. {npc.name}")
        print("0. 返回上一级")

        choice = input("请选择 NPC 编号: ")
        if choice == '0':
            return

        try:
            npc_index = int(choice) - 1
            if 0 <= npc_index < len(self.npcs):
                self.npcs[npc_index].interact(player)
            else:
                print("无效的选择，请重试。")
        except ValueError:
            print("无效的输入，请输入数字。")

    def collect_materials(self):
        """采集地图上的物品"""
        player = game_state.get_player()  # 确保通过 game_state 获取 player 对象
        if not player:
            print("错误：未找到玩家对象。")
            return

        if not self.collectible_items:
            print("此地图上没有可采集的物品。")
            return

        while True:
            print("\n你可以采集以下物品：")
            for i, item in enumerate(self.collectible_items.keys(), 1):
                print(f"{i}. {item.name}")
            print("0. 返回上一级")

            choice = input("请输入你想采集的物品编号: ")

            if choice == '0':
                print("你决定暂时不进行采集。")
                break

            try:
                choice = int(choice) - 1
                if 0 <= choice < len(self.collectible_items):
                    selected_item = list(self.collectible_items.keys())[choice]
                    item_info = self.collectible_items[selected_item]
                    success_rate = item_info["success_rate"]
                    quantity_range = item_info["quantity_range"]

                    # 根据成功率和数量范围采集物品
                    if random.uniform(0, 1) <= success_rate:
                        if isinstance(quantity_range, tuple):
                            quantity = random.randint(quantity_range[0], quantity_range[1])
                        else:
                            quantity = quantity_range
                            collect_item = copy.deepcopy(selected_item)
                            collect_item.quantity = quantity
                            player.add_to_inventory(collect_item)
                        print(f"成功采集到 {selected_item.name} x {quantity}！")
                    else:
                        print(f"采集 {selected_item.name} 失败。")
                else:
                    print("无效的选择，请重试。")
            except ValueError:
                print("无效的输入，请输入数字。")

    def clean_monsters(self):
        player = game_state.get_player()  # 获取当前玩家对象
        if not player:
            print("错误：未找到玩家对象。")
            return

        if not self.battles:
            print("此地图上没有野怪。")
            return

        print("你可以挑战以下战斗场景:")
        for i, enemy_list in enumerate(self.battles):
            # 展示敌人列表
            enemies = ', '.join([enemy.name for enemy in enemy_list])
            print(f"{i + 1}. 敌人: {enemies}")
        print("0. 返回上一级")

        choice = input("请选择战斗场景编号: ")
        if choice == '0':
            return

        try:
            battle_index = int(choice) - 1
            if 0 <= battle_index < len(self.battles):
                from .battle import Battle
                battle = Battle(player, [], self.battles[battle_index])
                result = battle.run_battle()  # 运行战斗并获取结果

                # 根据战斗结果处理
                if result == "loss":
                    self.handle_monster_defeat(player)  # 战斗失败处理
                elif result == "win":
                    print(f"{player.name} 战胜了敌人！")
                else:
                    print("战斗结束，未定义的结果。")

            else:
                print("无效的选择，请重试。")
        except ValueError:
            print("无效的输入，请输入数字。")

    def handle_monster_defeat(self, player):
        print("你被野怪击晕了。")
        player.hp = 1
        print(f"{player.name} 的生命值已恢复至 1。")
        exp_loss_percentage = random.uniform(0.01, 0.1)
        exp_loss = int(player.exp * exp_loss_percentage)
        player.exp = max(0, player.exp - exp_loss)  # 确保经验值不会低于 0
        print(f"因为战败，沾染了因果，心魔悄然积累。{player.name} 损失了 {exp_loss} 点经验 ({int(exp_loss_percentage * 100)}%)。")
        print("你被野怪打晕在此。在此地休整了一下，你决定继续出发。")
        # 防止ui阻塞
        try:
            with patch('builtins.input', return_value="7"):
                self.explore()
        except Exception as e:
            print(f"探索地图时发生错误: {e}")
        return f"你被野怪击晕了,在此地休整了一会，你的生命值已经恢复至1，沾染了因果，心魔悄然积累。{player.name}损失了{exp_loss}点经验。"

    def explore_dungeon(self):
        player = game_state.get_player()
        if not player:
            print("错误：未找到玩家对象。")
            return

        if not self.dungeons:
            print("此地图上没有秘境可以探索。")
            return

        print("你可以探索以下秘境:")
        for i, dungeon in enumerate(self.dungeons):
            print(f"{i + 1}. {dungeon.name}: {dungeon.description}")
        print("0. 返回上一级")

        choice = input("请选择秘境编号: ")
        if choice == '0':
            return

        try:
            dungeon_index = int(choice) - 1
            if 0 <= dungeon_index < len(self.dungeons):
                dungeon = self.dungeons[dungeon_index]
                player = game_state.get_player()
                dungeon.enter_dungeon(player)
            else:
                print("无效的选择，请重试。")
        except ValueError:
            print("无效的输入，请输入数字。")

    # 移除npc的逻辑
    def remove_npc_from_map(self, npc_number):
        # 遍历地图的 NPC 列表，找到并删除相应的 NPC
        self.npcs = [npc for npc in self.npcs if npc.number != npc_number]
