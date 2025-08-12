class LotteryInterface:
    def __init__(self, player):
        self.player = player

    def show_lottery_interface(self, lottery_pool):
        while True:
            print("欢迎来到抽奖系统！请选择抽奖类型:")
            print("1. 单次抽奖")
            print("2. 十连抽奖")
            print("3. 百连抽奖")
            print("0. 退出抽奖")
            choice = input("请输入选项编号: ")

            if choice == '1':
                self.perform_lottery(lottery_pool, 1)
            elif choice == '2':
                self.perform_lottery(lottery_pool, 10)
            elif choice == '3':
                self.perform_lottery(lottery_pool, 100)
            elif choice == '0':
                print("退出抽奖系统。")
                break
            else:
                print("无效的选择，请重试。")

    def perform_lottery(self, lottery_pool, draw_count):
        """执行指定数量的抽奖"""
        if draw_count == 1:
            quantity_to_use = 1
        elif draw_count == 10:
            quantity_to_use = 10
        elif draw_count == 100:
            quantity_to_use = 100
        else:
            print("无效的抽奖数量。")
            return

        if not self.player.decrease_material_quantity(120000, quantity_to_use):
            print("抽奖材料不足，无法进行抽奖。")
            return

        print(f"消耗了 {quantity_to_use} 个 北斗白石。")

        lottery = lottery_pool

        results = lottery.draw(draw_count)
        for reward, probability in results:
            # 如果 reward 是一个有效的物品
            if reward:
                quantity = 1
                if probability == 0.03:
                    quantity = 1  # 第一档奖励数量
                elif probability == 0.17:
                    quantity = 1  # 第二档奖励数量
                elif probability == 0.2:
                    quantity = 1  # 第三档奖励数量
                elif probability == 0.3:
                    quantity = 1  # 第四档奖励数量
                elif probability == 0.3:
                    quantity = 1  # 第五档奖励数量

                quantity = int(quantity)  # 确保是整数
                for _ in range(quantity):
                    print(f"即将添加到背包的材料: {reward.name}, 数量: 1")
                    self.player.add_to_inventory(reward)
