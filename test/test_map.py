from common.module.npc import NPC
from common.module.battle import Battle
from common.module.map import Map
from library.dungeon_library import dungeon_library
from library.material_library import material_library
from library.enemy_library import enemy_library
from all.gamestate import game_state  # Ensure using the same global instance

# Debugging: Print game state instance to ensure it's consistent
print(f"GameState instance memory address: {id(game_state)}")

# Initialize global game state manager
print("Initializing player...")
game_state.initialize_player(1, "测试玩家")  # Ensure that initialize_player is called

# Verify player initialization
player = game_state.get_player()
if player is None:
    print("Player initialization failed. Exiting test script.")
    exit()  # Exit the script if the player is not initialized correctly

# Create example data
npc1 = NPC(101, "猎人", "一个经验丰富的猎人", "人类", 0, [], "你好，冒险者！", "你有兴趣接受任务吗？", "谢谢你完成了任务！")
battle1 = Battle(player, [], [enemy_library[500001]])  # Simplified battle example

# Initialize maps
map1 = Map(1, "起始村庄", "一个宁静的小村庄", {2: {"distance": 10, "direction": "双向"}}, [npc1], [battle1], [material_library[100054]], [dungeon_library[10001]])
map2 = Map(2, "黑暗森林", "一片危险的森林", {1: {"distance": 10, "direction": "双向"}}, [], [], [], [])

# Add to game state
game_state.add_map(1, map1)
game_state.add_map(2, map2)

# Start exploring the map
map1.explore()