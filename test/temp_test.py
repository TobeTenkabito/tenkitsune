from common.character.player import Player
from common.module.battle import Battle
from common.module.task import Task
from common.module.npc import NPC
from library.material_library import material_library
from library.enemy_library import enemy_library


def test_task_completion_by_killing_enemies():
    # 创建测试玩家
    player = Player(number=1, name="测试玩家")

    # 创建测试敌人（如哥布林）
    goblin_enemy = enemy_library[500001]  # 从敌人库中获取哥布林敌人

    # 创建一个需要击败2只哥布林才能完成的任务
    task_to_complete = Task(
        number=1,
        name="击败哥布林",
        description="玩家需要击败2只哥布林才能完成这个任务。",
        quality="普通",
        repeatable=False,
        acceptance_conditions=[{"level": 1}],
        completion_conditions=[{"kill": {"enemy_number": 500001, "count": 2}}],
        rewards=[
            {"type": "item", "item": material_library[100001], "quantity": 1},  # 假设有一个奖励物品
            {"type": "exp", "amount": 100}
        ]
    )

    # 将任务添加到NPC中，并将NPC加入到地图中
    npc_with_task = NPC(
        number=101,
        name="任务发布者",
        description="任务发布的NPC",
        race="人类",
        affection=50,
        favorite_items=[material_library[100001]],
        daily_dialogue="你好，勇士！",
        task_dialogue="你能帮我击败一些敌人吗？",
        finish_task_dialogue="太感谢你了，任务已经完成！",  # 新增任务完成后的对话
        tasks=[task_to_complete]
    )

    # 模拟玩家与NPC对话并接受任务
    npc_with_task.handle_task_dialogue(player)

    # 检查玩家是否成功接受了任务
    print(f"\n玩家接受的任务列表: {[task.name for task in player.accepted_tasks]}")

    # 创建战斗场景，包含需要击败的敌人
    battle = Battle(player=player, allies=[], enemies=[goblin_enemy, goblin_enemy])

    # 运行战斗模拟（假设玩家和队友能够击败敌人）
    battle.run_battle()

    # 检查任务完成情况
    for task in player.accepted_tasks:
        if task.check_completion(player):
            print(f"任务 '{task.name}' 已完成！")
            task.complete(player)
        else:
            print(f"任务 '{task.name}' 未完成。")

    # 打印玩家的任务状态和背包状态
    print(f"\n玩家已完成的任务列表: {player.completed_tasks}")
    print("玩家背包状态:")
    player.display_inventory()


if __name__ == "__main__":
    test_task_completion_by_killing_enemies()