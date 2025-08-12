import tkinter as tk


class CultivationUI:
    def __init__(self, root, cultivation_system):
        self.root = root
        self.cultivation_system = cultivation_system

        # 主框架，用于容纳修为界面
        self.cultivation_frame = tk.Frame(self.root)
        self.cultivation_frame.pack(fill=tk.BOTH, expand=True)

        # 显示剩余培养点和修为点数的 Label
        self.unused_points_label = tk.Label(self.cultivation_frame,
                                            text=f"剩余培养点: {self.cultivation_system.unused_points}")
        self.unused_points_label.pack(pady=10)

        self.cultivation_points_label = tk.Label(self.cultivation_frame,
                                                 text=f"修为点: {self.cultivation_system.player.cultivation_point}")
        self.cultivation_points_label.pack(pady=10)

        # 创建按钮
        self.create_buttons()

        # 用于显示结果的 Text 区域
        self.result_text = tk.Text(self.cultivation_frame, wrap="word", height=10, width=50)
        self.result_text.pack(pady=10)

    def create_buttons(self):
        """ 创建修为界面按钮 """
        button_frame = tk.Frame(self.cultivation_frame)
        button_frame.pack(pady=10)

        # 各项操作按钮
        allocate_points_button = tk.Button(button_frame, text="分配修为点数", command=self.allocate_points_menu)
        allocate_points_button.grid(row=0, column=0, padx=10)

        choose_xinfa_button = tk.Button(button_frame, text="选择心法线", command=self.choose_xinfa_line_menu)
        choose_xinfa_button.grid(row=0, column=1, padx=10)

        check_xinfa_unlock_button = tk.Button(button_frame, text="检查心法解锁", command=self.check_xinfa_unlock)
        check_xinfa_unlock_button.grid(row=1, column=0, padx=10, pady=10)

        show_xinfa_skills_button = tk.Button(button_frame, text="展示当前心法技能", command=self.display_xinfa_skills)
        show_xinfa_skills_button.grid(row=1, column=1, padx=10, pady=10)

        reset_button = tk.Button(button_frame, text="重置修为和心法", command=self.reset_cultivation)
        reset_button.grid(row=2, column=0, padx=10, pady=10)

        exit_button = tk.Button(button_frame, text="退出修为系统", command=self.exit_cultivation)
        exit_button.grid(row=2, column=1, padx=10, pady=10)

    def allocate_points_menu(self):
        """ 分配修为点数的界面 """
        elements = ["金", "木", "水", "火", "土"]

        # 创建一个简单的弹窗来分配点数
        def allocate_points(element):
            result = self.cultivation_system.upgrade(element)  # 调用升级逻辑
            self.update_labels()  # 更新修为点的显示
            self.show_result(result)  # 显示升级结果

        allocate_window = tk.Toplevel(self.root)
        allocate_window.title("分配修为点数")
        tk.Label(allocate_window, text=f"剩余培养点: {self.cultivation_system.unused_points}").pack(pady=5)

        for i, element in enumerate(elements):
            button = tk.Button(allocate_window, text=f"提升 {element}", command=lambda e=element: allocate_points(e))
            button.pack(pady=5)

    def choose_xinfa_line_menu(self, custom_names=None):
        xinfa_window = tk.Toplevel(self.root)
        xinfa_window.title("选择心法线")

        tk.Label(xinfa_window, text="请选择心法路线:").pack(pady=10)

        num_lines = len(custom_names) if custom_names else 9

        for i in range(num_lines):
            line_name = custom_names[i] if custom_names and i < len(custom_names) else f"心法线 {i + 1}"
            button = tk.Button(xinfa_window, text=line_name, command=lambda line=i + 1: self.select_xinfa_line(line))
            button.pack(pady=5)

    def select_xinfa_line(self, line):
        """ 选择心法线 """
        self.cultivation_system.select_xinfa_line(line)
        self.display_xinfa_skills()  # 更新心法技能的显示

    def check_xinfa_unlock(self):
        """ 检查心法是否解锁 """
        result = self.cultivation_system.check_xinfa_unlock()  # 调用检查心法解锁的逻辑
        self.show_result(result)

    def display_xinfa_skills(self):
        """ 展示当前心法技能 """
        if not self.cultivation_system.current_xinfa_line:
            self.show_result("该心法暂未制作。")
            return

        result = "\n=== 当前心法线技能 ===\n"
        for level, skill in self.cultivation_system.current_xinfa_line.items():
            skill_status = "已解锁" if level <= self.cultivation_system.current_xinfa_level else "未解锁"
            result += f"心法等级 {level}: {skill.name} ({skill_status})\n"
            result += f"描述: {skill.description}\n" + "-" * 40 + "\n"

        self.show_result(result)

    def reset_cultivation(self):
        """ 重置修为和心法 """
        self.cultivation_system.reset()  # 重置修为系统
        self.update_labels()
        self.show_result("修为和心法已重置。")

    def update_labels(self):
        """ 更新修为点和剩余培养点的显示 """
        self.unused_points_label.config(text=f"剩余培养点: {self.cultivation_system.unused_points}")
        self.cultivation_points_label.config(text=f"修为点: {self.cultivation_system.player.cultivation_point}")

    def show_result(self, result_text):
        """ 在文本框中显示结果 """
        # 确保 result_text 不为 None，并且为字符串
        if result_text:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, str(result_text))  # 确保 result_text 是字符串

    def exit_cultivation(self):
        """ 退出修为系统界面 """
        self.cultivation_frame.destroy()
