from common.character.player import Player
from library.material_library import material_library
from common.interface.synthesis_interface import show_synthesis_interface

def main():
    player = Player(number=1, name="玩家")

    # 添加初始材料到玩家背包
    player.add_to_inventory(material_library[100006])
    player.add_to_inventory(material_library[100007])
    player.add_to_inventory(material_library[100008])
    player.add_to_inventory(material_library[100004])
    player.add_to_inventory(material_library[100004])
    player.add_to_inventory(material_library[100009])
    player.add_to_inventory(material_library[100009])
    player.add_to_inventory(material_library[100009])
    player.add_to_inventory(material_library[100029])
    player.add_to_inventory(material_library[100029])
    player.add_to_inventory(material_library[100029])
    player.add_to_inventory(material_library[100029])
    player.add_to_inventory(material_library[100029])
    player.add_to_inventory(material_library[100001])
    player.add_to_inventory(material_library[100001])
    player.add_to_inventory(material_library[100001])
    player.add_to_inventory(material_library[100001])
    player.add_to_inventory(material_library[100001])
    player.add_to_inventory(material_library[100016])
    # 进入合成界面
    show_synthesis_interface(player)

    # 打印玩家背包内容
    for item in player.inventory:
        print(f"{item.name} x {item.quantity}")

if __name__ == "__main__":
    main()