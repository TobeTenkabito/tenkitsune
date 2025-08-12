import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from functools import partial
from common.module.item import Skill, Equipment, Warp, Medicine


class BagUI:
    def __init__(self, player, content_frame):
        self.player = player
        self.content_frame = content_frame  # 接受主界面传入的content_frame用来显示背包内容
        self.current_page = 0
        self.items_per_page = 7

    def show_bag_interface(self):
        self.clear_content_frame()  # 清除当前窗口的内容
        title_label = tk.Label(self.content_frame, text="====== 玩家背包界面 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        # 创建操作按钮
        equipment_button = tk.Button(self.content_frame, text="查看装备栏", command=self.display_equipment, width=20)
        skills_button = tk.Button(self.content_frame, text="查看技能栏", command=self.display_skills, width=20)
        inventory_button = tk.Button(self.content_frame, text="查看背包栏", command=self.display_inventory, width=20)
        equip_button = tk.Button(self.content_frame, text="装备/卸下装备", command=self.manage_equipment, width=20)
        skill_button = tk.Button(self.content_frame, text="装备/卸下技能", command=self.manage_skills, width=20)
        research_button = tk.Button(self.content_frame, text="查找物品", command=self.research_item, width=20)
        sort_button = tk.Button(self.content_frame, text="背包整理", command=self.sort_item, width=20)

        # 将按钮排列在content_frame中
        equipment_button.pack(pady=5)
        skills_button.pack(pady=5)
        inventory_button.pack(pady=5)
        equip_button.pack(pady=5)
        skill_button.pack(pady=5)
        research_button.pack(pady=5)
        sort_button.pack(pady=5)

    def display_inventory(self):
        """显示背包中的物品，支持分页"""
        self.clear_content_frame()
        title_label = tk.Label(self.content_frame, text="====== 玩家背包 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        # 获取当前页要展示的物品
        start_index = self.current_page * self.items_per_page
        end_index = start_index + self.items_per_page
        items_to_display = self.player.inventory[start_index:end_index]

        if items_to_display:
            for item in items_to_display:
                item_color = self.get_item_color(item.quality)
                item_button = tk.Button(self.content_frame, text=f"{item.name} - {item.quantity}",
                                        command=partial(self.select_item, item), fg=item_color)
                item_button.pack(anchor="w", pady=5)
        else:
            empty_label = tk.Label(self.content_frame, text="背包为空。")
            empty_label.pack()

        # 分页按钮
        self.create_pagination_buttons()

    def create_pagination_buttons(self):
        button_frame = tk.Frame(self.content_frame)
        button_frame.pack(pady=5)

        if self.current_page > 0:
            prev_button = tk.Button(button_frame, text="上一页", command=self.previous_page)
            prev_button.pack(side="left", padx=5)

        if (self.current_page + 1) * self.items_per_page < len(self.player.inventory):
            next_button = tk.Button(button_frame, text="下一页", command=self.next_page)
            next_button.pack(side="right", padx=5)

        back_button = tk.Button(button_frame, text="返回", command=self.show_bag_interface)
        back_button.pack(pady=5)

    def select_item(self, item):
        """选择物品并显示详细信息和使用按钮"""
        self.clear_content_frame()
        title_label = tk.Label(self.content_frame, text=f"选择的物品: {item.name}", font=("Arial", 16))
        title_label.pack(pady=10)

        # 显示物品详细信息
        details_label = tk.Label(self.content_frame, text=f"描述: {item.description}\n品质: {item.quality}\n数量: {item.quantity}")
        details_label.pack(pady=5)

        if isinstance(item, Equipment):
            combat_stats = (f"生命：{item.hp}\n法力：{item.mp}\n攻击: {item.attack}\n"
                            f"防御: {item.defense}\n速度: {item.speed}\n"
                            f"暴击: {item.crit}\n暴击伤害: {item.crit_damage}\n"
                            f"抗性: {item.resistance}\n穿透: {item.penetration}")
            stats_label = tk.Label(self.content_frame, text=combat_stats)
            stats_label.pack(pady=5)

        use_button = tk.Button(self.content_frame, text="使用", command=partial(self.use_item, item))
        use_button.pack(pady=5)

        back_button = tk.Button(self.content_frame, text="返回", command=self.display_inventory)
        back_button.pack(pady=5)

    def use_item(self, item):
        if isinstance(item, Warp):
            item.use(self.player)
            self.display_inventory()
        elif isinstance(item, Medicine):
            item.use(self.player)
            self.display_inventory()
        elif isinstance(item, Skill):
            if len(self.player.skills) < 9:  # 假设技能栏最大为9个
                self.player.skills.append(item)
                self.player.inventory.remove(item)
                messagebox.showinfo("装备成功", f"装备了技能 {item.name}。")
                self.display_inventory()
            else:
                messagebox.showerror("技能栏已满", "技能栏已满，无法装备新技能。")
        elif isinstance(item, Equipment):
            self.equip_selected_item(item)
        else:
            messagebox.showinfo("提示", f"{item.name} 不支持在背包界面使用。")

    def next_page(self):
        """下一页"""
        if (self.current_page + 1) * self.items_per_page < len(self.player.inventory):
            self.current_page += 1
            self.display_inventory()

    def previous_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.display_inventory()

    def display_equipment(self):
        self.clear_content_frame()  # 清空内容框架，确保旧组件被移除

        # 创建 Canvas 和包含滚动条的框架
        canvas = tk.Canvas(self.content_frame)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        # 绑定 Frame 以调整滚动区域
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 添加标题
        title_label = tk.Label(scrollable_frame, text="====== 玩家装备栏 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        # 定义栏目
        columns = {
            "武器": "武器栏",
            "防具": "防具栏",
            "饰品": "饰品栏",
            "法宝": "法宝栏"
        }

        # 遍历并显示每个栏目
        for category, label_text in columns.items():
            category_label = tk.Label(scrollable_frame, text=f"{label_text}:", font=("Arial", 14, "bold"))
            category_label.pack(anchor="w", pady=(10, 5))

            # 获取当前类别的装备
            items = [item for item in self.player.equipment if item.category == category]
            if items:
                for i, item in enumerate(items, 1):
                    item_color = self.get_item_color(item.quality)  # 获取物品颜色

                    # 创建装备按钮
                    item_button = tk.Button(
                        scrollable_frame,
                        text=f"{i}. {item.name}",
                        fg=item_color,
                        command=lambda itm=item: self.unequip_selected_item(itm)
                    )
                    item_button.pack(anchor="w")

                    # 添加装备的详细属性文本
                    combat_stats = (f"简介：{item.description}"
                                    f"\n生命：{item.hp} | 法力：{item.mp} | 攻击: {item.attack} | 防御: {item.defense} | "
                                    f"速度: {item.speed} | 暴击: {item.crit} | 暴击伤害: {item.crit_damage} | "
                                    f"抗性: {item.resistance} | 穿透: {item.penetration}")

                    stats_label = tk.Label(
                        scrollable_frame,
                        text=combat_stats,
                        fg=item_color  # 可以保持一致的颜色，或选择不同颜色
                    )
                    stats_label.pack(anchor="w")
            else:
                empty_label = tk.Label(scrollable_frame, text="(空)", fg="gray")
                empty_label.pack(anchor="w")

        # 布局滚动条和 Canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 添加返回按钮
        back_button = tk.Button(scrollable_frame, text="返回", command=self.show_bag_interface)
        back_button.pack(pady=10)

    def display_skills(self):
        self.clear_content_frame()  # 确保旧组件被清理

        # 创建 Canvas 和包含滚动条的框架
        canvas = tk.Canvas(self.content_frame)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        # 绑定 Frame 以调整滚动区域
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 添加标题
        title_label = tk.Label(scrollable_frame, text="====== 玩家技能栏 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        # 获取技能列表，限制最多显示 9 个
        max_skills = 9
        skills_to_display = self.player.skills[:max_skills]

        if skills_to_display:
            for i, skill in enumerate(skills_to_display, 1):
                skill_color = self.get_item_color(skill.quality)  # 获取技能颜色

                # 创建技能按钮用于卸下技能
                skill_button = tk.Button(
                    scrollable_frame,
                    text=f"{i}. {skill.name} - {skill.description}",
                    fg=skill_color,
                    command=lambda skl=skill: self.unequip_selected_skill(skl)
                )
                skill_button.pack(anchor="w")
        else:
            empty_label = tk.Label(scrollable_frame, text="技能栏为空。")
            empty_label.pack()

        # 布局滚动条和 Canvas
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 添加返回按钮
        back_button = tk.Button(scrollable_frame, text="返回", command=self.show_bag_interface)
        back_button.pack(pady=10)

    def manage_equipment(self):
        self.clear_content_frame()
        title_label = tk.Label(self.content_frame, text="====== 装备管理 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        # 装备和卸下装备的按钮
        equip_button = tk.Button(self.content_frame, text="装备物品", command=self.equip_item, width=20)
        unequip_button = tk.Button(self.content_frame, text="卸下物品", command=self.unequip_item, width=20)
        back_button = tk.Button(self.content_frame, text="返回", command=self.show_bag_interface, width=20)

        equip_button.pack(pady=5)
        unequip_button.pack(pady=5)
        back_button.pack(pady=5)

    def manage_skills(self):
        self.clear_content_frame()
        title_label = tk.Label(self.content_frame, text="====== 技能管理 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        equip_button = tk.Button(self.content_frame, text="装备技能", command=self.equip_skill, width=20)
        unequip_button = tk.Button(self.content_frame, text="卸下技能", command=self.unequip_skill, width=20)
        back_button = tk.Button(self.content_frame, text="返回", command=self.show_bag_interface, width=20)

        equip_button.pack(pady=5)
        unequip_button.pack(pady=5)
        back_button.pack(pady=5)

    def equip_item(self):
        self.clear_content_frame()

        title_label = tk.Label(self.content_frame, text="====== 装备物品 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        # 获取装备物品列表
        equipment_items = [item for item in self.player.inventory if isinstance(item, Equipment)]
        if not equipment_items:
            empty_label = tk.Label(self.content_frame, text="背包中没有可装备的物品。")
            empty_label.pack()
            return_button = tk.Button(self.content_frame, text="返回", command=self.manage_equipment)
            return_button.pack(pady=10)
            return

        # 使用 partial 传递参数给回调函数
        for i, item in enumerate(equipment_items, 1):
            item_color = self.get_item_color(item.quality)  # 获取物品颜色
            item_button = tk.Button(self.content_frame, text=f"{i}. {item.name} - {item.description}",
                                    command=partial(self.equip_selected_item, item), fg=item_color)
            item_button.pack(anchor="w", pady=5)

        # 添加返回按钮
        back_button = tk.Button(self.content_frame, text="返回", command=self.manage_equipment)
        back_button.pack(pady=10)

    def equip_selected_item(self, item):
        # 检查装备限制
        equipment_types = {"武器": 0, "防具": 0, "饰品": 0, "法宝": 0}
        for eq in self.player.equipment:
            if eq.category in equipment_types:
                equipment_types[eq.category] += 1

        if item.category in ["武器", "防具", "饰品"] and equipment_types[item.category] >= 1:
            messagebox.showerror("装备失败", f"{item.category} 已经装备，无法再装备 {item.name}。")
            return
        elif item.category == "法宝" and equipment_types["法宝"] >= 3:
            messagebox.showerror("装备失败", "法宝数量已达上限，无法再装备。")
            return

        # 装备物品
        self.player.equipment.append(item)
        item.apply_attributes(self.player)
        self.player.inventory.remove(item)
        self.player.update_stats()
        self.equip_item()

    def unequip_item(self):
        self.clear_content_frame()

        title_label = tk.Label(self.content_frame, text="====== 卸下装备 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        if not self.player.equipment:
            empty_label = tk.Label(self.content_frame, text="你没有装备任何物品。")
            empty_label.pack()
            return_button = tk.Button(self.content_frame, text="返回", command=self.manage_equipment)
            return_button.pack(pady=10)
            return

        # 显示当前装备的物品
        for i, item in enumerate(self.player.equipment, 1):
            item_button = tk.Button(self.content_frame, text=f"{i}. {item.name} - {item.description}",
                                    command=partial(self.unequip_selected_item, item))
            item_button.pack(anchor="w", pady=5)

        # 添加返回按钮
        back_button = tk.Button(self.content_frame, text="返回", command=self.manage_equipment)
        back_button.pack(pady=10)

    def unequip_selected_item(self, item):
        item.remove_attributes(self.player)
        self.player.equipment.remove(item)
        self.player.inventory.append(item)
        messagebox.showinfo("卸下成功", f"卸下了 {item.name}。")
        self.manage_equipment()

    def equip_skill(self):
        self.clear_content_frame()

        title_label = tk.Label(self.content_frame, text="====== 装备技能 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        available_skills = [item for item in self.player.inventory if isinstance(item, Skill)]
        if not available_skills:
            empty_label = tk.Label(self.content_frame, text="背包中没有可装备的技能。")
            empty_label.pack()
            return_button = tk.Button(self.content_frame, text="返回", command=self.manage_skills)
            return_button.pack(pady=10)
            return

        # 显示可装备的技能
        for i, skill in enumerate(available_skills, 1):
            skill_color = self.get_item_color(skill.quality)  # 获取技能颜色
            skill_button = tk.Button(self.content_frame, text=f"{i}. {skill.name} - {skill.description}",
                                     command=partial(self.equip_selected_skill, skill), fg=skill_color)
            skill_button.pack(anchor="w", pady=5)

        # 添加返回按钮
        back_button = tk.Button(self.content_frame, text="返回", command=self.manage_skills)
        back_button.pack(pady=10)

    def equip_selected_skill(self, skill):
        if len(self.player.skills) >= 9:
            messagebox.showerror("技能栏已满", "技能栏已满，无法再装备新的技能。")
            return

        self.player.skills.append(skill)
        self.player.inventory.remove(skill)
        self.equip_skill()

    def unequip_skill(self):
        """卸下技能并返回到背包"""
        self.clear_content_frame()

        title_label = tk.Label(self.content_frame, text="====== 卸下技能 ======", font=("Arial", 16))
        title_label.pack(pady=10)

        if not self.player.skills:
            empty_label = tk.Label(self.content_frame, text="你没有装备任何技能。")
            empty_label.pack()
            return_button = tk.Button(self.content_frame, text="返回", command=self.manage_skills)
            return_button.pack(pady=10)
            return

        # 显示当前装备的技能
        for i, skill in enumerate(self.player.skills, 1):
            skill_button = tk.Button(self.content_frame, text=f"{i}. {skill.name} - {skill.description}",
                                     command=partial(self.unequip_selected_skill, skill))
            skill_button.pack(anchor="w", pady=5)

        # 添加返回按钮
        back_button = tk.Button(self.content_frame, text="返回", command=self.manage_skills)
        back_button.pack(pady=10)

    def unequip_selected_skill(self, skill):
        """选择的技能进行卸下"""
        self.player.skills.remove(skill)
        self.player.inventory.append(skill)
        messagebox.showinfo("卸下成功", f"卸下了技能 {skill.name}。")
        self.manage_skills()

    def research_item(self):
        research_window = tk.Toplevel(self.content_frame)
        research_window.title("查找物品")
        research_window.geometry("300x300")

        tk.Label(research_window, text="输入名称").grid(row=0, column=0, padx=5, pady=5)
        item_name_entry = tk.Entry(research_window)
        item_name_entry.grid(row=0, column=1, padx=5, pady=5)

        # Label for displaying results
        result_label = tk.Label(research_window, text="搜索结果:")
        result_label.grid(row=2, columnspan=2, pady=10)

        # Text widget to display results
        results_text = tk.Text(research_window, height=10, width=30, state='disabled')
        results_text.grid(row=3, columnspan=2, padx=5, pady=5)

        def search_items():
            search_text = item_name_entry.get().strip()
            if not search_text:
                messagebox.showwarning("警告", "请输入搜索内容")
                return

            exact_matches = []
            fuzzy_matches = []

            for item in self.player.inventory:
                if item.name == search_text:
                    exact_matches.append(item)
                elif search_text in item.name:
                    fuzzy_matches.append(item)

            # Combine and prioritize matches
            results = exact_matches + sorted(fuzzy_matches, key=lambda x: x.name)

            # Update the results in the text widget
            results_text.config(state='normal')  # Enable editing to insert text
            results_text.delete(1.0, tk.END)  # Clear previous results

            if results:
                for idx, result in enumerate(results):
                    results_text.insert(tk.END, result.name + '\n')
                    # Use the current line index to create a tag
                    results_text.tag_add(result.name, f"{idx + 1}.0", f"{idx + 1}.end")
                    results_text.tag_config(result.name, foreground="blue")  # Color the item names

                    # Bind the click event to select the item
                    results_text.bind(f"<Button-1>", lambda event, item=result: self.select_item(item))
            else:
                results_text.insert(tk.END, "未找到匹配项\n")

            results_text.config(state='disabled')  # Disable editing again

        search_button = tk.Button(research_window, text="搜索", command=search_items)
        search_button.grid(row=1, columnspan=2, pady=10)

    def sort_item(self):
        """选择排序方式并整理背包"""
        # 创建弹窗以选择排序方式
        sort_window = tk.Toplevel(self.content_frame)
        sort_window.title("选择排序方式")
        sort_window.geometry("200x300")

        tk.Label(sort_window, text="请选择排序依据：", font=("Arial", 12)).pack(pady=5)

        # 选择排序依据
        sort_criterion = tk.StringVar(value="quality")
        tk.Radiobutton(sort_window, text="按品质", variable=sort_criterion, value="quality").pack()
        tk.Radiobutton(sort_window, text="按价格", variable=sort_criterion, value="price").pack()
        tk.Radiobutton(sort_window, text="按数量", variable=sort_criterion, value="quantity").pack()

        # 选择升序或降序
        sort_order = tk.BooleanVar(value=False)
        tk.Label(sort_window, text="选择排序顺序：", font=("Arial", 12)).pack(pady=5)
        tk.Radiobutton(sort_window, text="升序", variable=sort_order, value=False).pack()
        tk.Radiobutton(sort_window, text="降序", variable=sort_order, value=True).pack()

        def perform_sort():
            criterion = sort_criterion.get()
            reverse = sort_order.get()
            quality_order = {"神器": 5, "传说": 4, "史诗": 3, "精良": 2, "优秀": 1, "普通": 0}

            def get_sort_key(item):
                if criterion == "quality":
                    return quality_order.get(item.quality, -1)  # 使用品质的权重排序
                elif criterion == "price":
                    return item.price
                elif criterion == "quantity":
                    return item.quantity
                else:
                    return 0

            # 按选定依据和顺序对背包排序
            self.player.inventory.sort(key=get_sort_key, reverse=reverse)
            print(f"背包已按 {criterion}（{'降序' if reverse else '升序'}）整理完成")
            messagebox.showinfo("排序完成", f"背包已按 {criterion}（{'降序' if reverse else '升序'}）整理完成")

            # 关闭弹窗并更新显示
            sort_window.destroy()
            self.display_inventory()

        tk.Button(sort_window, text="确认排序", command=perform_sort).pack(pady=10)

    def clear_content_frame(self):
        """清空content_frame中的所有内容"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

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

