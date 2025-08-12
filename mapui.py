from PIL import Image, ImageTk
import os
import tkinter as tk
from tkinter import ttk
import random
import copy
from tkinter import messagebox
from functools import partial
from common.ui.battleui import BattleUI
from common.ui.dungeonui import DungeonUI
from common.ui.npcui import NPCUI
import threading


class MapUI:
    def __init__(self, root, player, content_frame, game_state):
        self.root = root
        self.player = player
        self.content_frame = content_frame
        self.game_state = game_state
        self.page_stack = []
        self.current_map = None
        self.map_image_label = None

    def __del__(self):
        """销毁 MapUI 实例时解除滚动绑定"""
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.unbind("<MouseWheel>")
            self.canvas.destroy()
        if hasattr(self, 'scrollbar') and self.scrollbar:
            self.scrollbar.destroy()

    def show_map_ui(self, map_object):
        """显示地图主界面"""
        # 将当前界面压入栈中，便于返回
        self.page_stack.append(partial(self.show_map_ui, map_object))
        self.current_map = map_object
        self.clear_content_frame()
        # 创建带滚动条的框架
        scrollable_frame = self.create_scrollable_frame()

        # 显示地图名称和描述
        tk.Label(scrollable_frame, text=f"当前地图: {map_object.name}", font=("Arial", 18)).pack(pady=10)
        tk.Label(scrollable_frame, text=map_object.description, wraplength=500).pack(pady=5)

        # 此处显示地图图片
        image_path = f"resources/map/{map_object.number}.png"
        if os.path.exists(image_path):
            map_image = Image.open(image_path)
            map_image = map_image.resize((400, 300), Image.LANCZOS)  # 调整图像大小
            map_photo = ImageTk.PhotoImage(map_image)
            self.map_image_label = tk.Label(scrollable_frame, image=map_photo)
            self.map_image_label.image = map_photo  # 保持引用，防止图片被垃圾回收
            self.map_image_label.pack(pady=10)
        else:
            print(f"未找到地图图片: {image_path}")

        # 显示地图功能按钮
        tk.Button(scrollable_frame, text="谈天说地", command=self.show_npcs).pack(pady=5)
        tk.Button(scrollable_frame, text="采集物品", command=self.show_collectibles).pack(pady=5)
        tk.Button(scrollable_frame, text="清理野怪", command=self.show_battles).pack(pady=5)
        tk.Button(scrollable_frame, text="探索秘境", command=self.show_dungeons).pack(pady=5)
        tk.Button(scrollable_frame, text="离开此地", command=self.show_adjacent_maps).pack(pady=5)
        # 返回按钮
        tk.Button(scrollable_frame, text="返回", command=self.go_back).pack(pady=10)

    def show_npcs(self):
        """显示 NPC 界面"""
        self.clear_content_frame()

        # 首先自动移除已被标记为死亡的 NPC
        self.remove_killed_npcs()

        scrollable_frame = self.create_scrollable_frame()

        if self.current_map.npcs:
            tk.Label(scrollable_frame, text="此地图上的 NPC:", font=("Arial", 14)).pack(pady=10)
            for i, npc in enumerate(self.current_map.npcs):
                tk.Button(scrollable_frame, text=f"{npc.name}: {npc.description}",
                          command=lambda n=npc: self.interact_with_npc(n)).pack(pady=5)
        else:
            tk.Label(scrollable_frame, text="此地图上没有 NPC。", font=("Arial", 14)).pack(pady=10)

        tk.Button(scrollable_frame, text="返回", command=self.go_back).pack(pady=10)

    def remove_killed_npcs(self):
        """移除已经被玩家杀死的 NPC"""
        # 移除当前地图中的 NPC 如果他们在 player.npcs_removed 列表中
        self.current_map.npcs = [npc for npc in self.current_map.npcs if npc.number not in self.player.npcs_removed]

    def interact_with_npc(self, npc):
        """与选定的 NPC 互动"""
        self.clear_content_frame()
        NPCUI(self.content_frame, npc, self.player, self.go_back)

    def show_collectibles(self):
        """显示采集物品界面"""
        self.clear_content_frame()

        scrollable_frame = self.create_scrollable_frame()

        if self.current_map.collectible_items:
            tk.Label(scrollable_frame, text="此地图上的可采集物品:", font=("Arial", 14)).pack(pady=10)
            for i, item in enumerate(self.current_map.collectible_items):
                tk.Button(scrollable_frame, text=f"{item.name}", command=lambda it=item: self.collect_item(it)).pack(pady=5)
        else:
            tk.Label(scrollable_frame, text="此地图上没有可采集的物品。", font=("Arial", 14)).pack(pady=10)

        tk.Button(scrollable_frame, text="返回", command=self.go_back).pack(pady=10)

    def collect_item(self, item):
        """采集选定的物品"""
        self.clear_content_frame()
        # 从地图中获取当前物品的采集信息
        item_info = self.current_map.collectible_items.get(item)

        if not item_info:
            # 若当前物品不在地图的采集物品列表中
            messagebox.showwarning("无法采集", f"{item.name} 不在此地图可采集的物品列表中。")
            self.go_back()
            return

        success_rate = item_info["success_rate"]
        quantity_range = item_info["quantity_range"]

        # 生成采集成功或失败的消息
        if random.uniform(0, 1) <= success_rate:
            if isinstance(quantity_range, tuple):
                quantity = random.randint(quantity_range[0], quantity_range[1])
            else:
                quantity = quantity_range
            success_message = f"成功采集到 {item.name} x {quantity}！"
            collected_item = copy.deepcopy(item)
            collected_item.quantity = quantity
            self.player.add_to_inventory(collected_item)
            tk.Label(self.content_frame, text=success_message, font=("Arial", 14)).pack(pady=10)
        else:
            # 采集失败
            fail_message = f"采集 {item.name} 失败。"
            tk.Label(self.content_frame, text=fail_message, font=("Arial", 14)).pack(pady=10)

        # 返回按钮
        tk.Button(self.content_frame, text="返回", command=self.show_collectibles).pack(pady=10)

    def show_battles(self):
        """显示地图中的战斗场景，并允许玩家选择战斗"""
        self.clear_content_frame()
        scrollable_frame = self.create_scrollable_frame()

        # 显示提示文本
        tk.Label(scrollable_frame, text="请选择战斗场景：", font=("Arial", 14)).pack(pady=10)

        # 遍历当前地图中的战斗实例
        for i, battle_instance in enumerate(self.current_map.battles):
            # 获取每个战斗实例中的敌人名称
            enemy_names = [enemy.name for enemy in battle_instance]
            enemies_text = ", ".join(enemy_names)  # 将敌人名称组合成一个字符串

            # 创建按钮，并显示战斗实例的敌人名称
            tk.Button(scrollable_frame, text=f"战斗场景 {i + 1}: {enemies_text}",
                      command=lambda b=battle_instance: self.start_battle(b)).pack(pady=5)

        # 添加返回按钮
        tk.Button(scrollable_frame, text="返回", command=self.go_back).pack(pady=10)

    def start_battle(self, enemies):
        print(f"敌人列表: {enemies}")
        BattleUI(self.root, self.player, [], enemies, self.on_battle_end)

    def on_battle_end(self, result):
        """战斗结束后的回调处理"""
        if result == "victory":
            messagebox.showinfo("战斗胜利", "你已经赢得了战斗！")
        elif result == "defeat":
            if self.current_map:
                messagebox.showinfo("战斗失败", f"{self.current_map.handle_monster_defeat(self.player)}")

        self.show_battles()

    def show_dungeons(self):
        """显示秘境界面"""
        self.clear_content_frame()
        scrollable_frame = self.create_scrollable_frame()
        if self.current_map.dungeons:
            tk.Label(scrollable_frame, text="此地图上的秘境:", font=("Arial", 14)).pack(pady=10)
            for i, dungeon in enumerate(self.current_map.dungeons):
                tk.Button(scrollable_frame, text=f"{dungeon.name}: {dungeon.description}", command=lambda d=dungeon: self.enter_dungeon(d)).pack(pady=5)
        else:
            tk.Label(scrollable_frame, text="此地图上没有秘境可以探索。", font=("Arial", 14)).pack(pady=10)

        tk.Button(scrollable_frame, text="返回", command=self.go_back).pack(pady=10)

    def enter_dungeon(self, dungeon):
        """进入选定的秘境"""
        # 清空当前内容
        self.clear_content_frame()
        DungeonUI(self.content_frame, dungeon, self.player, self.go_back)

    def show_adjacent_maps(self):
        """显示相邻地图并允许玩家移动"""
        self.clear_content_frame()
        scrollable_frame = self.create_scrollable_frame()
        adjacent_maps = self.game_state.get_adjacent_maps()
        if not adjacent_maps:
            tk.Label(scrollable_frame, text="此地图没有可去的相邻地图。", font=("Arial", 14)).pack(pady=10)
            tk.Button(scrollable_frame, text="返回", command=self.go_back).pack(pady=10)
            return

        tk.Label(scrollable_frame, text="你可以离开此地去以下地点:", font=("Arial", 14)).pack(pady=10)
        for map_number, details in adjacent_maps.items():
            adjacent_map = self.game_state.get_map(map_number)
            map_button = tk.Button(scrollable_frame, text=f"{adjacent_map.name}，距离: {details['distance']}",
                                   command=lambda m=map_number: self.move_to_map(m))
            map_button.pack(pady=5)

        tk.Button(scrollable_frame, text="返回", command=self.go_back).pack(pady=10)

    def move_to_map(self, map_number):
        # 获取要进入的地图对象
        new_map = self.game_state.get_map(map_number)

        # 进行通行证检查
        if new_map and new_map.passport and new_map.passport not in self.player.inventory:
            messagebox.showinfo("无法进入", new_map.unpasstext or "你无法进入该地图")
            return  # 阻止进入该地图

        # 通行证检查通过，执行进入地图的逻辑
        self.clear_content_frame()  # 清空界面
        # 启动一个新的线程进行地图移动，避免阻塞 Tkinter 主线程
        move_thread = threading.Thread(target=self._move_to_map_thread, args=(map_number,))
        move_thread.start()

    def _move_to_map_thread(self, map_number):
        """地图移动线程，避免阻塞 Tkinter 的主事件循环"""
        # 在子线程中执行地图移动逻辑
        self.game_state.move_player_to_map(map_number)
        new_map = self.game_state.get_map(map_number)
        if not new_map.can_enter(self.player):
            return
        # 确保界面更新通过主线程执行
        if new_map:
            self.root.after(0, lambda: self.show_map_ui(new_map))
        else:
            self.root.after(0, lambda: messagebox.showerror("错误", "无法加载新地图。"))

    def clear_content_frame(self):
        """清空 content_frame 的所有内容"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def go_back(self):
        """返回上一级界面"""
        if self.page_stack:
            # 从栈中弹出上一级页面并显示
            self.page_stack.pop()()

    def create_scrollable_frame(self):
        """创建一个带滚动条的可滚动框架"""

        # 创建 Canvas 作为主容器，用于显示内容
        self.canvas = tk.Canvas(self.content_frame, background="#f0f0f0")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建一个垂直滚动条并绑定到 Canvas
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 创建一个 Frame 用于显示可滚动内容，放在 Canvas 中
        scrollable_frame = tk.Frame(self.canvas, background="#f0f0f0")

        # 将 Frame 置于 Canvas 的 window 中，并保存引用
        self.canvas_window = self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # 自动调整 Canvas 滚动区域的范围
        def on_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", on_frame_configure)

        # 确保 Canvas 宽度随窗口大小调整
        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)

        self.canvas.bind("<Configure>", on_canvas_configure)

        # 添加鼠标滚轮支持，绑定到 root 窗口的全局滚动
        def _on_mouse_wheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # 绑定鼠标滚动事件到 root 窗口
        self.root.bind_all("<MouseWheel>", _on_mouse_wheel)

        return scrollable_frame