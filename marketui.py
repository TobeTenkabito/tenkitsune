import tkinter as tk
from tkinter import messagebox
from common.module.market import Market


class MarketUI:
    def __init__(self, root, player, content_frame):
        self.root = root
        self.player = player
        self.content_frame = content_frame  # 将界面内容放入 content_frame 中
        self.market = Market()  # 假设 Market 是一个已存在的类
        self.current_page = 0
        self.items_per_page = 7  # 每页显示7个物品
        self.items_listbox = None  # 用于存储物品列表的 Listbox

    def start_market_ui(self):
        # 清空 content_frame 中的内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 显示市场物品标题
        title_label = tk.Label(self.content_frame, text="市场", font=("Arial", 18))
        title_label.pack(pady=10)

        # 创建 Listbox，用于显示市场物品
        self.items_listbox = tk.Listbox(self.content_frame, height=10)
        self.items_listbox.pack(pady=10)

        # 显示市场物品
        self.update_items_listbox()

        # 按钮：出售物品、刷新市场、退出
        tk.Button(self.content_frame, text="购买物品", command=lambda: self.buy_item_ui(self.items_listbox)).pack(pady=5)
        tk.Button(self.content_frame, text="出售物品", command=self.sell_item_ui).pack(pady=5)
        tk.Button(self.content_frame, text="刷新市场", command=self.refresh_market).pack(pady=5)

        # 创建分页按钮
        self.create_pagination_buttons()

    def update_items_listbox(self):
        """更新市场物品列表显示"""
        # 清空 Listbox 的内容，而不是重新创建它
        self.items_listbox.delete(0, tk.END)

        # 获取当前页显示的物品
        start_index = self.current_page * self.items_per_page
        end_index = start_index + self.items_per_page
        items_to_display = self.market.items_for_sale[start_index:end_index]

        # 显示物品
        for i, item in enumerate(items_to_display):
            item_name = getattr(item, 'name', '未知物品')
            item_price = getattr(item, 'price', '未知价格')
            # 调用 get_item_color 方法获取对应的颜色
            item_color = self.get_item_color(item.quality)
            # 插入条目
            self.items_listbox.insert(tk.END, f"{i+1}. {item_name} (价格: {item_price})")
            # 设置该条目的颜色
            self.items_listbox.itemconfig(i, {'fg': item_color})

    def refresh_market(self):
        """刷新市场物品，仅更新物品列表框的内容"""
        self.market.items_for_sale = self.market.refresh_market()  # 刷新市场物品
        self.update_items_listbox()  # 只更新物品列表框内容

    def buy_item_ui(self, items_listbox):
        """显示购买物品界面"""
        selected_index = items_listbox.curselection()
        if not selected_index:
            messagebox.showerror("错误", "请先从列表中选择一个物品进行购买。")
            return

        item_index = selected_index[0] + (self.current_page * self.items_per_page)  # 根据分页计算正确的索引
        selected_item = self.market.items_for_sale[item_index]

        buy_window = tk.Toplevel(self.root)
        buy_window.title("购买物品")

        tk.Label(buy_window, text=f"购买物品: {selected_item.name}").pack(pady=5)

        tk.Label(buy_window, text="请输入购买数量:").pack(pady=5)
        quantity_entry = tk.Entry(buy_window)
        quantity_entry.pack(pady=5)

        tk.Button(buy_window, text="购买", command=lambda: self.buy_item(selected_item, quantity_entry)).pack(pady=10)

    def buy_item(self, item, quantity_entry):
        """执行购买物品操作"""
        try:
            quantity = int(quantity_entry.get())
            success, message = self.market.buy_item(self.player, item, quantity)
            messagebox.showinfo("购买结果", message)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数量。")

    def sell_item_ui(self):
        """显示出售物品界面，支持背包翻页和点击选择物品"""
        items_per_page = 10  # 每页显示的物品数量
        current_page = 0
        # 在外部定义输入框变量
        sell_item_number_entry = None
        sell_quantity_entry = None

        def update_item_list():
            nonlocal current_page, sell_item_number_entry, sell_quantity_entry
            # 清除旧的子组件
            for widget in sell_window.winfo_children():
                widget.destroy()

            # 显示标题
            tk.Label(sell_window, text="请选择要出售的物品:").pack(pady=5)

            # 获取当前页的物品
            start_index = current_page * items_per_page
            end_index = start_index + items_per_page
            inventory_items = self.player.inventory[start_index:end_index]

            if inventory_items:
                for i, item in enumerate(inventory_items, start=start_index + 1):
                    item_button = tk.Button(
                        sell_window,
                        text=f"{i}. {item.name} - {item.description}",
                        command=lambda num=i: sell_item_number_entry.delete(0, 'end') or sell_item_number_entry.insert(
                            0, str(num))
                    )
                    item_button.pack(anchor="w")
            else:
                tk.Label(sell_window, text="当前页无物品。").pack()

            # 显示分页按钮
            if current_page > 0:
                tk.Button(sell_window, text="上一页", command=lambda: change_page(-1)).pack(side="left", padx=10)
            if end_index < len(self.player.inventory):
                tk.Button(sell_window, text="下一页", command=lambda: change_page(1)).pack(side="right", padx=10)

            # 创建输入框，每次刷新时重新创建
            tk.Label(sell_window, text="请输入要出售的物品编号:").pack(pady=5)
            sell_item_number_entry = tk.Entry(sell_window)
            sell_item_number_entry.pack(pady=5)

            tk.Label(sell_window, text="请输入要出售的数量:").pack(pady=5)
            sell_quantity_entry = tk.Entry(sell_window)
            sell_quantity_entry.pack(pady=5)

            def sell_item_with_validation():
                try:
                    # 在出售时获取并转换物品编号和数量为整数
                    item_number_entry = int(sell_item_number_entry.get())
                    quantity = int(sell_quantity_entry.get())
                    # 根据输入的物品编号获取物品索引
                    item_number = self.player.get_item_number_by_index(item_number_entry)

                    # 调用出售物品的逻辑
                    self.sell_item(item_number, quantity)
                except ValueError:
                    # 如果转换失败，显示错误消息
                    tk.messagebox.showerror("输入错误", "请输入有效的数字！")

            # 创建出售按钮
            tk.Button(sell_window, text="出售", command=sell_item_with_validation).pack(pady=10)

        def change_page(direction):
            nonlocal current_page
            current_page += direction
            update_item_list()

        # 创建出售窗口
        sell_window = tk.Toplevel(self.root)
        sell_window.title("出售物品")

        # 初始化显示第一页
        update_item_list()

    def sell_item(self, item_number_entry, quantity_entry):
        """执行出售物品操作"""
        try:
            item_number = item_number_entry
            quantity = quantity_entry
            item = self.player.get_inventory_item(item_number)
            if item:
                success, message = self.market.sell_item(self.player, item, quantity)
                messagebox.showinfo("出售结果", message)
            else:
                messagebox.showerror("错误", "背包中没有该物品。")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的编号和数量。")

    def create_pagination_buttons(self):
        """创建分页按钮"""
        button_frame = tk.Frame(self.content_frame)
        button_frame.pack(pady=5)

        if self.current_page > 0:
            prev_button = tk.Button(button_frame, text="上一页", command=self.previous_page)
            prev_button.pack(side="left", padx=5)

        if (self.current_page + 1) * self.items_per_page < len(self.market.items_for_sale):
            next_button = tk.Button(button_frame, text="下一页", command=self.next_page)
            next_button.pack(side="right", padx=5)

    def previous_page(self):
        """显示上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_items_listbox()

    def next_page(self):
        """显示下一页"""
        if (self.current_page + 1) * self.items_per_page < len(self.market.items_for_sale):
            self.current_page += 1
            self.update_items_listbox()

    def get_item_color(self, quality):
        """根据物品品质返回颜色"""
        color_mapping = {
            "优秀": "green",
            "精良": "blue",
            "史诗": "purple",
            "传说": "orange",
            "神器": "red"
        }
        return color_mapping.get(quality, "black")  # 默认黑色