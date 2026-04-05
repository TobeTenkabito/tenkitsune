import random
from all.gamestate import game_state


class NPC:
    def __init__(self, number, name, description, race, affection, favorite_items,
                 daily_dialogue, task_dialogue, finish_task_dialogue,
                 tasks=None, exchange=None, affection_dialogues=None, fight=None, taunt_dialogue=None, lottery=None):
        self.number = number
        self.name = name
        self.description = description
        self.race = race
        self.affection = affection
        self.favorite_items = favorite_items
        self.daily_dialogue = daily_dialogue if isinstance(daily_dialogue, list) else [daily_dialogue]
        self.task_dialogue = task_dialogue
        self.finish_task_dialogue = finish_task_dialogue
        self.fight = fight
        self.tasks = tasks or []
        self.exchange = exchange or {}
        self.lottery = lottery
        self.affection_dialogues = affection_dialogues or {
            "low": [],
            "medium": [],
            "high": []
        }
        self.taunt_dialogue = taunt_dialogue or {
            "low": [],
            "medium": [],
            "high": []
        }

    def interact(self, player):
        while True:
            print(f"\n你正在与 {self.name} 互动。")
            print("1. 日常对话")
            print("2. 接取任务")
            print("3. 任务对话")
            print("4. 交付任务")
            print("5. 赠送物品")
            print("6. 交易、学习、打造")
            print("7. 退出对话")
            choice = input("请输入选项编号: ")

            if choice == '1':
                self.handle_daily_dialogue(player)
            elif choice == '2':
                self.handle_task_dialogue(player)
            elif choice == '3':
                self.handle_finish_task_dialogue(player)
            elif choice == '4':
                self.handle_npc_task(player)
            elif choice == '5':
                self.give_gift(player)
            elif choice == '6':
                self.handle_exchange(player)  # 调用交易逻辑
            elif choice == '7':
                print(f"你结束了与 {self.name} 的对话。")
                break
            else:
                print("无效的选择，请重试。")

    def handle_exchange(self, player):
        if not self.exchange:
            print(f"{self.name} 当前没有可交易的物品。")
            return

        print(f"{self.name} 提供以下物品进行交易：")
        for i, (offered_item, details) in enumerate(self.exchange.items(), 1):
            required_item, required_quantity = details['item'], details['quantity']
            print(f"{i}. {offered_item.name} - 需要 {required_item.name} x{required_quantity}")

        choice = input("请输入你想交易的物品编号: ")

        if choice.isdigit():
            choice = int(choice) - 1
            if 0 <= choice < len(self.exchange):
                offered_item, details = list(self.exchange.items())[choice]
                required_item, required_quantity = details['item'], details['quantity']

                # 检查玩家是否有足够的交易物品
                if player.remove_from_inventory(required_item.number, required_quantity):
                    player.add_to_inventory(offered_item)  # 给玩家添加物品
                    print(f"你成功交易了 {required_quantity} 个 {required_item.name}，获得了 {offered_item.name}。")
                else:
                    print(f"你没有足够的 {required_item.name} 进行交易。")
            else:
                print("无效的选择，请重试。")
        else:
            print("无效的输入，请重试。")

    def handle_daily_dialogue(self, player):
        # 获取日常对话和好感度对话
        all_dialogues = self.daily_dialogue + self.get_affection_based_dialogue()

        # 从合并后的对话列表中随机选择一条
        dialogue = random.choice(all_dialogues)

        # 打印选择的对话
        print(f"{self.name}: {dialogue}")

        if self.affection >= -25:
            print("1. 继续对话")
            print("2. 其它事情")
            print("3. 结束对话")
            choice = input("请输入选项编号: ")
            if choice == '1':
                print(f"{self.name}: {random.choice(all_dialogues)}")
            elif choice == '2':
                self.invoke_function_module(player)
            elif choice == '3':
                print(f"你结束了与 {self.name} 的日常对话。")
            else:
                print("无效的选择，请重试。")

    def invoke_function_module(self, player):
        if self.affection < -25:
            print(f"{self.name} 对你已经失去了信任，无法调用任何功能模块。")
            return

        print("选择要调用的功能模块:")
        if self.affection >= 0:
            print("1. 市场")
        if self.affection >= 0:
            print("2. 战斗")
        if self.affection >= 0:
            print("3. 合成")
        print("4. 返回")
        choice = input("请输入选项编号: ")

        if choice == '1' and self.affection >= 0:
            self.call_market(player)
        elif choice == '2' and self.affection >= 0:
            self.call_battle(player)
        elif choice == '3' and self.affection >= 0:
            self.call_synthesis(player)
        elif choice == '4':
            print("返回上一级菜单。")
        else:
            print("无效的选择，请重试。")

    def handle_task_dialogue(self, player):
        if self.affection < -25:
            print(f"{self.name} 对你已经失去了信任，不愿意给你任何任务。")
            return

        print(f"{self.name}: {self.get_task_dialogue_based_on_affection()}")
        available_tasks = self.get_available_tasks_based_on_affection()

        if available_tasks:
            print("可接取任务:")
            for i, task in enumerate(available_tasks):
                print(f"{i + 1}. {task.name}")
            choice = int(input("请输入任务编号以接受任务: ")) - 1
            if 0 <= choice < len(available_tasks):
                task = available_tasks[choice]
                if task.can_accept(player):
                    task.accept(player)
                    print(f"任务 '{task.name}' 已接受。")
                else:
                    print(f"你未满足任务 '{task.name}' 的接受条件。")
            else:
                print("无效的选择，请重试。")
        else:
            print("此 NPC 没有可接取的任务。")

    def handle_finish_task_dialogue(self, player):
        # 记录玩家与该 NPC 的对话
        player.talk_to_npc(self.number)

        # 遍历玩家已接受的任务，检查是否有可以完成的任务
        completed_any_task = False
        for task in player.accepted_tasks:
            for condition in task.completion_conditions:
                if "talk_to_npc" in condition and condition["talk_to_npc"] == self.number:
                    if task.check_completion(player):
                        # 检查 finish_task_dialogue 是否是字典，处理不同类型的情况
                        if isinstance(self.finish_task_dialogue, dict):
                            dialogue = self.finish_task_dialogue.get(task.number, "感谢你完成任务！")
                        else:
                            dialogue = self.finish_task_dialogue  # 如果是字符串，直接使用

                        print(f"{self.name}: {dialogue}")
                        task.complete(player)
                        completed_any_task = True
                    else:
                        print(f"{self.name}: 你还没有完成任务 '{task.name}'。")
                    return  # 一旦找到任务相关的对话就结束对话

        if not completed_any_task:
            print(f"{self.name}: 你没有可以在这里完成的任务。")

    def handle_npc_task(self, player):
        # 检查玩家所有已完成但尚未交付的任务
        for task in player.ready_to_complete_tasks:
            # 直接比较 source_npc 编号和当前 NPC 的编号
            if task.source_npc == self.number:
                print(f"{self.name}: 你完成了任务 '{task.name}'！")
                task.give_rewards(player)  # 发放奖励
                player.completed_tasks.append(task.number)  # 标记任务完成
                player.ready_to_complete_tasks.remove(task)  # 从可交付任务中移除
                return

        print(f"{self.name}: 你没有可以交付的任务。")

    def give_gift(self, player):
        print(f"{self.name}: 你想赠送什么给我？")

        # 获取玩家的背包物品，并生成临时编号
        inventory_items = player.get_inventory()  # 调用新的 get_inventory 方法
        if not inventory_items:
            print("你没有可以赠送的物品。")
            return

        item_mapping = {}  # 用于临时存储编号与物品的映射
        for idx, item in enumerate(inventory_items, 1):  # 用1开始的编号
            print(f"{idx}. {item.name} (数量: {item.quantity})")
            item_mapping[idx] = item  # 将序号与物品关联起来

        choice = input("请输入物品编号: ")

        if choice.isdigit():
            item_idx = int(choice)
            if item_idx in item_mapping:
                item = item_mapping[item_idx]

                # 输入赠送数量
                quantity = input(f"你有 {item.quantity} 个 {item.name}，请输入你想赠送的数量: ")
                if quantity.isdigit():
                    quantity = int(quantity)

                    # 检查是否有足够的数量
                    if quantity > item.quantity:
                        print(f"你没有足够的 {item.name}，无法赠送 {quantity} 个。")
                        return

                    # 通过循环逐个赠送物品
                    for _ in range(quantity):
                        self.receive_gift(item)  # NPC 接受物品并影响好感度
                        player.remove_from_inventory(item.number, 1)  # 每次移除一个物品

                    # 记录赠送的物品数量
                    player.give_item_to_npc(self.number, item.number, quantity)

                    # 检查是否有任务涉及此物品赠送
                    for task in player.accepted_tasks:
                        if task.check_completion(player):
                            print(f"任务 '{task.name}' 已完成！")
                        else:
                            print(f"任务 '{task.name}' 尚未完成。")
                else:
                    print("无效的数量输入，请重试。")
            else:
                print("无效的物品编号，请重试。")
        else:
            print("无效的输入，请重试。")

    def get_affection_based_dialogue(self):
        """根据好感度返回不同的对话文本列表"""
        if self.affection < -25:
            return self.affection_dialogues.get("low", ["你这个家伙，别再来烦我了！"])
        elif -25 <= self.affection <= 25:
            return self.affection_dialogues.get("medium", ["哦，你来了，最近过得好吗？"])
        elif self.affection > 25:
            return self.affection_dialogues.get("high", ["嘿，老朋友！我一直在等你呢，有什么需要我帮忙的？"])

    def get_task_dialogue_based_on_affection(self):
        """根据好感度返回不同的任务对话文本"""
        if self.affection < -25:
            return "我没有什么要和你说的，滚开！"
        elif -25 <= self.affection <= 25:
            return self.task_dialogue
        elif 26 <= self.affection <= 75:
            return "嘿，有些任务你可能感兴趣。"
        elif self.affection > 75:
            return "你来了！有些特别的任务需要你来完成。"

    def get_available_tasks_based_on_affection(self):
        """根据好感度返回可接取的任务列表"""
        if self.affection < 25:
            return [task for task in self.tasks if task.quality == "普通"]
        elif 25 <= self.affection <= 75:
            return [task for task in self.tasks if task.quality in ["普通", "稀有"]]
        elif self.affection > 75:
            return self.tasks  # 所有任务都可接取

    def call_market(self, player):
        print(f"你与 {self.name} 进入了市场。")
        # 调用市场模块逻辑
        # market.open_market(player)

    def call_battle(self, player):
        if not self.fight:
            print(f"{self.name} 没有准备战斗信息。")
            return

        print(f"你与 {self.name} 进入了战斗。")
        # 调用战斗模块逻辑
        result = self.go_battle(player)

        if result == "win":
            self.handle_victory(player)
        elif result == "loss":
            self.handle_defeat(player)

    def go_battle(self, player):
        from .battle import Battle
        enemies = self.fight
        battle = Battle(player, [], enemies)
        return battle.run_battle()

    def handle_victory(self, player):
        print(f"你战胜了 {self.name}！")

        choice = input("你想杀掉此 NPC 吗？有些npc会影响剧情和探索，请慎重！(y/n): ").strip().lower()
        if choice == 'y':
            self.remove_npc_from_game()
        else:
            print(f"{self.name} 感谢你放他一条生路。")

    def handle_defeat(self, player):
        print(f"你被 {self.name} 打败了！")
        taunt = self.get_random_taunt()
        print(f"{self.name} 说：'{taunt}'")

    def get_random_taunt(self):
        if self.affection <= -25:
            dialogue_list = self.taunt_dialogue["low"]
        elif self.affection <= 25:
            dialogue_list = self.taunt_dialogue["medium"]
        else:
            dialogue_list = self.taunt_dialogue["high"]

        if dialogue_list:
            return random.choice(dialogue_list)
        else:
            return "看来你还需要多加努力。"

    def remove_npc_from_game(self):
        print(f"{self.name} 被你杀死了，本周目他将不再出现！")
        game_state.player.mark_remove_npc(self.number)  # 玩家记录已删除的 NPC
        game_state.remove_npc(self.number)  # 将 NPC 从游戏中移除
        return f"{self.name}已被你杀死，凄惨地倒在地上。"

    def call_synthesis(self, player):
        print(f"你与 {self.name} 进入了合成模块。")
        # 调用合成模块逻辑
        # synthesis.open_synthesis(player)

    def receive_gift(self, item):
        if item in self.favorite_items:
            self.affection += 5  # 喜欢的物品增加5点好感度
            print(f"{self.name} 非常喜欢 {item.name}，好感度增加了 5 点！")
        else:
            self.affection += 1  # 其他物品只增加1点好感度
            print(f"{self.name} 接受了 {item.name}，好感度增加了 1 点。")

    def __str__(self):
        return (f"NPC({self.number}, {self.name}, {self.description}, "
                f"种族: {self.race}, 好感度: {self.affection})")