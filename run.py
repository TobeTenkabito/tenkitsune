import tkinter as tk
import copy
import os
import pygame
from tkinter import ttk
from tkinter import messagebox, simpledialog
from all.gamestate import game_state
from all.dlcmanager import DLCManager
from common.ui.bagui import BagUI
from common.ui.mapui import MapUI
from common.ui.synthesisui import SynthesisUI
from common.ui.cultivationui import CultivationUI
from common.ui.lotteryui import LotteryUI
from common.ui.marketui import MarketUI
from common.ui.storyui import StoryUI
from common.module.story import Chapter, load_story_from_json
from common.module.battle import Battle
from library.material_library import material_library
from library.skill_library import skill_library
from library.lottery_library import lottery_library
from library.map_library import map_library
from library.npc_library import npc_library
from library.warp_library import warp_library
from library.product_library import product_library
from all.load import equipment_library


# Tkinter 主应用类
class GameApp:
    def __init__(self, root, dlc_manager):
        self.root = root
        self.dlc_manager = dlc_manager
        self.root.title("天狐修炼纪")
        self.current_player = None  # 不再直接管理玩家实例
        self.slot_number = None
        self.debug = False

        self.init_mixer()

        # 玩家相关的标签
        self.hp_label = tk.Label(self.root, text="生命值: 100/100")
        self.hp_label.pack()

        self.hp_progress = tk.Label(self.root, text="", bg="red", width=20, height=2)
        self.hp_progress.pack()

        self.mp_label = tk.Label(self.root, text="法力值: 100/100")
        self.mp_label.pack()

        self.mp_progress = tk.Label(self.root, text="", bg="blue", width=20, height=2)
        self.mp_progress.pack()

        self.exp_label = tk.Label(self.root, text="经验值: 0/100")
        self.exp_label.pack()

        self.exp_progress = tk.Label(self.root, text="", bg="gray", width=20, height=2)
        self.exp_progress.pack()

        # 显示主菜单
        self.show_title_screen()

    # 初始化音频
    def init_mixer(self):
        try:
            pygame.mixer.init()
            print("mixer: 初始化成功")
        except pygame.error as e:
            print(f"mixer: 初始化失败: {e}")

    # 主菜单界面
    def show_title_screen(self):
        self.clear_screen()
        title_label = tk.Label(self.root, text="======= 天狐修炼纪 =======", font=("Arial", 24))
        title_label.pack(pady=20)

        start_button = tk.Button(self.root, text="旅途开始", command=self.start_new_game, width=20, height=2)
        load_button = tk.Button(self.root, text="前尘忆梦（读档）", command=self.load_game_menu, width=20, height=2)
        exit_button = tk.Button(self.root, text="结束征程（退出）", command=self.end_game, width=20, height=2)

        start_button.pack(pady=10)
        load_button.pack(pady=10)
        exit_button.pack(pady=10)

        self.play_bgm('resources/music/main/main1.mp3')

    # 清除屏幕上的所有小部件
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # 新游戏功能
    def start_new_game(self):
        self.clear_screen()

        # 初始化玩家
        game_state.initialize_player(1, "白夙")
        self.current_player = game_state.get_player()

        # 初始化地图
        try:
            for map_number, map_obj in map_library.items():
                game_state.add_map(map_number, map_obj)
            print("全局地图初始化成功")
        except Exception as e:
            print(f"全局地图初始化失败: {e}")

        # 初始化npc
        try:
            for npc_number, npc_obj in npc_library.items():
                game_state.add_npc(npc_number, npc_obj)
            print("全局npc初始化成功")
        except Exception as e:
            print(f"全局npc初始化失败: {e}")

        # 调用 load_all_dlcs() 方法，而不是将其当作迭代对象
        for dlc in self.dlc_manager.load_all_dlcs():  # 这里需要调用方法
            dlc.register_trait_hooks(self.current_player)

        # 将DLC应用到玩家
        self.dlc_manager.apply_dlcs_to_player(self.current_player)

        # 添加初始物品
        coin = copy.deepcopy(material_library[100000])
        coin.quantity = 100
        self.current_player.add_to_inventory(coin)
        self.current_player.add_to_skill(copy.deepcopy(skill_library[200001]))
        self.current_player.add_to_skill(copy.deepcopy(skill_library[200011]))
        self.current_player.add_to_skill(copy.deepcopy(skill_library[200000]))
        self.current_player.add_to_skill(copy.deepcopy(skill_library[200002]))
        self.current_player.add_to_skill(copy.deepcopy(skill_library[200004]))

        # 以下物品仅供测试
        beidou = copy.deepcopy(material_library[120000])
        beidou.quantity = 200
        self.current_player.add_to_inventory(copy.deepcopy(equipment_library[410012]))
        a = copy.deepcopy(material_library[100059])
        a.quantity = 20
        self.current_player.add_to_inventory(a)
        b = copy.deepcopy(material_library[100019])
        b.quantity = 3
        self.current_player.add_to_inventory(b)
        self.current_player.add_to_inventory(copy.deepcopy(material_library[100004]))
        self.current_player.add_to_inventory(copy.deepcopy(material_library[100004]))
        self.current_player.add_to_inventory(copy.deepcopy(material_library[100005]))
        self.current_player.add_to_inventory(copy.deepcopy(material_library[100006]))
        self.current_player.add_to_inventory(copy.deepcopy(material_library[100007]))
        self.current_player.add_to_inventory(copy.deepcopy(material_library[100008]))
        self.current_player.add_to_inventory(beidou)
        self.current_player.add_to_inventory(copy.deepcopy(skill_library[200019]))
        self.current_player.add_to_inventory(copy.deepcopy(skill_library[200032]))
        self.current_player.add_to_inventory(copy.deepcopy(equipment_library[400001]))
        self.current_player.add_to_inventory(copy.deepcopy(equipment_library[400006]))
        self.current_player.add_to_inventory(copy.deepcopy(equipment_library[430002]))
        self.current_player.add_to_inventory(copy.deepcopy(warp_library[170003]))
        self.current_player.add_to_inventory(copy.deepcopy(product_library[310002]))

        self.enter_main_screen()

    # 读档菜单
    def load_game_menu(self):
        slot_number = simpledialog.askinteger("读档", "请输入存档编号 (1-5):")
        from main import load_game
        if slot_number:
            player = load_game(slot_number)
            if player:
                game_state.set_player(player)  # 通过GameState设置玩家
                self.current_player = game_state.get_player()  # 更新当前玩家
                self.slot_number = slot_number
                self.enter_main_screen()

    def save_game_menu(self):
        slot_number = self.choose_save_slot()
        from main import save_game
        if slot_number:
            save_game(self.current_player, slot_number)

    # 进入游戏主界面
    def enter_main_screen(self):
        self.clear_screen()
        self.play_bgm('resources/music/main/mian2.mp3')
        # 玩家状态在左上角显示
        player_info_frame = tk.Frame(self.root)
        player_info_frame.pack(side="top", anchor="nw", padx=20, pady=20)

        player_info_label = tk.Label(player_info_frame, text=f"玩家: {self.current_player.name}", font=("Arial", 16))
        player_info_label.pack(anchor="w")

        # 使用 ttk.Progressbar 来显示进度条
        style = ttk.Style()
        style.theme_use('default')
        style.configure("red.Horizontal.TProgressbar", troughcolor='gray', background='red')
        style.configure("blue.Horizontal.TProgressbar", troughcolor='gray', background='blue')
        style.configure("yellow.Horizontal.TProgressbar", troughcolor='gray', background='yellow')

        # 重新创建所有状态显示的控件
        self.hp_label = tk.Label(player_info_frame,
                                 text=f"生命值: {self.current_player.hp}/{self.current_player.max_hp}",
                                 font=("Arial", 12))
        self.hp_label.pack(anchor="w")
        self.hp_progress = ttk.Progressbar(player_info_frame, style="red.Horizontal.TProgressbar", length=200,
                                           mode='determinate')
        self.hp_progress['value'] = (self.current_player.hp / self.current_player.max_hp) * 100
        self.hp_progress.pack(anchor="w")

        self.mp_label = tk.Label(player_info_frame,
                                 text=f"法力值: {self.current_player.mp}/{self.current_player.max_mp}",
                                 font=("Arial", 12))
        self.mp_label.pack(anchor="w")
        self.mp_progress = ttk.Progressbar(player_info_frame, style="blue.Horizontal.TProgressbar", length=200,
                                           mode='determinate')
        self.mp_progress['value'] = (self.current_player.mp / self.current_player.max_mp) * 100
        self.mp_progress.pack(anchor="w")

        self.exp_label = tk.Label(player_info_frame,
                                  text=f"经验值: {self.current_player.exp}/{self.current_player.max_exp}",
                                  font=("Arial", 12))
        self.exp_label.pack(anchor="w")
        self.exp_progress = ttk.Progressbar(player_info_frame, style="yellow.Horizontal.TProgressbar", length=200,
                                            mode='determinate')
        self.exp_progress['value'] = (self.current_player.exp / self.current_player.max_exp) * 100
        self.exp_progress.pack(anchor="w")

        # 新增的显示区域 (绿色边框)
        self.content_frame = tk.Frame(self.root, width=600, height=400, bg="white", highlightbackground="orange", highlightthickness=2)
        self.content_frame.pack(pady=20)
        self.content_frame.pack_propagate(False)

        # 每次进入主界面时重新创建 Text 控件
        self.text_area = tk.Text(self.content_frame, wrap="word", height=10, width=50, font=("Arial", 12))
        self.text_area.pack(pady=10)

        # 主界面其他按钮显示在底部，并水平排列
        button_frame = tk.Frame(self.root)
        button_frame.pack(side="bottom", pady=20)

        # 水平排列的按钮
        bag_button = tk.Button(button_frame, text="背包", command=self.show_bag_interface, width=10, height=2)
        cultivation_button = tk.Button(button_frame, text="修为", command=self.show_cultivation_interface, width=10, height=2)
        synthesis_button = tk.Button(button_frame, text="合成", command=self.show_synthesis_ui, width=10, height=2)
        lottery_button = tk.Button(button_frame, text="抽奖", command=self.show_lottery_ui, width=10, height=2)
        market_button = tk.Button(button_frame, text="集市", command=self.show_market_ui, width=10, height=2)
        explore_button = tk.Button(button_frame, text="探索", command=self.explore_current_map, width=10, height=2)
        train_button = tk.Button(button_frame, text="修炼", command=self.train_player_interact, width=10, height=2)
        save_button = tk.Button(button_frame, text="保存", command=self.save_game_menu, width=10, height=2)
        load_button = tk.Button(button_frame, text="读档", command=self.load_game_menu, width=10, height=2)
        story_button = tk.Button(button_frame, text="故事", command=self.show_story_mode, width=10, height=2)
        exit_button = tk.Button(button_frame, text="返回主菜单", command=self.show_title_screen, width=10, height=2)

        if self.debug:
            debug_button = tk.Button(button_frame, text="调试模式", command=self.debug_mod, width=10, height=2)
            debug_button.pack(side="left", padx=5)

        # 检查是否加载了特质DLC，并显示相关按钮
        if self.dlc_manager.is_dlc_loaded("dlc.dlc_traits"):
            traits_button = tk.Button(self.root, text="查看特质", command=self.show_traits, width=10, height=2)
            traits_button.pack(pady=10)

        # 将按钮水平排列在一个Frame中
        bag_button.pack(side="left", padx=5)
        cultivation_button.pack(side="left", padx=5)
        synthesis_button.pack(side="left", padx=5)
        lottery_button.pack(side="left", padx=5)
        market_button.pack(side="left", padx=5)
        explore_button.pack(side="left", padx=5)
        train_button.pack(side="left", padx=5)
        save_button.pack(side="left", padx=5)
        load_button.pack(side="left", padx=5)
        story_button.pack(side="left", padx=5)
        exit_button.pack(side="left", padx=5)

    # 显示玩家信息
    def show_player_info(self):
        player = self.current_player
        player_info = f"玩家: {player.name}\n等级: {player.level}\n生命值: {player.hp}/{player.max_hp}\n法力值: {player.mp}/{player.max_mp}"
        player_info_label = tk.Label(self.root, text=player_info, font=("Arial", 16))
        player_info_label.pack(pady=10)

    # 背包互动
    def show_bag_interface(self):
        bag_ui = BagUI(self.current_player, self.content_frame)
        bag_ui.show_bag_interface()  # 显示背包界面

    # 修为互动
    def show_cultivation_interface(self):
        # 清空 content_frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        cultivation_frame = tk.Frame(self.content_frame, bg="white")
        cultivation_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        CultivationUI(cultivation_frame, self.current_player.cultivation_system)

    def train_player_interact(self):
        from main import train_player
        # 清空 content_frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 重新创建 Text 区域
        self.text_area = tk.Text(self.content_frame, wrap="word", height=10, width=50, font=("Arial", 12))
        self.text_area.pack(pady=10)

        # 执行修炼逻辑
        result_text = train_player(self.current_player)
        self.update_player_info(self.current_player)

        # 在 text_area 中显示修炼结果
        self.text_area.delete(1.0, tk.END)  # 清空之前的内容
        self.text_area.insert(tk.END, result_text)  # 显示新的修炼结果

    # 合成互动
    def show_synthesis_ui(self):
        synthesis_ui = SynthesisUI(self.root, self.current_player, self.content_frame)
        synthesis_ui.start_synthesis_ui()

    # 抽奖互动
    def show_lottery_ui(self):
        lottery_pool = lottery_library[1]
        lottery_ui = LotteryUI(self.root, self.current_player, self.content_frame, lottery_pool)
        lottery_ui.start_lottery_ui()

    # 市场互动
    def show_market_ui(self):
        market_ui = MarketUI(self.root, self.current_player, self.content_frame)
        market_ui.start_market_ui()

    # 探索地图
    def explore_current_map(self):
        current_map = game_state.get_map(self.current_player.map_location)
        self.play_bgm('resources/music/explore/explore1.mp3')
        if current_map:
            map_ui = MapUI(self.root, self.current_player, self.content_frame, game_state)
            map_ui.show_map_ui(current_map)  # 启动地图界面
        else:
            messagebox.showerror("错误", f"无法探索当前地图。")

    # 故事模式
    def show_story_mode(self):
        from common.module.story import StoryManager
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # 禁用主界面按钮
        self.disable_main_buttons()
        canvas = tk.Canvas(self.content_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollable_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", on_frame_configure)

        # 定义故事的动态战斗
        dynamic_battle = Battle(player=self.current_player, allies=[], enemies=[])

        # 定义故事章节并加载内容
        chapters = self.define_chapters(self.current_player, dynamic_battle)
        story_manager = StoryManager(self.current_player, chapters)

        # 创建Story UI
        StoryUI(scrollable_frame, self.current_player, story_manager, self.enable_main_buttons)

    # 定义故事章节
    def define_chapters(self, player, dynamic_battle):
        chapters = []
        chapter1 = Chapter(1, "第一章", None, None)
        load_story_from_json('chapter/chapter1.json', player, dynamic_battle, chapter=chapter1)
        chapter1.is_completed = player.story_progress["chapters_completed"].get("1", False)
        chapters.append(chapter1)
        chapter2 = Chapter(2, "第二章", None, None)
        load_story_from_json('chapter/chapter2.json', player, dynamic_battle, chapter=chapter2)
        chapter2.is_completed = player.story_progress["chapters_completed"].get("2", False)
        chapters.append(chapter2)
        chapter3 = Chapter(3, "第三章", None, None)
        load_story_from_json('chapter/chapter3.json', player, dynamic_battle, chapter=chapter3)
        chapter3.is_completed = player.story_progress["chapters_completed"].get("3", False)
        chapters.append(chapter3)
        return chapters

    # 选择存档槽
    def choose_save_slot(self):
        slot_number = simpledialog.askinteger("选择存档", "请输入存档编号 (1-5):")
        return slot_number

    def update_player_info(self, player):
        # 更新生命值
        self.hp_label.config(text=f"生命值: {player.hp}/{player.max_hp}")
        self.hp_progress['value'] = (player.hp / player.max_hp) * 100

        # 更新法力值
        self.mp_label.config(text=f"法力值: {player.mp}/{player.max_mp}")
        self.mp_progress['value'] = (player.mp / player.max_mp) * 100

        # 更新经验值
        self.exp_label.config(text=f"经验值: {player.exp}/{player.max_exp}")
        self.exp_progress['value'] = (player.exp / player.max_exp) * 100

    # 主界面按钮类
    def disable_main_buttons(self):
        """禁用主界面按钮"""
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.DISABLED)

    def enable_main_buttons(self):
        """启用主界面按钮"""
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.config(state=tk.NORMAL)

    def play_bgm(self, file_path):
        """播放背景音乐"""
        if os.path.exists(file_path):
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(-1)
        else:
            print(f"文件 {file_path} 未找到！")

    # 退出游戏
    def end_game(self):
        pygame.mixer.music.stop()
        self.root.quit()

    # debug模式
    def debug_mod(self):
        return

    # dlc特质
    def show_traits(self):
        """展示特质信息"""
        for dlc in self.dlc_manager.dlc_modules:
            if hasattr(dlc, 'show_traits'):
                dlc.show_traits(self.current_player)
                return


if __name__ == "__main__":
    root = tk.Tk()
    dlc_manager = DLCManager()
    app = GameApp(root, dlc_manager)
    root.mainloop()

