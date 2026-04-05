from common.character.player import Player
from library.task_library import task_library


def main():
    # 创建玩家
    player = Player(number=1, name="测试玩家")

    # 打印玩家状态
    print(f"\n任务完成前玩家状态:\n{player}")

    # 接取任务1
    task = task_library[1]
    task.accept(player)

    # 模拟完成任务1
    player.tutorial_complete = True
    task.complete(player)

    # 打印玩家状态
    print(f"\n任务完成后玩家状态:\n{player}")

    # 尝试接取任务2
    task2 = task_library[2]
    task2.accept(player)

    # 模拟完成任务2
    task2.complete(player)

    # 打印玩家状态
    print(f"\n任务完成后玩家状态:\n{player}")

    # 接取任务1
    task3 = task_library[3]
    task3.accept(player)
    task3.complete(player)

    # 检查背包中的物品
    print("\n背包中的物品:")
    player.display_inventory()


if __name__ == "__main__":
    main()