import tkinter as tk
import json
from tkinter import simpledialog, messagebox
from .battleui import BattleUI


class StoryUI:
    def __init__(self, root, player, story_manager, on_exit_callback):
        self.root = root
        self.player = player
        self.story_manager = story_manager
        self.on_exit_callback = on_exit_callback  # 回调到主界面
        self.current_node = None
        self.current_chapter = None
        self.auto_play = False
        self.story_frame = tk.Frame(self.root)
        self.story_frame.pack()
        self.text_slices = []  # 用于存储切分的文本段
        self.current_text_index = 0  # 当前显示的文本段的索引

        # 创建章节选择界面
        self.create_chapter_selection()

    def create_chapter_selection(self):
        """创建章节选择界面"""
        self.clear_frame()
        tk.Label(self.story_frame, text="选择章节", font=("Arial", 16)).pack(pady=10)

        # 从 player.story_progress 中获取已完成的章节
        chapters_completed = self.player.story_progress.get("chapters_completed", {})

        # 列出章节供选择
        for chapter in self.story_manager.chapters:
            # 如果章节在 story_progress 中标记为已完成，则将 chapter.is_completed 设为 True
            if str(chapter.number) in chapters_completed:
                chapter.is_completed = chapters_completed[str(chapter.number)]

            # 更新按钮文本
            status = "已完成" if chapter.is_completed else "未完成"
            btn_text = f"{chapter.number} - {chapter.title} ({status})"

            # 创建章节选择按钮
            button = tk.Button(self.story_frame, text=btn_text,
                               command=lambda ch=chapter: self.select_chapter(ch))
            button.pack(pady=5)

            # 如果章节不是第一章，且前一章未完成，则禁用该章节按钮
            if chapter.number != 1 and not self.story_manager.chapters[chapter.number - 2].is_completed:
                button.config(state="disabled")  # 禁用未解锁的章节

        tk.Button(self.story_frame, text="返回", command=self.exit_story).pack(pady=10)

    def select_chapter(self, chapter):
        """根据选择章节进入节点选择界面"""
        self.story_manager.current_chapter = chapter
        self.create_node_selection()

    def create_node_selection(self):
        """创建节点选择界面"""
        self.clear_frame()
        tk.Label(self.story_frame, text="选择节点", font=("Arial", 16)).pack(pady=10)

        # 获取当前章节号
        current_chapter_number = self.story_manager.current_chapter.number

        # 获取当前章节已完成的节点列表
        completed_nodes = self.player.story_progress.get("completed_nodes", [])

        # 提取已完成的当前章节的节点
        completed_node_ids = [node[1] for node in completed_nodes if node[0] == current_chapter_number]

        # 列出节点供选择
        for node_id, node in self.story_manager.current_chapter.nodes.items():
            btn_text = f"节点 {node_id}"

            # 默认解锁第一个节点，或者如果节点已完成则解锁
            if node_id == 1 or node_id in completed_node_ids:
                button_state = "normal"  # 可点击
            else:
                button_state = "disabled"  # 禁用

            button = tk.Button(self.story_frame, text=btn_text,
                               command=lambda n=node: self.start_story(n),
                               state=button_state)  # 设置按钮状态
            button.pack(pady=5)

        tk.Button(self.story_frame, text="返回", command=self.create_chapter_selection).pack(pady=10)

    def start_story(self, node):
        """启动故事模式并显示文本内容"""
        self.current_node = node
        self.current_chapter = self.story_manager.current_chapter
        self.clear_frame()
        self.text_slices = split_text(self.current_node.description)
        self.current_text_index = 0
        self.show_next_text()

    def show_next_text(self):
        """显示下一段故事文本或执行节点操作"""
        # 确保索引没有超出文本切片的长度
        if self.current_text_index < len(self.text_slices):
            # 处理空白片段
            while self.current_text_index < len(self.text_slices) and not self.text_slices[self.current_text_index].strip():
                print(f"Skipping empty slice at index: {self.current_text_index}")  # 调试信息
                self.current_text_index += 1

            # 确保当前索引在有效范围内
            if self.current_text_index < len(self.text_slices):
                current_text = self.text_slices[self.current_text_index]
                print(f"Displaying text at index {self.current_text_index}: {current_text}")  # 调试信息

                # 显示文本
                self.clear_frame()
                text_label = tk.Label(self.story_frame, text=current_text, font=("Arial", 14), wraplength=500,
                                      justify="left")
                text_label.pack(pady=5)
                self.create_story_controls()
                # 增加 current_text_index，处理下一段文本
                self.current_text_index += 1

                # 自动播放逻辑
                if self.auto_play:
                    self.root.after(3000, self.show_next_text)
            else:
                # 如果没有文本片段，继续执行节点操作
                self.execute_node_actions()
                self.create_choices_buttons()
                self.create_story_controls()

        else:
            # 播放完毕，执行节点操作
            self.execute_node_actions()

            # 检查是否为终节点，如果是则不创建选择或自动跳转
            is_end_node = any(
                action.type == "end" for action in self.current_node.actions) if self.current_node.actions else False

            if self.current_node.choices and not is_end_node:
                # 如果有选择且不是终节点，则创建选择按钮
                self.create_choices_buttons()
                self.create_story_controls()
            elif not is_end_node:
                # 如果没有选择项，且不是终节点，检查是否有下一个节点并自动切换
                next_node_id = self.current_node.node_id + 1
                next_node = self.current_chapter.get_node(next_node_id)
                if next_node:
                    print(f"文本播放完毕，自动进入下一个节点: {next_node_id}")
                    self.start_story(next_node)
            else:
                # 如果是终节点，则返回章节选择界面或结束故事流程
                print("当前节点为终节点，停止自动跳转")
                # 可以调用返回章节选择或其他结束操作
                self.create_chapter_selection()

    def execute_node_actions(self):
        """执行当前节点的所有动作"""
        if self.current_node.actions:
            for action in self.current_node.actions:
                action.execute()

        # 如果当前节点有战斗，则启动战斗界面
        if self.current_node.battle:
            self.start_battle_ui(self.current_node.battle)
        else:
            # 当节点动作执行完，标记节点为完成
            self.mark_node_completed(self.current_node)

            # 检查是否为当前章节的最后一个节点
            next_node_id = self.current_node.node_id + 1
            is_last_node = not self.current_chapter.get_node(next_node_id)

            # 如果章节完成且当前节点为最后一个节点，返回章节选择界面
            if self.current_chapter.is_completed and is_last_node:
                print(f"章节 {self.current_chapter.number} 已完成，返回章节选择界面")
                self.create_chapter_selection()

    def mark_node_completed(self, node):
        """标记当前节点为已完成"""
        if node:
            node.mark_completed()  # 标记节点为完成
            self.story_manager.mark_node_completed(node.chapter_number, node.node_id)  # 传递章节号和节点号
            print(f"章节 {node.chapter_number} 的节点 {node.node_id} 已完成")

    def create_choices_buttons(self):
        """为节点中的每个选择创建按钮"""
        if self.current_node.choices:
            for choice in self.current_node.choices:
                choice_button = tk.Button(self.story_frame, text=choice.description,
                                          command=lambda c=choice: self.select_choice(c))
                choice_button.pack(pady=20)

    def select_choice(self, choice):
        """选择故事分支后，进入相应的节点"""
        self.start_story(choice.next_node)

    def start_battle_ui(self, battle_data):
        """启动战斗UI并传递玩家、敌人等信息"""
        player = self.player
        allies = battle_data.allies if hasattr(battle_data, 'allies') else []
        enemies = battle_data.enemies if hasattr(battle_data, 'enemies') else []

        def on_battle_end(result):
            """处理战斗结束后的逻辑，继续执行当前节点的剩余操作"""
            if result == "victory":
                print("胜利！继续故事...")
                # 标记当前节点为完成
                self.mark_node_completed(self.current_node)
                # 检查当前节点是否有 next_node_id
                next_node_id = getattr(self.current_node, 'next_node_id', None)
                if next_node_id is not None:
                    print(f"跳转到下一个节点: {next_node_id}")
                    next_node = self.current_chapter.get_node(next_node_id)
                else:
                    # 如果没有 next_node_id，默认跳转到当前节点 id + 1
                    next_node_id = self.current_node.node_id + 1
                    next_node = self.current_chapter.get_node(next_node_id)

                # 检查是否有下一个节点
                if next_node:
                    self.start_story(next_node)
                else:
                    print(f"节点 {next_node_id} 不存在，结束故事")

            elif result == "defeat":
                print("失败...故事结束。")
                self.exit_story()  # 退出故事模式或返回主界面

        # 创建并显示 BattleUI
        self.battle_ui = BattleUI(self.root, player, allies, enemies, on_battle_end)

    def create_story_controls(self):
        """创建故事控制按钮"""
        control_frame = tk.Frame(self.story_frame)
        control_frame.pack(pady=10)

        prev_button = tk.Button(control_frame, text="上一句", command=self.show_previous_text)
        prev_button.pack(side=tk.LEFT, padx=5)

        next_button = tk.Button(control_frame, text="下一句", command=self.show_next_text)
        next_button.pack(side=tk.LEFT, padx=5)

        tk.Button(control_frame, text="保存", command=self.save_progress).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="读档", command=self.load_progress).pack(side=tk.LEFT, padx=5)
        auto_btn = tk.Button(control_frame, text="自动播放", command=self.toggle_auto_play)
        auto_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="退出", command=self.exit_story).pack(side=tk.LEFT, padx=5)

    def show_previous_text(self):
        if self.current_text_index > 0:
            self.current_text_index -= 1
            self.clear_frame()  # 清除当前所有小部件
            if self.text_slices:
                current_text = self.text_slices[self.current_text_index]
                print(f"{current_text}")
                # 创建新的文本标签
                text_label = tk.Label(self.story_frame, text=current_text, font=("Arial", 14), wraplength=500,
                                      justify="left")
                text_label.pack(pady=5)

            # 重新创建故事控制按钮
            self.create_story_controls()

    def save_progress(self):
        # 让玩家输入存档编号
        save_slot = simpledialog.askstring("输入存档编号", "请输入存档编号（1至5）")
        if not save_slot:
            messagebox.showwarning("存档失败", "存档编号不能为空")
            return

        # 1. 检查当前节点和章节是否存在
        if self.current_node and self.current_node.node_id and self.story_manager.current_chapter:
            # 保存当前章节和节点
            current_chapter = self.story_manager.current_chapter.number
            current_node_id = self.current_node.node_id
            print(f"保存当前章节: {current_chapter}, 当前节点: {current_node_id}")

            # 保存故事进度
            new_progress = {
                "current_chapter": current_chapter,
                "current_node": current_node_id,
                "completed_nodes": self.player.story_progress.get("completed_nodes", {}),
                "chapters_completed": self.player.story_progress.get("chapters_completed", {})
            }

            # 2. 读取已有存档（如果存在）
            save_path = f"data/save_slot_{save_slot}.json"
            try:
                # 如果文件存在，加载现有数据
                with open(save_path, 'r', encoding='GBK') as f:
                    save_data = json.load(f)
            except FileNotFoundError:
                # 如果文件不存在，创建一个新的存档结构
                save_data = {"player": {},
                             "npcs_affection": {},
                             "story_progress": {}}

            # 3. 更新存档中的故事进度
            save_data["story_progress"] = new_progress

            # 4. 将更新后的数据写回文件
            try:
                with open(save_path, 'w', encoding='GBK') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("存档成功", f"进度已保存到 {save_path}")
                print(f"进度已保存到 {save_path}")
            except Exception as e:
                messagebox.showerror("存档失败", f"保存进度时出错: {e}")
        else:
            messagebox.showerror("存档失败", "当前节点或章节信息不完整，无法保存进度。")

    def load_progress(self):
        # 让玩家输入存档编号
        save_slot = simpledialog.askstring("输入读档编号", "请输入存档编号（1至5）")
        if not save_slot:
            messagebox.showwarning("读档失败", "存档编号不能为空")
            return

        # 读取指定的存档文件
        load_path = f"data/save_slot_{save_slot}.json"
        try:
            with open(load_path, 'r', encoding='GBK') as f:
                save_data = json.load(f)

            # 恢复玩家的故事进度
            self.player.story_progress["current_chapter"] = save_data["story_progress"]["current_chapter"]
            self.player.story_progress["current_node"] = save_data["story_progress"]["current_node"]
            self.player.story_progress["completed_nodes"] = save_data["story_progress"]["completed_nodes"]
            self.player.story_progress["chapters_completed"] = save_data["story_progress"]["chapters_completed"]

            messagebox.showinfo("读档成功", f"进度已从 {load_path} 加载")
            print(f"进度已从 {load_path} 加载")

            # 恢复游戏的当前章节和节点信息
            self.current_chapter = self.story_manager.chapters[self.player.story_progress["current_chapter"] - 1]
            self.current_node = self.current_chapter.get_node(self.player.story_progress["current_node"])
            self.start_story(self.current_node)  # 从读取的节点开始游戏

        except FileNotFoundError:
            messagebox.showerror("读档失败", f"未找到存档文件 {load_path}")
        except Exception as e:
            messagebox.showerror("读档失败", f"读取存档时出错: {e}")

    def toggle_auto_play(self):
        self.auto_play = not self.auto_play
        if self.auto_play:
            self.show_next_text()

    def exit_story(self):
        self.story_frame.destroy()
        self.on_exit_callback()

    def clear_frame(self):
        for widget in self.story_frame.winfo_children():
            widget.destroy()


def split_text(description):
    if isinstance(description, list):
        print("description 是列表，逐行处理")
        text_slices = []
        for line in description:
            text_slices.extend(line.split('|'))
        return text_slices
    elif isinstance(description, str):
        print("description 是字符串，直接分割")
        return description.split('|')
    else:
        raise ValueError("description 既不是字符串也不是列表")
