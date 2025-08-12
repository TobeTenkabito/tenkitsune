from all.gamestate import game_state


class TaskInterface:
    def __init__(self, player):
        self.player = player

    def task_system_menu(self):
        while True:
            print("\n=== 任务系统 ===")
            print("1. 查看当前任务")
            print("2. 查看已完成任务")
            print("3. 接取新任务")
            print("4. 返回主界面")
            choice = input("请选择操作: ")

            if choice == "1":
                self.display_current_tasks()  # 从 player 读取任务
            elif choice == "2":
                self.display_completed_tasks()  # 从 player 读取已完成任务
            elif choice == "3":
                # 显示可接取的任务（与 NPC 交互的逻辑）
                self.accept_new_task()
            elif choice == "4":
                break
            else:
                print("无效选择，请重新输入。")

    def display_current_tasks(self):
        if self.player.accepted_tasks:
            print("\n=== 当前任务列表 ===")
            for i, task in enumerate(self.player.accepted_tasks, 1):
                print(f"{i}. {task.name} - {task.description}")
        else:
            print("\n你当前没有正在进行的任务。")

    def display_completed_tasks(self):
        if self.player.completed_tasks:
            print("\n=== 已完成任务列表 ===")
            for i, task_number in enumerate(self.player.completed_tasks, 1):
                print(f"{i}. 任务 {task_number}")
        else:
            print("\n你还没有完成任何任务。")

    def accept_new_task(self):
        print("\n=== 可接取任务列表 ===")
        available_tasks = [task for task in game_state.tasks if task.can_accept(self.player)]
        if not available_tasks:
            print("当前没有可以接取的任务。")
            return

        for idx, task in enumerate(available_tasks, 1):
            print(f"{idx}. {task.name}: {task.description}")
        choice = input("请选择任务编号进行接取: ")

        if choice.isdigit():
            task_index = int(choice) - 1
            if 0 <= task_index < len(available_tasks):
                task = available_tasks[task_index]
                task.accept(self.player)  # 接受任务，添加到玩家的任务列表
                game_state.add_task_to_player(task.number)  # 更新全局任务状态
            else:
                print("无效的任务编号。")
        else:
            print("无效的输入，请重试。")
