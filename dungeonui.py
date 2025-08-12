import tkinter as tk
from tkinter import messagebox
from common.ui.battleui import BattleUI
from common.ui.npcui import NPCUI


class DungeonUI:
    def __init__(self, root, dungeon, player, on_exit_callback):
        self.root = root
        self.dungeon = dungeon
        self.player = player
        self.on_exit_callback = on_exit_callback  # 回调接口

        # 创建主界面框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        self.title_label = tk.Label(self.main_frame, text=f"秘境: {self.dungeon.name}", font=("Arial", 20))
        self.title_label.pack(pady=10)

        # 秘境描述
        self.description_label = tk.Label(self.main_frame, text=self.dungeon.description, wraplength=400,
                                          justify=tk.LEFT)
        self.description_label.pack(pady=5)

        # 当前最高层数显示
        self.highest_floor_label = tk.Label(self.main_frame, text=f"当前通过的最高层数: {self.dungeon.highest_floor}")
        self.highest_floor_label.pack(pady=5)

        self.when_enter_dungeon()

        # 楼层选择部分
        self.floor_listbox = tk.Listbox(self.main_frame, height=10)
        for floor in self.dungeon.floors:
            status = "已完成" if floor.completed else "未完成"
            self.floor_listbox.insert(tk.END, f"第 {floor.number} 层 - {status}")
        self.floor_listbox.pack(pady=10)

        # 进入层按钮
        self.enter_floor_button = tk.Button(self.main_frame, text="进入选定的层", command=self.enter_selected_floor)
        self.enter_floor_button.pack(pady=5)

        exit_button = tk.Button(self.main_frame, text="逃离秘境", command=self.back_to_main)
        exit_button.pack(pady=2)

    def display_npc_affection_changes(self):
        """显示 NPC 好感度变化"""
        affection_changes = self.dungeon.npc_affection_impact
        if not affection_changes:
            return

        # 从 NPC 库中获取 NPC 信息并显示好感度变化
        from library.npc_library import npc_library
        changes_text = ""
        for npc_id, affection_change in affection_changes.items():
            npc = npc_library.get(npc_id)
            if npc:
                changes_text += f"{npc.name} 的好感度提升了 {affection_change} 点。\n"

        if changes_text:
            messagebox.showinfo("NPC 好感度变化", changes_text)

    def when_enter_dungeon(self):
        """进入秘境前的检查和处理"""
        # 检查秘境是否已经通关并且不可重复挑战
        if (self.dungeon.completed or self.dungeon.number in self.player.dungeons_cleared) and not self.dungeon.can_replay_after_completion:
            messagebox.showwarning("无法进入", f"秘境 '{self.dungeon.name}' 已经通关，无法再次进入。")
            self.back_to_main()
            return

        # 处理 NPC 好感度变化
        self.dungeon.apply_npc_affection_impact(self.player)

        # 显示好感度变化
        self.display_npc_affection_changes()

        # 如果秘境有 NPC 并且 NPC 尚未被移除
        for floor in self.dungeon.floors:
            if floor.npc is not None and floor.npc.number in self.player.npcs_removed:
                # 如果 NPC 已被移除，则将其设置为 None
                floor.npc = None

    def enter_selected_floor(self):
        try:
            selected_index = self.floor_listbox.curselection()[0]
            selected_floor = self.dungeon.floors[selected_index]

            # 获取当前秘境编号
            dungeon_number = self.dungeon.number
            # 获取玩家在当前秘境中通过的最高楼层
            player_highest_floor = self.player.highest_floor.get(dungeon_number, 0)

            # 如果所选楼层超过了玩家的最高通关楼层 + 1，阻止进入
            if selected_floor.number > player_highest_floor + 1:
                messagebox.showwarning(
                    "无法进入", f"请先完成第 {player_highest_floor + 1} 层才能进入第 {selected_floor.number} 层。"
                )
                return

            # 显示选定楼层的详细信息
            self.show_floor_details(selected_floor)

        except IndexError:
            messagebox.showwarning("错误", "请选择要进入的楼层。")

    def show_floor_details(self, floor):
        """显示秘境楼层详情"""
        # 清空主界面
        self.clear_main_frame()

        # 重新创建 main_frame，确保其存在
        self.main_frame = tk.Frame(self.root)  # 或者 self.content_frame 取决于 UI 结构
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 显示层的描述
        floor_label = tk.Label(self.main_frame, text=f"第 {floor.number} 层: {floor.description}", font=("Arial", 16))
        floor_label.pack(pady=10)

        # NPC交互信息
        if floor.npc:
            npc_label = tk.Label(self.main_frame, text=f"NPC: {floor.npc.name}")
            npc_label.pack(pady=5)
        else:
            npc_label = tk.Label(self.main_frame, text="该层没有NPC")
            npc_label.pack(pady=5)

        # 进入Buff信息
        if isinstance(floor.entry_buff, list):
            entry_buff_names = ', '.join([buff.name for buff in floor.entry_buff])
            entry_buff_label = tk.Label(self.main_frame, text=f"进入时获得的Buff: {entry_buff_names}")
        elif floor.entry_buff:  # 单个 Buff 的情况
            entry_buff_label = tk.Label(self.main_frame, text=f"进入时获得的Buff: {floor.entry_buff.name}")
        else:
            entry_buff_label = tk.Label(self.main_frame, text="该层没有Buff")
        entry_buff_label.pack(pady=5)

        # 敌人信息
        if floor.enemies:
            enemies_text = ', '.join([enemy.name for enemy in floor.enemies])
            enemies_label = tk.Label(self.main_frame, text=f"敌人: {enemies_text}")
            enemies_label.pack(pady=5)
        else:
            enemies_label = tk.Label(self.main_frame, text="该层没有敌人")
            enemies_label.pack(pady=5)

        # 奖励信息
        rewards_text = ', '.join([reward['item'].name for reward in floor.rewards])
        rewards_label = tk.Label(self.main_frame, text=f"固定奖励: {rewards_text}")
        rewards_label.pack(pady=5)

        # 进入层按钮
        enter_button = tk.Button(self.main_frame, text="进入此层", command=lambda: self.enter_floor(floor))
        enter_button.pack(pady=10)

        # 返回按钮
        back_button = tk.Button(self.main_frame, text="返回", command=self.back_to_main)
        back_button.pack(pady=5)

    def enter_floor(self, floor):
        # 判断是否是首次通过
        is_first_time = self.player.highest_floor.get(self.dungeon.number, 0) < floor.number

        if floor.npc:
            print("进入NPC互动")
            self.clear_main_frame()
            self.main_frame = tk.Frame(self.root)
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            NPCUI(self.root, floor.npc, self.player, self.after_npc_interaction(floor, is_first_time))
        else:
            # 如果没有 NPC，则直接处理敌人或战斗逻辑
            self.after_npc_interaction(floor, is_first_time)()

    def after_npc_interaction(self, floor, is_first_time):
        def proceed():
            print(f"进入战斗回调: {floor.number} 层, 首次通过: {is_first_time}")
            if floor.enemies:
                print("发现敌人，进入战斗")
                BattleUI(self.root, self.player, [], floor.enemies,
                         lambda result: self.on_battle_end(result, floor, is_first_time))
            else:
                self.handle_no_battle(floor, is_first_time)

        return proceed

    def handle_no_battle(self, floor, is_first_time):
        # 没有敌人，直接发放奖励并结束
        floor.completed = True
        floor.give_rewards(self.player, is_first_time)
        self.update_the_highest_floor(floor.number)  # 更新最高层
        messagebox.showinfo("层完成", f"你通过了第 {floor.number} 层！")

        # 返回主界面
        self.back_to_main()

    def on_battle_end(self, result, floor, is_first_time):
        """根据战斗结果处理秘境楼层完成状态"""
        if result == "victory":
            messagebox.showinfo("胜利", f"你通过了第 {floor.number} 层！")
            floor.completed = True
            floor.give_rewards(self.player, is_first_time)  # 发放奖励
            self.update_the_highest_floor(floor.number)  # 更新最高层
        elif result == "defeat":
            messagebox.showwarning("失败", f"你未能通过第 {floor.number} 层。"
                                           f"\n{self.dungeon.handle_loss_explore(self.player)}")

        # 返回主界面
        self.back_to_main()

    def update_the_highest_floor(self, floor_number):
        self.dungeon.highest_floor = max(self.dungeon.highest_floor, floor_number)
        self.player.update_highest_floor(self.dungeon.number, floor_number)
        self.highest_floor_label.config(text=f"当前通过的最高层数: {self.dungeon.highest_floor}")
        self.evaluate_complete()

    def evaluate_complete(self):
        # 从玩家的最高层记录中获取当前副本编号对应的最高层数
        highest_floor = self.player.get("highest_floor", {})
        dungeon_number = self.dungeon.number

        if dungeon_number in highest_floor:
            # 获取对应副本的最高层数值
            player_highest_floor = highest_floor[dungeon_number]

            # 判断是否不小于副本的楼层数
            if player_highest_floor >= len(self.dungeon.floors):
                # 调用副本完成方法
                self.dungeon.finish(self.player)
        else:
            self.dungeon.finish(self.player)  # 只有一层的情况，直接完成

    def clear_main_frame(self):
        self.main_frame.destroy()

    def back_to_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        if self.on_exit_callback:
            print("退出秘境")
            self.on_exit_callback()