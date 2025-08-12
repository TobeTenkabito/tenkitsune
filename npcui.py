import random
import copy
import tkinter as tk
from tkinter import messagebox, simpledialog
from library.lottery_library import lottery_library
from .lotteryui import LotteryUI
from .battleui import BattleUI


class NPCUI:
    def __init__(self, root, npc, player, on_exit_callback):
        self.root = root
        self.npc = npc
        self.player = player
        self.on_exit_callback = on_exit_callback

        # 创建主界面框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        self.title_label = tk.Label(self.main_frame, text=f"与 {self.npc.name} 的互动", font=("Arial", 20))
        self.title_label.pack(pady=10)

        # 描述
        self.description_label = tk.Label(self.main_frame, text=self.npc.description, wraplength=400, justify=tk.LEFT)
        self.description_label.pack(pady=5)

        # 创建互动选项按钮
        self.create_interaction_buttons()

    def create_interaction_buttons(self):
        """创建 NPC 互动按钮"""
        interaction_frame = tk.Frame(self.main_frame)
        interaction_frame.pack(pady=10)

        # 日常对话
        daily_dialogue_button = tk.Button(interaction_frame, text="日常对话", command=self.handle_daily_dialogue)
        daily_dialogue_button.grid(row=0, column=0, padx=10, pady=5)

        # 接取任务
        task_button = tk.Button(interaction_frame, text="接取任务", command=self.handle_task_dialogue)
        task_button.grid(row=0, column=1, padx=10, pady=5)

        # 任务对话
        task_dialogue_button = tk.Button(interaction_frame, text="任务对话", command=self.handle_finish_task_dialogue)
        task_dialogue_button.grid(row=0, column=2, padx=10, pady=5)

        # 交付任务
        submit_task_button = tk.Button(interaction_frame, text="交付任务", command=self.handle_npc_task)
        submit_task_button.grid(row=1, column=0, padx=10, pady=5)

        # 赠送物品
        gift_button = tk.Button(interaction_frame, text="赠送物品", command=self.give_gift)
        gift_button.grid(row=1, column=1, padx=10, pady=5)

        # 交易
        exchange_button = tk.Button(interaction_frame, text="交易物品", command=self.handle_exchange)
        exchange_button.grid(row=1, column=2, padx=10, pady=5)

        # 退出对话
        exit_button = tk.Button(self.main_frame, text="离开互动", command=self.back_to_main)
        exit_button.pack(pady=10)

    def handle_daily_dialogue(self):
        """处理日常对话"""
        # 清空当前界面
        self.clear_main_frame()

        # 随机选择并展示日常对话
        all_dialogues = self.npc.daily_dialogue + self.npc.get_affection_based_dialogue()
        dialogue = random.choice(all_dialogues)

        # 显示 NPC 的对话
        dialogue_label = tk.Label(self.main_frame, text=f"{self.npc.name}: {dialogue}", wraplength=400, justify=tk.LEFT)
        dialogue_label.pack(pady=10)

        # 如果好感度大于 -25，则显示操作选项
        if self.npc.affection >= -25:
            options_frame = tk.Frame(self.main_frame)
            options_frame.pack(pady=10)

            # 继续对话按钮
            continue_button = tk.Button(options_frame, text="继续对话", command=self.continue_daily_dialogue)
            continue_button.grid(row=0, column=0, padx=5, pady=5)

            # 其他功能按钮
            other_actions_button = tk.Button(options_frame, text="其他功能", command=self.show_other_actions)
            other_actions_button.grid(row=0, column=1, padx=5, pady=5)

            # 结束对话按钮
            end_button = tk.Button(options_frame, text="结束对话", command=self.back_to_main)
            end_button.grid(row=0, column=2, padx=5, pady=5)
        else:
            # 如果好感度小于 -25，直接结束对话
            end_button = tk.Button(self.main_frame, text="结束对话", command=self.back_to_main)
            end_button.pack(pady=10)

    def continue_daily_dialogue(self):
        """继续日常对话"""
        # 清空当前界面
        self.clear_main_frame()

        # 再次随机选择并展示日常对话
        all_dialogues = self.npc.daily_dialogue + self.npc.get_affection_based_dialogue()
        dialogue = random.choice(all_dialogues)

        # 显示新的对话
        dialogue_label = tk.Label(self.main_frame, text=f"{self.npc.name}: {dialogue}", wraplength=400, justify=tk.LEFT)
        dialogue_label.pack(pady=10)

        # 添加继续对话按钮，重新调用自身
        continue_button = tk.Button(self.main_frame, text="继续对话", command=self.continue_daily_dialogue)
        continue_button.pack(pady=10)

        # 添加结束对话按钮，结束对话并返回主界面
        end_button = tk.Button(self.main_frame, text="结束对话", command=self.back_to_main)
        end_button.pack(pady=10)

    def show_other_actions(self):
        """展示其他可用功能"""
        # 清空当前界面
        self.clear_main_frame()

        # 根据好感度调用不同功能模块
        options_label = tk.Label(self.main_frame, text="选择要调用的功能:", font=("Arial", 16))
        options_label.pack(pady=10)

        if self.npc.affection >= 0:
            market_button = tk.Button(self.main_frame, text="进入抽奖", command=self.call_lottery)
            market_button.pack(pady=5)

            battle_button = tk.Button(self.main_frame, text="进入战斗", command=self.call_battle)
            battle_button.pack(pady=5)

            synthesis_button = tk.Button(self.main_frame, text="进入合成", command=self.call_synthesis)
            synthesis_button.pack(pady=5)

        # 返回按钮
        back_button = tk.Button(self.main_frame, text="返回", command=self.back_to_top)
        back_button.pack(pady=10)

    def call_lottery(self):
        if self.npc.lottery is not None:
            lottery_pool = lottery_library[self.npc.lottery]
            lottery_ui = LotteryUI(self.root, self.player, self.main_frame, lottery_pool)
            lottery_ui.start_lottery_ui()
        else:
            return "该功能尚未定义"

    def call_battle(self):
        """调用与NPC的战斗"""
        if not self.npc.fight:
            messagebox.showinfo("战斗", f"{self.npc.name} 没有准备战斗信息。")
            return

        # 启动战斗
        enemies = [copy.copy(enemy) for enemy in self.npc.fight]  # 获取战斗中的敌人列表
        messagebox.showinfo("战斗", f"你与 {self.npc.name} 进入了战斗！")

        battle_button = tk.Button(self.main_frame, text="进入战斗", command=self.call_battle)
        battle_button.pack(pady=5)

        # 调用 BattleUI，开始战斗
        BattleUI(self.root, self.player, [], enemies, self.on_battle_end)

    def on_battle_end(self, result):
        """处理战斗结束后的回调"""
        if result == "victory":
            messagebox.showinfo("战斗结果", f"你战胜了 {self.npc.name}！")
            self.handle_victory()
        elif result == "defeat":
            messagebox.showinfo("战斗结果", f"你被 {self.npc.name} 打败了！")
            self.handle_defeat()
        else:
            messagebox.showinfo("战斗结果", "战斗结束了。")

    def handle_victory(self):
        """处理战斗胜利后的逻辑"""
        choice = messagebox.askyesno("选择",
                                     f"你战胜了 {self.npc.name}！你想杀掉此 NPC 吗？\n(某些NPC会影响剧情和探索，请慎重！)")
        if choice:
            self.npc.remove_npc_from_game()  # 如果选择杀死NPC，调用移除逻辑
        else:
            messagebox.showinfo("选择", f"{self.npc.name} 感谢你放他一条生路。")

    def handle_defeat(self):
        """处理战斗失败后的逻辑"""
        taunt = self.npc.get_random_taunt()  # 获取NPC的嘲讽台词
        messagebox.showinfo("战斗失败", f"{self.npc.name} 说：'{taunt}'")

    def call_synthesis(self):
        return "暂未开放"

    def handle_task_dialogue(self):
        """处理接取任务"""
        self.clear_main_frame()

        available_tasks = self.npc.get_available_tasks_based_on_affection()  # 获取 NPC 提供的可接任务

        if not available_tasks:
            tk.Label(self.main_frame, text=f"{self.npc.name} 当前没有可接取的任务。", font=("Arial", 14)).pack(pady=10)
        else:
            tk.Label(self.main_frame, text=f"{self.npc.name} 提供的任务:", font=("Arial", 14)).pack(pady=10)
            for i, task in enumerate(available_tasks):
                # 显示任务名称，并设置点击按钮来查看任务详情并接取任务
                task_button = tk.Button(self.main_frame, text=f"任务: {task.name}",
                                        command=lambda t=task: self.show_task_details(t))
                task_button.pack(pady=5)

        self.create_back_button()  # 返回按钮

    def show_task_details(self, task):
        """显示任务详情并提供接取选项"""
        self.clear_main_frame()

        # 显示任务名称和描述
        tk.Label(self.main_frame, text=f"任务: {task.name}", font=("Arial", 16)).pack(pady=10)
        tk.Label(self.main_frame, text=f"描述: {task.description}", wraplength=400, justify=tk.LEFT).pack(pady=5)

        # 显示任务接取条件
        tk.Label(self.main_frame, text="任务接取条件:", font=("Arial", 14)).pack(pady=5)
        if task.can_accept(self.player):
            tk.Label(self.main_frame, text="你满足条件，可以接取此任务。", fg="green").pack(pady=5)
            # 接取任务按钮
            accept_button = tk.Button(self.main_frame, text="接取任务", command=lambda: self.accept_task(task))
            accept_button.pack(pady=10)
        else:
            tk.Label(self.main_frame, text="你不满足接取此任务的条件。", fg="red").pack(pady=5)

        self.create_back_button()  # 返回按钮

    def accept_task(self, task):
        """接取任务逻辑"""
        if task.can_accept(self.player):
            task.accept(self.player)
            messagebox.showinfo("任务接取成功", f"你已接取任务: {task.name}")
        else:
            messagebox.showwarning("无法接取任务", "你不满足接取此任务的条件。")
        self.back_to_top()  # 接取任务后返回 NPC 主界面

    def handle_finish_task_dialogue(self):
        from all.gamestate import game_state
        player = game_state.get_player()
        """处理任务对话"""
        self.clear_main_frame()
        # 检查玩家已接的任务，是否有任务要求与当前 NPC 对话
        completed_any_task = False
        for task in self.player.accepted_tasks:
            for condition in task.completion_conditions:
                # 如果任务的完成条件是与当前 NPC 对话
                if "talk_to_npc" in condition and condition["talk_to_npc"] == self.npc.number:
                    # 标记玩家与 NPC 对话，满足任务条件
                    player.talk_to_npc(self.npc.number)
                    # 检查是否完成任务
                    if task.check_completion(self.player):  # 再次检查任务是否完成
                        completed_any_task = True
                        self.show_finish_task_dialogue(task)  # 显示完成对话
                        break

        if not completed_any_task:
            tk.Label(self.main_frame, text=f"{self.npc.name}: 没有可以完成的任务。", font=("Arial", 14)).pack(pady=10)

        self.create_back_button()

    def show_finish_task_dialogue(self, task):
        """显示任务完成对话，并处理任务完成逻辑"""
        self.clear_main_frame()

        # 检查 NPC 的 finish_task_dialogue 是否是字典
        if isinstance(self.npc.finish_task_dialogue, dict):
            # 获取任务编号对应的完成对话
            dialogue = self.npc.finish_task_dialogue.get(task.number, "感谢你完成任务！")
        else:
            # 如果不是字典（字符串形式），直接使用对话
            dialogue = self.npc.finish_task_dialogue

        # 显示任务完成对话
        tk.Label(self.main_frame, text=f"{self.npc.name}: {dialogue}", wraplength=400, justify=tk.LEFT,
                 font=("Arial", 14)).pack(pady=10)

        # 任务完成按钮
        complete_button = tk.Button(self.main_frame, text="完成任务", command=lambda: self.complete_task(task))
        complete_button.pack(pady=10)

        self.create_back_button()

    def handle_npc_task(self):
        """处理交付任务"""
        self.clear_main_frame()

        # 获取当前可以交付的任务
        ready_to_complete_tasks = [task for task in self.player.ready_to_complete_tasks if
                                   task.source_npc == self.npc.number]

        if not ready_to_complete_tasks:
            tk.Label(self.main_frame, text=f"{self.npc.name} 没有可以交付的任务。", font=("Arial", 14)).pack(pady=10)
        else:
            tk.Label(self.main_frame, text=f"{self.npc.name} 的任务:", font=("Arial", 14)).pack(pady=10)
            for task in ready_to_complete_tasks:
                task_button = tk.Button(self.main_frame, text=f"交付任务: {task.name}",
                                        command=lambda t=task: self.complete_task(t))
                task_button.pack(pady=5)

        self.create_back_button()

    def complete_task(self, task):
        """交付任务逻辑"""
        self.clear_main_frame()

        # 如果任务有 source_npc，要求交付任务给指定的 NPC
        if task.source_npc:
            # 显示任务交付详情
            tk.Label(self.main_frame, text=f"交付任务: {task.name}", font=("Arial", 16)).pack(pady=10)
            tk.Label(self.main_frame, text=f"描述: {task.description}", wraplength=400, justify=tk.LEFT).pack(pady=5)

            # 显示任务奖励
            tk.Label(self.main_frame, text="任务奖励:", font=("Arial", 14)).pack(pady=5)
            for reward in task.rewards:
                if reward.get('item'):
                    tk.Label(self.main_frame, text=f"{reward['item'].name} x {reward['quantity']}").pack(pady=2)
                elif reward.get('attribute'):
                    tk.Label(self.main_frame, text=f"{reward['attribute'].name} x {reward['value']}").pack(pady=2)
                elif reward.get('amount'):
                    tk.Label(self.main_frame, text=f"经验值: {reward['amount']}").pack(pady=2)

            # 交付任务按钮
            tk.Button(self.main_frame, text="交付任务", command=lambda: self.finalize_task_completion(task)).pack(
                pady=10)
            self.create_back_button()
        else:
            self.finalize_task_completion(task)

    def finalize_task_completion(self, task):
        """完成任务交付并发放奖励"""
        task.give_rewards(self.player)
        messagebox.showinfo("任务完成", f"你成功完成了任务: {task.name}，并获得了奖励！")
        if task in self.player.ready_to_complete_tasks:
            self.player.ready_to_complete_tasks.remove(task)  # 从可交付任务中移除

        self.back_to_top()  # 交付任务后返回 NPC 主界面

    def give_gift(self):
        """处理赠送物品"""
        self.clear_main_frame()

        # 获取玩家背包中的物品
        inventory_items = self.player.get_inventory()

        if not inventory_items:
            messagebox.showinfo("提示", "你没有可以赠送的物品。")
            self.create_back_button()
            return

        # 显示物品选择界面
        gift_frame = tk.Frame(self.main_frame)
        gift_frame.pack(pady=10)
        tk.Label(gift_frame, text="请选择要赠送的物品:").pack(pady=5)
        listbox = tk.Listbox(gift_frame)
        for item in inventory_items:
            listbox.insert(tk.END, f"{item.name} (数量: {item.quantity})")
        listbox.pack(pady=5)

        def confirm_gift():
            selected_index = listbox.curselection()
            if not selected_index:
                messagebox.showwarning("错误", "请选择要赠送的物品。")
                return

            selected_item = inventory_items[selected_index[0]]

            # 输入赠送数量
            quantity = simpledialog.askinteger("输入数量", f"你有 {selected_item.quantity} 个 {selected_item.name}，请输入赠送的数量:")
            if quantity and 0 < quantity <= selected_item.quantity:
                # 赠送物品并更新好感度
                for _ in range(quantity):
                    self.npc.receive_gift(selected_item)
                    self.player.remove_from_inventory(selected_item.number, 1)
                messagebox.showinfo("提示", f"你赠送了 {quantity} 个 {selected_item.name} 给 {self.npc.name}。")
            else:
                messagebox.showerror("错误", "输入的数量无效。")
            self.back_to_top()

        confirm_button = tk.Button(gift_frame, text="确认赠送", command=confirm_gift)
        confirm_button.pack(pady=10)
        self.create_back_button()

    def handle_exchange(self):
        """处理交易逻辑 - 前端逻辑"""
        self.clear_main_frame()

        # 显示可交易物品
        if not self.npc.exchange:
            messagebox.showinfo("交易信息", f"{self.npc.name} 当前没有可交易的物品。")
            return

        tk.Label(self.main_frame, text=f"{self.npc.name} 提供以下物品进行交易：").pack(anchor="w")

        for i, (offered_item, details) in enumerate(self.npc.exchange.items(), 1):
            required_item, required_quantity = details['item'], details['quantity']
            item_description = f"{i}. {offered_item.name} - 需要 {required_item.name} x{required_quantity}"
            tk.Label(self.main_frame, text=item_description).pack(anchor="w")

            # 单次交易按钮
            single_trade_btn = tk.Button(self.main_frame, text="单次交易",
                                         command=lambda idx=i - 1: self.execute_trade(idx, quantity=1))
            single_trade_btn.pack(anchor="w")

            # 批量交易按钮
            batch_trade_btn = tk.Button(self.main_frame, text="批量交易",
                                        command=lambda idx=i - 1: self.handle_batch_trade(idx))
            batch_trade_btn.pack(anchor="w")

            # 全部交易按钮
            all_trade_btn = tk.Button(self.main_frame, text="全部交易",
                                      command=lambda idx=i - 1: self.handle_all_trade(idx))
            all_trade_btn.pack(anchor="w")

        # 返回按钮
        self.create_back_button()

    def handle_batch_trade(self, choice):
        """处理批量交易输入数量并执行"""
        offered_item, details = list(self.npc.exchange.items())[choice]
        required_item, required_quantity = details['item'], details['quantity']

        # 用户输入批量交易的数量
        quantity = simpledialog.askinteger("批量交易", f"请输入需要交易的 {offered_item.name} 数量：")
        if quantity is None or quantity <= 0:
            return

        # 计算批量交易需要的总物品数
        total_required_quantity = required_quantity * quantity
        if self.player.remove_from_inventory(required_item.number, total_required_quantity):
            for _ in range(quantity):
                self.player.add_to_inventory(offered_item)  # 按输入数量添加物品
            messagebox.showinfo("交易成功",
                                f"你成功交易了 {total_required_quantity} 个 {required_item.name}，获得了 {quantity} 个 {offered_item.name}。")
        else:
            messagebox.showwarning("交易失败", f"你没有足够的 {required_item.name} 进行批量交易。")

    def handle_all_trade(self, choice):
        """计算玩家可进行的最大交易量并执行"""
        offered_item, details = list(self.npc.exchange.items())[choice]
        required_item, required_quantity = details['item'], details['quantity']

        # 计算玩家拥有的物品数可以进行的最大交易次数
        player_quantity = self.player.get_inventory_count(required_item.number)
        max_trade_quantity = player_quantity // required_quantity

        if max_trade_quantity > 0:
            total_required_quantity = max_trade_quantity * required_quantity
            self.player.remove_from_inventory(required_item.number, total_required_quantity)
            for _ in range(max_trade_quantity):
                self.player.add_to_inventory(offered_item)  # 添加物品
            messagebox.showinfo("全部交易成功",
                                f"你成功交易了 {total_required_quantity} 个 {required_item.name}，获得了 {max_trade_quantity} 个 {offered_item.name}。")
        else:
            messagebox.showwarning("交易失败", f"你没有足够的 {required_item.name} 进行交易。")

    def execute_trade(self, choice, quantity=1):
        """执行单次交易逻辑"""
        offered_item, details = list(self.npc.exchange.items())[choice]
        required_item, required_quantity = details['item'], details['quantity']

        # 检查玩家是否有足够的交易物品
        total_required_quantity = required_quantity * quantity
        if self.player.remove_from_inventory(required_item.number, total_required_quantity):
            for _ in range(quantity):
                self.player.add_to_inventory(offered_item)  # 给玩家添加物品
            messagebox.showinfo("交易成功",
                                f"你成功交易了 {total_required_quantity} 个 {required_item.name}，获得了 {quantity} 个 {offered_item.name}。")
        else:
            messagebox.showwarning("交易失败", f"你没有足够的 {required_item.name} 进行交易。")

    def create_back_button(self):
        """创建返回按钮"""
        back_button = tk.Button(self.main_frame, text="离开互动", command=self.back_to_top)
        back_button.pack(pady=5)

    def back_to_main(self):
        """返回主界面并执行回调"""
        self.clear_main_frame()
        if self.on_exit_callback:
            print("退出NPC对话，进入回调逻辑")
            self.on_exit_callback()

    def back_to_top(self):
        self.clear_main_frame()
        self.create_interaction_buttons()

    def clear_main_frame(self):
        """清除当前界面的所有内容"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()