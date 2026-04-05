from all.gamestate import game_state
from library.map_library import map_library
from library.material_library import material_library
from library.warp_library import warp_library
# 假设已经定义了 map_library，并且地图对象已经初始化和添加到 game_state 中

# 初始化全局游戏状态管理器
game_state.initialize_player(1, "测试玩家")
player = game_state.get_player()
# 添加地图到游戏状态管理器
for map_number, map_obj in map_library.items():
    game_state.add_map(map_number, map_obj)
# 测试玩家是否能够正确在地图之间移动
print("\n--- 测试开始 ---\n")

player.add_to_inventory(material_library[160001])
player.add_to_inventory(material_library[150000])
player.add_to_inventory(warp_library[170000])
# 玩家开始探索初始地图 (仙狐村)
game_state.get_map(game_state.get_player().map_location).explore()
game_state.player.use_item(170000)
print("\n--- 测试结束 ---\n")