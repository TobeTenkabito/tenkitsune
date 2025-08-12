from common.module.market import Market


def show_market_interface(player):
    market = Market()

    while True:
        print("\n市场物品列表:")
        market.display_items()  # 现在会显示物品的编号
        print("\n请选择操作:")
        print("1. 出售物品")
        print("2. 购买物品")
        print("3. 刷新市场")
        print("0. 退出市场")
        choice = input("请输入选项编号: ")

        if choice == '1':
            item_number = int(input("请输入要出售的物品编号: "))
            quantity = int(input("请输入要出售的数量: "))
            item = player.get_inventory_item(item_number)
            if item:
                success, message = market.sell_item(player, item, quantity)
                print(message)
            else:
                print("背包中没有该物品。")
        elif choice == '2':
            item_index = int(input("请输入要购买的物品编号: "))  # 现在输入物品的编号
            quantity = int(input("请输入要购买的数量: "))
            item = market.get_market_item(item_index)  # 根据编号获取物品
            if item:
                success, message = market.buy_item(player, item, quantity)
                print(message)
            else:
                print("市场中没有该物品。")
        elif choice == '3':
            market.items_for_sale = market.refresh_market()
            print("市场已刷新。")
        elif choice == '0':
            break
        else:
            print("无效的选择。请重试。")
