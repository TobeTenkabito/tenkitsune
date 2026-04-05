from library.npc_library import npc_library
from common.character.player import Player
from library.material_library import material_library

def main():
    # 创建玩家
    player = Player(number=1, name="测试玩家")

    # 与村长老张互动
    npc = npc_library[101]
    print(f"\n与 {npc.name} 互动前的状态: 好感度 {npc.affection}")
    npc.interact(player)

    # 赠送物品给村长老张并查看好感度变化
    print("\n赠送物品给村长老张:")
    npc.receive_gift(material_library[100000])
    print(f"\n与 {npc.name} 互动后的状态: 好感度 {npc.affection}")
    npc.interact(player)

    # 将村长老张的好感度降低到负数
    npc.affection = -30
    print(f"\n将 {npc.name} 的好感度降低到负数 (-30)")
    npc.interact(player)

if __name__ == "__main__":
    main()