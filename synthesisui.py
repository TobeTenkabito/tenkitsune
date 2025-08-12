import tkinter as tk
from tkinter import messagebox, simpledialog
from common.module.item import Material, Equipment
from common.module.synthesis import synthesize, get_synthesis_result, get_available_synthesis_targets
from library.material_library import material_library
from library.equipment_library import equipment_library
from library.medicine_library import medicine_library
from library.product_library import product_library
from all.synthesis_recipes import synthesis_recipes


class SynthesisUI:
    def __init__(self, root, player, content_frame):
        self.root = root
        self.player = player
        self.content_frame = content_frame  # 将界面内容放入 content_frame 中
        self.target_material_number = None
        self.material_buttons = []
        self.synthesis_slots = [None, None, None]  # 默认3个合成栏位

    def start_synthesis_ui(self):
        # 清空内容框架
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 显示合成槽位信息
        self.update_synthesis_slots()

        # 按钮：选择要合成的物品
        tk.Button(self.content_frame, text="选择要合成的物品", command=self.choose_synthesis_target_ui).pack(pady=5)

        # 按钮：选择材料
        tk.Button(self.content_frame, text="选择栏位 1 的材料", command=lambda: self.choose_material_ui(0)).pack(pady=5)
        tk.Button(self.content_frame, text="选择栏位 2 的材料", command=lambda: self.choose_material_ui(1)).pack(pady=5)
        tk.Button(self.content_frame, text="选择栏位 3 的材料", command=lambda: self.choose_material_ui(2)).pack(pady=5)

        # 按钮：执行合成
        tk.Button(self.content_frame, text="执行合成", command=self.perform_synthesis).pack(pady=10)

    def update_synthesis_slots(self):
        """更新界面上的合成槽位显示"""
        for i in range(3):
            if self.synthesis_slots[i]:
                slot_text = f"栏位 {i + 1}: {self.synthesis_slots[i].name} x {self.synthesis_slots[i].quantity}"
            else:
                slot_text = f"栏位 {i + 1}: 空"

            # 如果没有该栏位的标签，创建它
            if len(self.material_buttons) <= i:
                btn = tk.Label(self.content_frame, text=slot_text)
                btn.pack(pady=5)
                self.material_buttons.append(btn)
            else:
                # 更新现有的槽位标签
                self.material_buttons[i].config(text=slot_text)

    def choose_material_ui(self, slot_index):
        """选择材料的UI界面"""
        material_window = tk.Toplevel(self.root)
        material_window.title(f"选择栏位 {slot_index + 1} 的材料")
        material_window.geometry("400x300")

        inventory_dict = {i: item for i, item in enumerate(self.player.inventory)}

        def select_material():
            choice = material_listbox.curselection()
            if not choice:
                messagebox.showerror("错误", "请选择一个材料。")
                return

            material_index = choice[0]
            material = inventory_dict[material_index]

            if isinstance(material, Material):
                quantity = int(quantity_entry.get())
                if 1 <= quantity <= material.quantity:
                    material_copy = Material(material.number, material.name, material.description, material.quality,
                                             material.price, quantity)
                    self.player.set_synthesis_slot(slot_index, material_copy)
                    self.synthesis_slots[slot_index] = material_copy
                    self.update_synthesis_slots()
                    material_window.destroy()
                else:
                    messagebox.showerror("错误", "无效的数量。")
            else:
                messagebox.showerror("错误", "请选择有效的材料。")

        tk.Label(material_window, text="请选择一个材料:").pack(pady=5)
        material_listbox = tk.Listbox(material_window)
        material_listbox.pack(pady=10)

        # 显示背包中的物品
        for i, item in enumerate(inventory_dict.values()):
            material_listbox.insert(tk.END, f"{i + 1}. {item.name} x {item.quantity}")

        tk.Label(material_window, text="请输入数量:").pack(pady=5)
        quantity_entry = tk.Entry(material_window)
        quantity_entry.pack(pady=5)

        tk.Button(material_window, text="确认", command=select_material).pack(pady=10)

    def choose_synthesis_target_ui(self):
        """选择要合成的目标物品的UI界面"""
        target_window = tk.Toplevel(self.root)
        target_window.title("选择要合成的物品")
        target_window.geometry("400x300")

        available_targets = get_available_synthesis_targets(self.player)

        if not available_targets:
            messagebox.showinfo("无效", "当前没有可合成的物品。")
            target_window.destroy()
            return

        def select_target():
            choice = target_listbox.curselection()
            if not choice:
                messagebox.showerror("错误", "请选择一个物品。")
                return

            target_index = choice[0]
            self.target_material_number = available_targets[target_index]
            self.set_required_materials()
            target_window.destroy()

        tk.Label(target_window, text="请选择要合成的物品:").pack(pady=5)
        target_listbox = tk.Listbox(target_window)
        target_listbox.pack(pady=10)

        # 显示可合成的物品
        for i, target_material_number in enumerate(available_targets):
            item = get_synthesis_result(target_material_number)
            required_materials_str = ", ".join(
                [f"{get_material_name(material_number)} x {quantity}" for material_number, quantity in
                 synthesis_recipes[target_material_number]["materials"].items()])
            target_listbox.insert(tk.END, f"{i + 1}. {item.name} - 需要材料: {required_materials_str}")

        tk.Button(target_window, text="确认", command=select_target).pack(pady=10)

    def set_required_materials(self):
        """根据所选目标自动填充所需材料"""
        if self.target_material_number:
            required_materials = synthesis_recipes[self.target_material_number]["materials"]
            for slot_index, (material_number, quantity) in enumerate(required_materials.items()):
                material = get_material_object(material_number)
                if material is None:
                    raise KeyError(f"编号 {material_number} 不存在于任何已知的物品库中")

                # 根据对象类型创建副本
                if isinstance(material, Material):
                    material_copy = Material(material.number, material.name, material.description, material.quality,
                                             material.price, quantity)
                elif isinstance(material, Equipment):
                    # 添加 category 参数
                    material_copy = Equipment(
                        material.number, material.name, material.description, material.quality, material.category,
                        material.price, quantity,
                        getattr(material, 'hp', 0), getattr(material, 'mp', 0), getattr(material, 'attack', 0),
                        getattr(material, 'defense', 0), getattr(material, 'speed', 0),
                        getattr(material, 'crit', 0), getattr(material, 'crit_damage', 0),
                        getattr(material, 'resistance', 0), getattr(material, 'penetration', 0)
                    )
                else:
                    raise TypeError(f"无法识别的材料类型: {type(material)}")

                self.player.set_synthesis_slot(slot_index, material_copy)
                self.synthesis_slots[slot_index] = material_copy
            self.update_synthesis_slots()

    def perform_synthesis(self):
        """执行合成操作"""
        if not self.target_material_number:
            messagebox.showerror("错误", "请先选择要合成的物品。")
            return

        max_quantity = min(self.player.get_material_quantity(material_number) // quantity
                           for material_number, quantity in
                           synthesis_recipes[self.target_material_number]["materials"].items())

        synthesis_quantity = simpledialog.askinteger("合成数量", f"请输入要合成的数量 (最多 {max_quantity}): ")

        if synthesis_quantity is None:
            return  # 用户取消输入

        if 1 <= synthesis_quantity <= max_quantity:
            success, message = synthesize(self.player, self.target_material_number, synthesis_quantity)
            messagebox.showinfo("合成结果", message)
        else:
            messagebox.showerror("错误", "无效的合成数量。")


def get_material_name(material_number):
    if material_number in material_library:
        return material_library[material_number].name
    elif material_number in equipment_library:
        return equipment_library[material_number].name
    elif material_number in medicine_library:
        return medicine_library[material_number].name
    elif material_number in product_library:
        return product_library[material_number].name
    else:
        return f"未知物品({material_number})"


def get_material_object(material_number):
    """从不同库中获取材料对象"""
    if material_number in material_library:
        return material_library[material_number]
    elif material_number in equipment_library:
        return equipment_library[material_number]
    elif material_number in medicine_library:
        return medicine_library[material_number]
    elif material_number in product_library:
        return product_library[material_number]
    else:
        return None