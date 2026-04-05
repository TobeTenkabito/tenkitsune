from library.npc_library import npc_library
from common.character.player import Player
from library.material_library import material_library


def main():
    # 创建玩家
    player = Player(number=1, name="测试玩家")

    # 与村长老张互动
    npc = npc_library[101]
    npc.interact(player)

    # 给村长老张赠送铜板
    print("\n赠送物品给村长老张:")
    npc.receive_gift(material_library[100000])

    # 检查 NPC 状态
    print("\n当前 NPC 状态:")
    print(npc)

    # 与神秘商人互动
    npc = npc_library[102]
    npc.interact(player)

    # 给神秘商人赠送银币
    print("\n赠送物品给神秘商人:")
    npc.receive_gift(material_library[100001])

    # 检查 NPC 状态
    print("\n当前 NPC 状态:")
    print(npc)

if __name__ == "__main__":
    main()