import tkinter as tk
from tkinter import messagebox


class LotteryUI:
    def __init__(self, root, player, content_frame, lottery_pool):
        self.root = root
        self.player = player
        self.content_frame = content_frame  # 将 UI 嵌入到 content_frame
        self.lottery_pool = lottery_pool

    def start_lottery_ui(self):
        # 清空 content_frame 中的内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 显示抽奖界面标题
        title_label = tk.Label(self.content_frame, text="抽奖系统", font=("Arial", 18))
        title_label.pack(pady=10)

        # 按钮：单次抽奖、十连抽、百连抽
        tk.Button(self.content_frame, text="单次抽奖", command=lambda: self.perform_lottery(1)).pack(pady=5)
        tk.Button(self.content_frame, text="十连抽奖", command=lambda: self.perform_lottery(10)).pack(pady=5)
        tk.Button(self.content_frame, text="百连抽奖", command=lambda: self.perform_lottery(100)).pack(pady=5)

        # 抽奖结果显示区域
        self.result_text = tk.Text(self.content_frame, height=10, width=50)
        self.result_text.pack(pady=10)

    def perform_lottery(self, draw_count):
        """执行指定数量的抽奖"""
        if draw_count == 1:
            quantity_to_use = 1
        elif draw_count == 10:
            quantity_to_use = 10
        elif draw_count == 100:
            quantity_to_use = 100
        else:
            messagebox.showerror("错误", "无效的抽奖数量。")
            return

        # 检查是否有足够的抽奖材料
        if not self.player.decrease_material_quantity(120000, quantity_to_use):
            messagebox.showerror("错误", "抽奖材料不足，无法进行抽奖。")
            return

        self.result_text.delete(1.0, tk.END)  # 清空之前的内容

        lottery = self.lottery_pool
        results = lottery.draw(draw_count)

        result_str = f"消耗了 {quantity_to_use} 个 北斗白石。\n"
        for reward, probability in results:
            if reward:  # 如果是有效的物品
                self.player.add_to_inventory(reward)  # 添加物品到背包
                result_str += f"获得: {reward.name}\n"

        # 在界面上显示抽奖结果
        self.result_text.insert(tk.END, result_str)