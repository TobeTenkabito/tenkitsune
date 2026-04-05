from common.module.cultivation import CultivationSystem
from common.character.player import Player
from library.skill_library import skill_library
from common.interface.cultivation_interface import CultivationInterface

player = Player(number=1,name="测试玩家")
player.add_to_inventory(skill_library[242001])
player.add_to_inventory(skill_library[241001])
cultivation_system = CultivationSystem(player, skill_library)
cultivation_interface = CultivationInterface(cultivation_system)

cultivation_interface.show_cultivation_interface()