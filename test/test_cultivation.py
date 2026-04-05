from common.character.player import Player
from common.module.cultivation import CultivationSystem
from library.skill_library import skill_library
player = Player(1, "Test Player")

# 创建修为系统
cultivation_system = CultivationSystem(player, skill_library)

# 测试1：模拟提升修为并解锁心法
print("\n--- 提升修为并解锁心法 ---")
cultivation_system.used_points = 15  # 模拟已经使用了15个培养点
cultivation_system.check_xinfa_unlock()  # 期望解锁心法等级1和2

# 检查玩家背包和技能栏
print("\n--- 玩家背包 ---")
for item in player.inventory:
    print(f"{item.name}: {item.description}")

print("\n--- 玩家技能栏 ---")
for skill in player.skills:
    print(f"{skill.name}: {skill.description}")

# 测试2：重置修为并检查心法和技能移除
print("\n--- 重置修为和心法 ---")
cultivation_system.reset()  # 重置修为，期望移除已解锁的技能

# 再次检查玩家背包和技能栏，确保技能已移除
print("\n--- 重置后玩家背包 ---")
for item in player.inventory:
    print(f"{item.name}: {item.description}")

print("\n--- 重置后玩家技能栏 ---")
for skill in player.skills:
    print(f"{skill.name}: {skill.description}")
