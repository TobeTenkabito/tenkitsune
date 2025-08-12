import threading
from unittest.mock import patch


class GameState:
    def __init__(self):
        self.player = None
        self.maps = {}
        self.npcs = {}
        self.dungeons = {}  # 管理所有秘境

    def initialize_player(self, player_number, player_name):
        try:
            from common.character.player import Player
            self.player = Player(player_number, player_name)
            self.player.map_location = 1
            print(f"Player initialized: {self.player.name}, Location: {self.player.map_location}")
        except ImportError as e:
            print(f"Error importing Player class: {e}")
        except Exception as e:
            print(f"Error initializing player: {e}")

    def get_player(self):
        if self.player is None:
            print("Error: Player object not found in GameState.")
        else:
            print(f"Player retrieved from GameState: {self.player}")
        return self.player

    def set_player(self, player):
        self.player = player
        print(f"Player set in GameState: {self.player}")

    # 地图管理
    def add_map(self, map_number, map_obj):
        self.maps[map_number] = map_obj

    def get_map(self, map_number):
        map_obj = self.maps.get(map_number)
        if map_obj:
            print(f"地图 {map_number} 已找到: {map_obj.name}")
        else:
            print(f"地图 {map_number} 未找到。")
        return map_obj

    def move_player_to_map(self, map_number):
        """地图移动逻辑，使用多线程以避免阻塞界面"""
        player = self.get_player()
        if not player:
            print("错误：未找到玩家对象。")
            return

        current_map = self.get_map(player.map_location)
        if current_map:
            print(f"玩家从 {current_map.name} 离开。")

        new_map = self.get_map(map_number)
        if new_map:
            if new_map.can_enter(player):
                print(f"玩家移动到 {new_map.name}。")
                player.map_location = map_number

                # 启动新线程运行地图探索功能，避免阻塞
                threading.Thread(target=self._explore_map, args=(new_map,)).start()
            else:
                print(f"玩家未能进入 {new_map.name}，依然留在 {current_map.name}。")
        else:
            print(f"地图编号 {map_number} 不存在。")

    def _explore_map(self, new_map):
        try:
            with patch('builtins.input', return_value="7"):
                new_map.explore()
        except Exception as e:
            print(f"探索地图时发生错误: {e}")

    def get_adjacent_maps(self):
        player = self.get_player()
        if not player:
            print("错误：未找到玩家对象。")
            return []

        current_map = self.get_map(player.map_location)
        if current_map:
            return current_map.adjacent_maps
        else:
            print("玩家当前地图不存在。")
            return []

    def show_adjacent_maps(self):
        adjacent_maps = self.get_adjacent_maps()
        if not adjacent_maps:
            print("此地图没有可去的相邻地图。")
            return

        print("你可以离开此地去以下地点:")
        for map_number, details in adjacent_maps.items():
            adjacent_map = self.get_map(map_number)
            print(f"{map_number}. {adjacent_map.name}，距离: {details['distance']}")
        print("0. 返回上一级")

        choice = input("请选择要前往的地图编号: ")
        if choice == '0':
            return

        try:
            map_number = int(choice)
            if map_number in adjacent_maps:
                self.move_player_to_map(map_number)
            else:
                print("无效的选择，请重试。")
        except ValueError:
            print("无效的输入，请输入数字。")

    # NPC管理
    def add_npc(self, npc_number, npc_obj):
        self.npcs[npc_number] = npc_obj

    def get_npc(self, npc_number):
        npc = self.npcs.get(npc_number)
        if npc:
            print(f"NPC retrieved: {npc.name}")
        else:
            print(f"NPC with number {npc_number} not found.")
        return npc

    def remove_npc(self, npc_number):
        print(f"当前游戏中的NPC编号列表: {list(self.npcs.keys())}")
        if npc_number in self.npcs:
            removed_npc = self.npcs.pop(npc_number)
            print(f"{removed_npc.name} 已从游戏中移除。")
            # 遍历所有地图，确保该 NPC 从地图中被移除
            for map_obj in self.maps.values():
                map_obj.remove_npc_from_map(npc_number)
            else:
                print(f"{npc_number} 该npc不存在于其它地图")
            # 遍历所有秘境楼层，检查并移除对应的 NPC
            npc_removed_from_dungeon = False
            for dungeon in self.dungeons.values():
                for floor in dungeon.floors:
                    # 检查 NPC 是否存在，避免对 None 进行操作
                    if floor.npc is not None and floor.npc.number == npc_number:
                        print(f"正在移除秘境 {dungeon.name} 第 {floor.number} 层的 NPC: {floor.npc.name}")
                        floor.npc = None  # 将楼层中的 NPC 设置为 None，表示移除
                        npc_removed_from_dungeon = True
        else:
            print(f"未找到编号为 {npc_number} 的 NPC。")


game_state = GameState()
