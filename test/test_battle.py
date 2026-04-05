from common.character.player import Player
from library.enemy_library import enemy_library
from library.equipment_library import equipment_library
from library.skill_library import skill_library
from common.module.battle import Battle
from library.boss_library import boss_library
from library.ally_library import ally_library
from library.medicine_library import medicine_library
from library.product_library import product_library


def main():
    player = Player(number=1, name="玩家")
    player.add_to_inventory(medicine_library[300007])
    player.add_to_equipment(equipment_library[400002])
    player.add_to_skill(skill_library[251001])
    player.add_to_skill(skill_library[200001])
    player.add_to_skill(skill_library[200004])
    player.add_to_skill(skill_library[251002])
    player.add_to_skill(skill_library[251003])
    player.add_to_skill(skill_library[251004])
    player.add_to_skill(skill_library[251005])
    player.add_to_skill(skill_library[220019])
    player.add_to_skill(skill_library[254005])
    player.add_to_equipment(equipment_library[430004])
    player.add_to_equipment(equipment_library[430014])
    player.add_to_equipment(equipment_library[430012])
    player.add_to_inventory(medicine_library[300001])
    player.add_to_inventory(medicine_library[300002])
    player.add_to_inventory(medicine_library[300002])
    player.add_to_inventory(medicine_library[300003])
    player.add_to_inventory(medicine_library[300003])
    player.add_to_inventory(medicine_library[300007])
    player.add_to_inventory(medicine_library[300007])
    player.add_to_inventory(product_library[310000])
    player.add_to_inventory(product_library[310000])
    player.add_to_inventory(product_library[310000])
    player.add_to_inventory(product_library[310001])
    player.add_to_inventory(product_library[310002])

    battle1 = Battle(player, [ally_library[700001]], [boss_library[600001]])
    battle1.run_battle()
    battle2 = Battle(player, [ally_library[700001]], [boss_library[600001]])
    battle2.run_battle()
    print(player)

if __name__ == "__main__":
    main()
