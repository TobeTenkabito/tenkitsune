def test_lottery_interface():
    from common.character.player import Player
    from library.lottery_library import lottery_library
    from common.interface.lottery_interface import LotteryInterface
    from library.material_library import material_library

    # 创建测试玩家，并给予抽奖材料
    player = Player(1, "测试玩家")
    for _ in range(200):  # 提供200个材料供抽奖测试
        player.add_to_inventory(material_library[120000])

    # 创建抽奖界面
    lottery_interface = LotteryInterface(player)

    # 打印初始玩家背包信息
    print("玩家初始背包:")
    player.display_inventory()

    # 执行抽奖界面
    lottery_interface.show_lottery_interface(lottery_library[1])

    # 打印抽奖后玩家背包信息
    print("抽奖后玩家背包:")
    player.display_inventory()


if __name__ == "__main__":
    test_lottery_interface()