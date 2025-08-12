import copy
import os
import sys
import pygame
import random
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
from common.character.boss import Boss
from common.module.item import Skill, Medicine, Product
from common.module.battle import Battle


class BattleUI:
    def __init__(self, root, player, allies, enemies, on_battle_end_callback):
        self.root = root
        self.player = player
        self.allies = allies
        self.enemies = enemies
        self.on_battle_end_callback = on_battle_end_callback
        self.battle_over = False
        self.auto_battle = False
        self.debug = True

        self.init_mixer()

        # 创建 Battle 对象管理战斗逻辑
        self.battle = Battle(player, allies, enemies)
        self.current_turn = 1  # 初始化当前回合数
        # 确保 turn_order 已正确初始化
        if not self.battle.turn_order:
            print(f"错误: 行动顺序未生成, 参与者: {self.battle.player}, {self.battle.allies}, {self.battle.enemies}")
            raise ValueError("行动顺序为空，无法开始回合")
        # 初始化战斗窗口
        self.window = tk.Toplevel(root)
        self.window.title("战斗场景")
        self.window.geometry("900x500")  # 调整窗口大小

        # **绑定关闭窗口事件**
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # 添加显示当前回合的标签
        self.turn_label = tk.Label(self.window, text=f"当前回合: {self.current_turn}")
        self.turn_label.pack(pady=5)

        # 回合顺序显示
        self.turn_order_label = tk.Label(self.window, text="回合顺序: " + ", ".join([p.name for p in self.battle.turn_order]))
        self.turn_order_label.pack(pady=5)

        # 显示敌人列表
        self.enemy_listbox = tk.Listbox(self.window, height=5, width=50)
        self.update_enemy_listbox()
        self.enemy_listbox.pack(pady=5)

        self.create_action_buttons()

        # 战斗日志显示框
        self.log_text = ScrolledText(self.window, height=10, width=60, state="disabled")
        self.log_text.pack(pady=5)

        # 配置文本标签样式
        self.log_text.tag_config("blue", foreground="blue")
        self.log_text.tag_config("green", foreground="green")
        self.log_text.tag_config("yellow", foreground="yellow")
        self.log_text.tag_config("orange", foreground="orange")
        self.log_text.tag_config("red", foreground="red")
        self.log_text.tag_config("magenta", foreground="magenta")
        self.log_text.tag_config("purple", foreground="purple")
        self.log_text.tag_config("normal", foreground="black")

        # 保存默认的 sys.stdout
        self.default_stdout = sys.stdout

        # 重定向日志输出到战斗界面
        self.redirect_stdout_to_battle_ui()

        # 创建左上角的玩家状态栏框架
        self.status_frame = tk.Frame(self.window)
        self.status_frame.place(x=10, y=10)

        # 配置进度条样式
        style = ttk.Style()
        style.theme_use('clam')  # 使用 clam 样式来确保自定义颜色生效
        style.configure("BattleRed.Horizontal.TProgressbar", troughcolor="gray", background="red")
        style.configure("BattleBlue.Horizontal.TProgressbar", troughcolor="gray", background="blue")

        # HP 条（红色）
        tk.Label(self.status_frame, text="HP:").grid(row=0, column=0, sticky="w")
        self.hp_bar = ttk.Progressbar(self.status_frame, style="BattleRed.Horizontal.TProgressbar", length=120, maximum=self.player.max_hp)
        self.hp_bar.grid(row=0, column=1, padx=5)
        self.hp_bar['value'] = self.player.hp  # 设置当前 HP 值

        # MP 条（蓝色）
        tk.Label(self.status_frame, text="MP:").grid(row=1, column=0, sticky="w")
        self.mp_bar = ttk.Progressbar(self.status_frame, style="BattleBlue.Horizontal.TProgressbar", length=120, maximum=self.player.max_mp)
        self.mp_bar.grid(row=1, column=1, padx=5)
        self.mp_bar['value'] = self.player.mp  # 设置当前 MP 值

        # 添加其他属性标签
        self.attr_labels = {}
        # 使用玩家的实际属性名称
        attributes = {
            "气血": f"{self.player.hp}/{self.player.max_hp}",
            "法力": f"{self.player.mp}/{self.player.max_mp}",
            "攻击": self.player.attack,
            "防御": self.player.defense,
            "速度": self.player.speed,
            "暴击": self.player.crit,
            "暴击伤害": self.player.crit_damage,
            "抗性": self.player.resistance,
            "穿透": self.player.penetration
        }

        for i, (attr_name, attr_value) in enumerate(attributes.items(), start=2):
            label = tk.Label(self.status_frame, text=f"{attr_name}: {attr_value}")
            label.grid(row=i, column=0, columnspan=2, sticky="w")
            self.attr_labels[attr_name] = label

        # 初始化 UI 更新
        self.update_ui()

        self.play_bgm('resources/music/battle/battle1.mp3')

        # 开始第一回合
        self.start_turn()

    def init_mixer(self):
        try:
            pygame.mixer.init()
            print("mixer: 初始化成功")
        except pygame.error as e:
            print(f"mixer: 初始化失败: {e}")

    def create_action_buttons(self):
        """创建玩家的操作按钮区域"""
        action_frame = tk.Frame(self.window)
        action_frame.pack(pady=10)

        self.action_buttons = []  # 用于存储所有操作按钮

        jump_button = tk.Button(action_frame, text="观望", command=self.jump_action)
        jump_button.grid(row=1, column=0, padx=10)

        attack_button = tk.Button(action_frame, text="攻击", command=self.attack_action)
        attack_button.grid(row=0, column=0, padx=10)

        skill_button = tk.Button(action_frame, text="使用技能", command=self.skill_action)
        skill_button.grid(row=0, column=1, padx=10)

        equipment_button = tk.Button(action_frame, text="使用法宝", command=self.equipment_action)
        equipment_button.grid(row=0, column=2, padx=10)

        medicine_button = tk.Button(action_frame, text="使用药品", command=self.medicine_action)
        medicine_button.grid(row=0, column=3, padx=10)

        item_button = tk.Button(action_frame, text="使用道具", command=self.item_action)
        item_button.grid(row=0, column=4, padx=10)

        self.auto_battle_button = tk.Button(action_frame, text="开启自动战斗", command=self.toggle_auto_battle)
        self.auto_battle_button.grid(row=0, column=5, padx=10)

        if self.debug:
            debug_button = tk.Button(action_frame, text="调试模式", command=self.debug_module)
            debug_button.grid(row=0, column=6, padx=10)

    def jump_action(self):
        self.log_action(f"你对战场局势心存疑惑或无法行动，选择观望以待时机。", tag="red")
        self.next_turn()

    def start_turn(self):
        # 更新回合显示
        self.turn_label.config(text=f"当前回合: {self.current_turn}")

        """执行当前回合角色的行动"""
        if not self.battle.turn_order:
            return  # 无有效行动者则返回

        # 获取当前行动者
        current_entity = self.battle.turn_order[0]
        print(f"当前回合的行动者：{current_entity.name}")

        # 回合开始检查属性
        self.player.update_stats()
        self.battle.check_hp_mp_limits()

        # 是否可以行动
        if current_entity.dizzy_rounds > 0:
            self.log_action(f"{current_entity.name}正眩晕,无法行动", tag="red")
            current_entity.dizzy_rounds -= 1
            return self.next_turn()
        elif current_entity.paralysis_rounds > 0 and random.random() < 0.5:
            self.log_action(f"{current_entity.name}正麻醉，无法行动", tag="red")
            current_entity.paralysis_rounds -= 1
            return self.next_turn()
        # 玩家行动
        if current_entity == self.battle.player:
            self.log_action(f"轮到 {self.player.name} 行动", tag="blue")
            if current_entity.hp <= 0:
                self.log_action(f"{self.player.name} 气血耗尽，已经倒下")
                return self.next_turn()
            else:
                if self.auto_battle:
                    self.battle.auto_action()
                    self.update_ui()
                    self.window.after(1000, self.next_turn)  # 自动战斗后自动进入下一回合
                else:
                    self.enable_player_controls()  # 启用玩家控制

        # 队友行动
        elif current_entity in self.battle.allies:
            self.log_action(f"轮到 {current_entity.name} 行动", tag="green")
            self.disable_player_controls()
            self.ally_action(current_entity)

        # 敌人行动
        elif current_entity in self.battle.enemies:
            self.log_action(f"轮到 {current_entity.name} 行动", tag="purple")
            self.disable_player_controls()
            self.enemy_action(current_entity)

        else:
            print(f"错误:{current_entity.name}不具有正确的战斗属性")
            return self.log_action(f"错误:{current_entity.name}不具有正确的战斗属性")

        # 确保回合结束前检查存活状态
        if not self.battle.enemies:
            self.end_battle("victory")
        elif self.player.hp <= 0 and all(ally.hp <= 0 for ally in self.allies):
            self.end_battle("defeat")

    def enable_player_controls(self):
        """启用玩家控制按钮"""
        for button in self.action_buttons:
            button.config(state=tk.NORMAL)

    def disable_player_controls(self):
        """禁用玩家控制按钮"""
        for button in self.action_buttons:
            button.config(state=tk.DISABLED)

    def attack_action(self):
        """玩家选择攻击某个敌人"""
        selected_enemy_index = self.enemy_listbox.curselection()
        if not selected_enemy_index:
            messagebox.showwarning("选择错误", "请选择一个敌人进行攻击")
            return

        selected_enemy = self.battle.enemies[selected_enemy_index[0]]

        # 计算实际伤害
        damage = self.battle.player.perform_attack(selected_enemy)  # 返回伤害值
        if damage is not None:
            self.log_action(f"{self.player.name} 攻击了 {selected_enemy.name}，造成了 {damage} 点伤害")
        else:
            self.log_action(f"由于致盲，{self.player.name}普通攻击未能生效")

        if selected_enemy.hp <= 0:
            # 移除敌人并处理掉落物
            drops = self.battle.process_enemy_drops(selected_enemy)  # 获取掉落物

            # 显示掉落物品
            for item_name, quantity in drops:
                self.log_action(f"获得掉落物: {item_name} x {quantity}")

            # 更新UI
            self.enemy_listbox.delete(selected_enemy_index)
            self.battle.turn_order = [entity for entity in self.battle.turn_order if entity != selected_enemy]
            self.battle.enemies.pop(selected_enemy_index[0])

        # 检查战斗是否结束
        if not self.battle.enemies:
            self.end_battle("victory")
        else:
            self.update_ui()

        # 结束玩家回合，继续下一回合
        self.next_turn()

    def enemy_action(self, enemy):
        """敌人进行自动行动"""
        if enemy.hp <= 0:
            # 如果敌人已经死亡，先将其从回合顺序和敌人列表中移除
            self.battle.turn_order = [entity for entity in self.battle.turn_order if entity != enemy]
            if enemy in self.battle.enemies:
                self.battle.enemies.remove(enemy)
            self.next_turn()
            return

        if isinstance(enemy, Boss):
            # Boss有可能召唤小怪，场上小怪数量限制为5
            if len(self.battle.enemies) < 5:
                enemy.boss_action(self.battle)
                self.log_action(f"{enemy.name} 召唤了更多的敌人！")
            else:
                self.log_action(f"{enemy.name} 无法召唤更多小怪，因为场上敌人数量已达上限。")
                # 普通攻击
                target = random.choice([self.player] + self.battle.allies)
                damage = enemy.perform_attack(target)
                if damage is not None:
                    self.log_action(f"{enemy.name} 攻击了 {target.name}，造成了 {damage} 点伤害")
                else:
                    self.log_action(f"由于致盲或倒下，{enemy.name}普通攻击未能生效", tag="red")
        else:
            # 50% 概率使用技能
            if enemy.battle_skills and random.random() < 0.5:
                skill = random.choice(enemy.battle_skills)
                # 技能目标选择逻辑
                if skill.target_scope == "all" and skill.target_type == "enemy":
                    targets = [self.player] + self.battle.allies
                else:
                    targets = [random.choice([self.player] + self.battle.allies)]
                if targets:
                    if enemy.silence_rounds > 0:
                        self.log_action(f"由于沉默，{enemy.name}无法使用技能", tag="red")
                        return
                    else:
                        enemy.use_skill(skill, targets)
                        self.log_action(
                            f"{enemy.name} 使用了技能 {skill.name}，对 {', '.join(t.name for t in targets)} 造成伤害")
            else:
                # 普通攻击
                target = random.choice([self.player] + self.battle.allies)
                damage = enemy.perform_attack(target)
                if damage is not None:
                    self.log_action(f"{enemy.name} 攻击了 {target.name}，造成了 {damage} 点伤害")
                else:
                    self.log_action(f"由于致盲，{enemy.name}普通攻击未能生效", tag="red")

        self.update_ui()

        # 检查战斗是否结束
        if self.battle.allies:
            if self.player.hp <= 0 and all(ally.hp <= 0 for ally in self.allies):
                self.end_battle("defeat")
                return
        if not self.battle.allies:
            if self.player.hp <= 0:
                self.end_battle("defeat")
                return

        # 敌人行动结束后，继续下一回合
        self.window.after(1000, self.next_turn)

    def ally_action(self, ally):
        """队友进行自动行动"""
        if ally.hp <= 0:
            self.battle.turn_order = [entity for entity in self.battle.turn_order if entity != ally]
            if ally in self.battle.enemies:
                self.battle.enemies.remove(ally)
            self.next_turn()
            return
        # 50% 的概率使用技能
        if ally.battle_skills and random.random() < 0.5:
            skill = random.choice(ally.battle_skills)
            # 技能目标选择逻辑
            if skill.target_scope == "all":
                target = self.battle.enemies if skill.target_type == "enemy" else [self.player] + self.battle.allies
            else:
                target = random.choice(self.battle.enemies) if self.battle.enemies else None
            if target:
                if ally.silence_rounds > 0:
                    self.log_action(f"由于沉默，{ally.name}无法使用技能", tag="red")
                    return
                else:
                    ally.use_skill(skill, target)
                    if isinstance(target, list):  # 群体技能
                        target_names = ", ".join([t.name for t in target])
                    else:
                        target_names = target.name
                    self.log_action(f"{ally.name} 使用了技能 {skill.name}，对 {target_names} 造成伤害")
        else:
            # 普通攻击
            if self.battle.enemies:
                target = random.choice(self.battle.enemies)
                damage = ally.perform_attack(target)
                if damage is not None:
                    self.log_action(f"{ally.name} 攻击了 {target.name}，造成了 {damage} 点伤害")
                else:
                    self.log_action(f"由于致盲，{ally.name}普通攻击未能生效", tag="red")

        self.update_ui()

        # 队友行动结束后，继续下一回合
        self.window.after(1000, self.next_turn)

    def next_turn(self):
        # 检查敌人或玩家的状态是否需要结束战斗
        if not self.battle.enemies:
            self.end_battle("victory")
            return
        elif self.player.hp <= 0 and all(ally.hp <= 0 for ally in self.allies):
            self.end_battle("defeat")
            return

        # 移除已行动的角色
        if self.battle.turn_order:
            self.battle.turn_order.pop(0)

        self.update_ui()

        # 若 turn_order 为空，生成新的回合顺序
        if not self.battle.turn_order:
            self.current_turn += 1  # 新的回合数
            self.battle.determine_turn_order()
            # 仅在回合更新时应用和减少 buff 持续时间
            self.battle.apply_buffs()
            self.log_action(f"回合结束，进入第 {self.current_turn} 回合", tag="magenta")

        # 开始当前回合行动
        self.start_turn()

    def skill_action(self):
        """玩家选择使用技能"""
        skills = [item for item in self.battle.player.battle_skills if isinstance(item, Skill)]
        if not skills:
            messagebox.showwarning("错误", "没有技能可以使用")
            return

        if self.player.silence_rounds > 0:
            self.log_action(f"正在沉默，{self.player.name}无法使用技能", tag="red")
            return
        else:
            self.choose_skill_ui(skills)

    def choose_skill_ui(self, skills):
        """让玩家通过UI选择技能"""
        skill_window = tk.Toplevel(self.window)
        skill_window.title("选择技能")
        skill_window.geometry("300x200")

        tk.Label(skill_window, text="请选择技能:", font=("Arial", 12)).pack(pady=10)

        skill_listbox = tk.Listbox(skill_window, height=5)
        for skill in skills:
            skill_listbox.insert(tk.END, f"{skill.name} - {skill.description}")
        skill_listbox.pack(pady=10)

        def confirm_skill():
            selected_index = skill_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("错误", "请选择一个技能")
                return
            selected_skill = skills[selected_index[0]]
            skill_window.destroy()
            # 选择目标并使用技能
            target = self.choose_target(selected_skill.target_type, selected_skill.target_scope)
            if target:
                self.battle.player.use_skill(selected_skill, target)
                self.log_action(f"{self.player.name} 使用了技能 {selected_skill.name}")
                self.update_ui()
                self.next_turn()
        tk.Button(skill_window, text="确认", command=confirm_skill).pack(pady=10)

    def equipment_action(self):
        """玩家选择使用法宝"""
        equipments = [item for item in self.battle.player.equipment if item.category == "法宝"]
        if not equipments:
            messagebox.showwarning("错误", "没有法宝可以使用")
            return

        # 创建一个选择法宝的弹窗
        self.choose_equipment_ui(equipments)

    def choose_equipment_ui(self, equipments):
        """让玩家通过UI选择法宝"""
        equipment_window = tk.Toplevel(self.window)
        equipment_window.title("选择法宝")
        equipment_window.geometry("300x200")

        tk.Label(equipment_window, text="请选择法宝:", font=("Arial", 12)).pack(pady=10)

        equipment_listbox = tk.Listbox(equipment_window, height=5)
        for equipment in equipments:
            equipment_listbox.insert(tk.END, f"{equipment.name} - {equipment.description}")
        equipment_listbox.pack(pady=10)

        def confirm_equipment():
            selected_index = equipment_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("错误", "请选择一个法宝")
                return
            selected_equipment = equipments[selected_index[0]]
            equipment_window.destroy()

            # 选择目标并使用法宝
            target = self.choose_target(selected_equipment.target_type, selected_equipment.target_scope)
            if target:
                self.battle.player.use_equipment(selected_equipment, target)
                self.log_action(f"{self.player.name} 使用了法宝 {selected_equipment.name}")
                self.update_ui()
                self.next_turn()

        tk.Button(equipment_window, text="确认", command=confirm_equipment).pack(pady=10)

    def choose_target(self, target_type, target_scope):
        """根据目标类型和范围选择目标"""
        if target_scope == "user":
            return self.player

        if target_type == "all":
            if target_type == "enemy":
                return self.battle.enemies  # 返回所有敌人
            elif target_type == "ally":
                return [self.player] + self.battle.allies  # 返回玩家和所有队友
        else:
            # 如果是单体目标，打开UI让玩家选择具体目标
            return self.choose_single_target(target_type)

    def choose_single_target(self, target_type):
        """选择单体目标的UI"""
        target_window = tk.Toplevel(self.window)
        target_window.title("选择目标")
        target_window.geometry("400x200")

        target_list = []
        if target_type == "enemy":
            target_list = self.battle.enemies
        elif target_type == "ally":
            target_list = [self.player] + self.battle.allies

        tk.Label(target_window, text="请选择目标:", font=("Arial", 12)).pack(pady=10)

        target_listbox = tk.Listbox(target_window, height=5)
        for target in target_list:
            target_listbox.insert(tk.END, f"{target.name} (HP: {target.hp}/{target.max_hp})")
        target_listbox.pack(pady=10)

        selected_target = None

        def confirm_target():
            nonlocal selected_target  # 允许修改外部变量 selected_target
            selected_index = target_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("错误", "请选择一个目标")
                return
            selected_target = target_list[selected_index[0]]
            target_window.destroy()

        tk.Button(target_window, text="确认", command=confirm_target).pack(pady=10)

        # 等待窗口关闭再返回目标
        self.window.wait_window(target_window)
        return selected_target

    def medicine_action(self):
        """玩家选择使用药品"""
        medicines = [item for item in self.battle.player.inventory if isinstance(item, Medicine)]
        if not medicines:
            messagebox.showwarning("错误", "没有药品可以使用")
            return

        medicine = self.battle.choose_skill_or_equipment(medicines)
        if medicine:
            target = self.battle.choose_target("ally")
            if target:
                self.battle.player.use_medicine(medicine, target)
                self.log_action(f"{self.player.name} 使用了药品 {medicine.name}，治疗了 {target.name}")
        self.update_ui()
        self.next_turn()

    def item_action(self):
        """玩家选择使用道具"""
        # 获取所有可用的道具（Product 类型）
        items = [item for item in self.battle.player.inventory if isinstance(item, Product)]
        if not items:
            messagebox.showwarning("错误", "没有道具可以使用")
            return

        # 创建一个选择道具的弹窗
        self.choose_item_ui(items)

    def choose_item_ui(self, items):
        """让玩家通过UI选择道具"""
        item_window = tk.Toplevel(self.window)
        item_window.title("选择道具")
        item_window.geometry("300x200")

        tk.Label(item_window, text="请选择道具:", font=("Arial", 12)).pack(pady=10)

        item_listbox = tk.Listbox(item_window, height=5)
        for item in items:
            item_listbox.insert(tk.END, f"{item.name} - {item.description}")
        item_listbox.pack(pady=10)

        def confirm_item():
            selected_index = item_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("错误", "请选择一个道具")
                return
            selected_item = items[selected_index[0]]
            item_window.destroy()

            # 处理道具效果
            if "summon" in selected_item.effect_changes:
                # 召唤逻辑
                self.battle.player.use_product(selected_item, target=None)
                self.log_action(f"{self.player.name} 使用了道具 {selected_item.name} 并召唤了新的队友。")
                self.update_ui()
                self.next_turn()
            else:
                # 非召唤道具：选择目标
                self.choose_item_target(selected_item)

        tk.Button(item_window, text="确认", command=confirm_item).pack(pady=10)

    def choose_item_target(self, item):
        """根据道具类型让玩家选择目标"""
        target_type = "enemy"  # 默认选择敌人为目标
        target_window = tk.Toplevel(self.window)
        target_window.title("选择目标")
        target_window.geometry("300x200")

        target_listbox = tk.Listbox(target_window, height=5)
        if target_type == "enemy":
            available_targets = self.battle.enemies
        else:
            available_targets = [self.player] + self.battle.allies

        for target in available_targets:
            target_listbox.insert(tk.END, f"{target.name} (HP: {target.hp}/{target.max_hp})")
        target_listbox.pack(pady=10)

        def confirm_target():
            selected_index = target_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("错误", "请选择一个目标")
                return
            selected_target = available_targets[selected_index[0]]
            target_window.destroy()

            # 使用道具并展示效果
            self.battle.player.use_product(item, selected_target)
            self.log_action(f"{self.player.name} 使用了道具 {item.name}，对 {selected_target.name} 造成了效果")
            self.update_ui()
            self.next_turn()

        tk.Button(target_window, text="确认", command=confirm_target).pack(pady=10)

    def toggle_auto_battle(self):
        """切换自动战斗状态"""
        self.auto_battle = not self.auto_battle
        if self.auto_battle:
            self.auto_battle_button.config(text="关闭自动战斗")
        else:
            self.auto_battle_button.config(text="开启自动战斗")
        self.log_action(f"自动战斗 {'开启' if self.auto_battle else '关闭'}")
        self.next_turn()

    def update_ui(self):
        """实时更新 HP、MP 条和属性值显示"""
        # 更新 HP 和 MP 进度条
        self.hp_bar["value"] = self.player.hp
        self.mp_bar["value"] = self.player.mp

        # 更新属性文本
        attributes = {
            "气血": f"{self.player.hp}/{self.player.max_hp}",
            "法力": f"{self.player.mp}/{self.player.max_mp}",
            "攻击": self.player.attack,
            "防御": self.player.defense,
            "速度": self.player.speed,
            "暴击": f"{self.player.crit}%",
            "暴击伤害": f"{self.player.crit_damage}%",
            "抗性": f"{self.player.resistance}%",
            "穿透": f"{self.player.penetration}%"
        }
        for attr, value in attributes.items():
            self.attr_labels[attr.lower()].config(text=f"{attr}: {value}")

        # 更新回合顺序
        self.update_turn_order_ui()

        # 更新敌人列表
        self.update_enemy_listbox()

    def update_turn_order_ui(self):
        """更新回合顺序显示"""
        self.turn_order_label.config(text="回合顺序: " + ", ".join([p.name for p in self.battle.turn_order]))

    def update_enemy_listbox(self):
        """更新敌人列表"""
        self.enemy_listbox.delete(0, tk.END)
        for enemy in self.battle.enemies:
            self.enemy_listbox.insert(tk.END, f"{enemy.name} (HP: {enemy.hp}/{enemy.max_hp})")

    def log_action(self, text, tag="normal"):
        """记录战斗日志"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def debug_module(self):
        # 创建调试窗口
        debug_window = tk.Toplevel(self.window)
        debug_window.title("调试模式")
        debug_window.geometry("500x300")

        # 添加物品功能
        tk.Label(debug_window, text="添加物品").grid(row=0, column=0, pady=5)
        item_number_entry = tk.Entry(debug_window, width=10)
        item_number_entry.grid(row=0, column=1)
        quantity_entry = tk.Entry(debug_window, width=5)
        quantity_entry.grid(row=0, column=2)
        tk.Button(debug_window, text="增加", command=lambda: add_items(item_number_entry.get(), quantity_entry)).grid(
            row=0, column=3, padx=5)

        def add_items(number, quantity_entry):
            from library.warp_library import warp_library
            from library.skill_library import skill_library
            from library.product_library import product_library
            from library.equipment_library import equipment_library
            from library.medicine_library import medicine_library
            from library.material_library import material_library
            try:
                quantity = int(quantity_entry.get())
                item_number = int(number)

                # 查找物品
                item = None
                item_category = None
                for library, category in [
                    (equipment_library, "equipment"),
                    (skill_library, "skill"),
                    (medicine_library, "medicine"),
                    (product_library, "product"),
                    (material_library, "material"),
                    (warp_library, "warp")]:

                    item = copy.deepcopy(library.get(item_number))  # 拷贝使用
                    if item:
                        item_category = category
                        break

                if not item:
                    messagebox.showerror("错误", f"未找到编号为 {item_number} 的物品。")
                    return

                # 处理不同类型物品
                if item_category == "equipment":
                    response = messagebox.askyesno("选择", f"是否将装备 '{item.name}' 添加到装备栏？")
                    if response:
                        self.player.equipment.append(item)
                    else:
                        item.quantity = quantity
                        self.player.add_to_inventory(item)
                        self.player.update_stats()
                elif item_category == "skill":
                    response = messagebox.askyesno("选择", f"是否将技能 '{item.name}' 添加到技能区？")
                    if response:
                        self.player.battle_skills.append(item)
                    else:
                        item.quantity = quantity
                        self.player.add_to_inventory(item)
                else:
                    self.player.add_to_inventory(item)
                self.update_ui()
                print(f"成功添加物品 {item.name} 数量 {quantity} 到 {item_category} 区域")

            except ValueError:
                messagebox.showerror("错误", "请输入有效的编号和数量")
            except Exception as e:
                print(f"添加物品失败: {e}")

        # 添加敌人功能
        tk.Label(debug_window, text="添加敌人编号").grid(row=1, column=0, pady=5)
        enemy_number_entry = tk.Entry(debug_window, width=10)
        enemy_number_entry.grid(row=1, column=1)
        tk.Button(debug_window, text="增加", command=lambda: add_enemy(enemy_number_entry.get())).grid(row=1, column=2,
                                                                                                       padx=5)

        def add_enemy(number):
            print("当前输入框内容:", enemy_number_entry.get())
            from library.enemy_library import enemy_library
            try:
                print(f"敌人库内容: {enemy_library.keys()}")
                if not number:  # 检查输入是否为空
                    raise ValueError("请输入敌人编号")

                enemy_number = int(number.strip())  # 转换为整数
                new_enemy = copy.copy(enemy_library[enemy_number])  # 拷贝加载，避免对源文件修改
                self.battle.enemies.append(new_enemy)
                print(f"成功添加敌人 {new_enemy.name}")
                self.update_ui()
            except ValueError:
                messagebox.showerror("错误", "敌人编号不能为空并且必须是有效数字")
            except KeyError:
                messagebox.showerror("错误", f"未找到编号为 {number} 的敌人")
            except Exception as e:
                print(f"添加敌人失败: {e}")

        # 添加队友功能
        tk.Label(debug_window, text="添加队友编号").grid(row=2, column=0, pady=5)
        ally_number_entry = tk.Entry(debug_window, width=10)
        ally_number_entry.grid(row=2, column=1)
        tk.Button(debug_window, text="增加", command=lambda: add_ally(ally_number_entry.get())).grid(row=2, column=2,
                                                                                                     padx=5)

        def add_ally(number):
            from library.ally_library import ally_library
            try:
                ally_number = int(number)
                new_ally = copy.copy(ally_library[ally_number])  # 拷贝加载
                self.battle.allies.append(new_ally)
                print(f"成功添加队友 {new_ally.name}")
                self.update_ui()
            except Exception as e:
                print(f"添加队友失败: {e}")

        # 修改属性功能
        tk.Label(debug_window, text="修改玩家属性").grid(row=3, column=0, pady=5)
        attribute_id_entry = tk.Entry(debug_window, width=10)
        attribute_id_entry.grid(row=3, column=1)
        attribute_value_entry = tk.Entry(debug_window, width=5)
        attribute_value_entry.grid(row=3, column=2)
        tk.Button(debug_window, text="修改",
                  command=lambda: change_player_attributes(attribute_id_entry.get(), attribute_value_entry.get())).grid(
            row=3, column=3, padx=5)

        def change_player_attributes(attr_id, value):
            try:
                # 检查属性是否在允许修改的属性列表中
                valid_attributes = ["hp", "max_hp", "mp", "max_mp", "attack", "defense", "speed",
                                    "crit", "crit_damage", "resistance", "penetration"]
                if attr_id not in valid_attributes:
                    raise ValueError(f"无效属性: {attr_id}")

                # 修改属性
                setattr(self.player, attr_id, int(value))
                print(f"成功将玩家的 {attr_id} 修改为 {value}")

                self.update_ui()

            except ValueError:
                messagebox.showerror("错误", "请输入有效的属性和数值")
            except Exception as e:
                print(f"修改玩家属性失败: {e}")

        # 修改队友属性功能
        tk.Label(debug_window, text="修改队友属性(编号，属性，值)").grid(row=4, column=0, pady=5)
        ally_number_entry = tk.Entry(debug_window, width=10)
        ally_number_entry.grid(row=4, column=1)
        ally_attribute_id_entry = tk.Entry(debug_window, width=5)
        ally_attribute_id_entry.grid(row=4, column=2)
        ally_attribute_value_entry = tk.Entry(debug_window, width=5)
        ally_attribute_value_entry.grid(row=4, column=3)

        tk.Button(debug_window, text="修改",
                  command=lambda: change_ally_attributes(
                      ally_number_entry.get(), ally_attribute_id_entry.get(), ally_attribute_value_entry.get())
                  ).grid(row=4, column=4, padx=5)

        def change_ally_attributes(ally_id, attr_id, value):
            """修改指定编号或全体队友的属性"""
            try:
                value = float(value)

                if ally_id.lower() == "all" or ally_id == "" or ally_id == 0:
                    for ally in self.battle.allies:
                        setattr(ally, attr_id, value)
                    print(f"成功将所有队友的 {attr_id} 修改为 {value}")

                else:
                    # 尝试找到对应编号的队友进行修改
                    ally = next((a for a in self.battle.allies if a.number == int(ally_id)), None)
                    if ally:
                        setattr(ally, attr_id, value)
                        print(f"成功将队友编号 {ally_id} 的 {attr_id} 修改为 {value}")
                    else:
                        print(f"未找到编号为 {ally_id} 的队友")

                self.update_ui()

            except ValueError:
                messagebox.showerror("错误", "请输入有效的属性、值和队友编号")
            except Exception as e:
                print(f"修改队友属性失败: {e}")

        tk.Label(debug_window, text="修改敌人属性(编号，属性，值)").grid(row=5, column=0, pady=5)
        enemy_number_entry = tk.Entry(debug_window, width=10)
        enemy_number_entry.grid(row=5, column=1)
        enemy_attribute_id_entry = tk.Entry(debug_window, width=5)
        enemy_attribute_id_entry.grid(row=5, column=2)
        enemy_attribute_value_entry = tk.Entry(debug_window, width=5)
        enemy_attribute_value_entry.grid(row=5, column=3)

        tk.Button(debug_window, text="修改",
                  command=lambda: change_enemy_attributes(
                      enemy_number_entry.get(), enemy_attribute_id_entry.get(), enemy_attribute_value_entry.get())
                  ).grid(row=5, column=4, padx=5)

        def change_enemy_attributes(enemy_id, attr_id, value):
            try:
                value = float(value)
                if enemy_id.lower() == "all" or enemy_id == "" or enemy_id == 0:
                    for enemy in self.battle.enemies:
                        setattr(enemy, attr_id, value)
                    print(f"成功将所有敌人的 {attr_id} 修改为 {value}")

                else:
                    # 尝试找到对应编号的队友进行修改
                    enemy = next((a for a in self.battle.enemies if a.number == int(enemy_id)), None)
                    if enemy:
                        setattr(enemy, attr_id, value)
                        print(f"成功将敌人编号 {enemy_id} 的 {attr_id} 修改为 {value}")
                    else:
                        print(f"未找到编号为 {enemy_id} 的敌人")

                self.update_ui()

            except ValueError:
                messagebox.showerror("错误", "请输入有效的属性、值和敌人编号")
            except Exception as e:
                print(f"修改敌人属性失败: {e}")

        # 战斗结算
        tk.Button(debug_window, text="战斗胜利", command=lambda: self.end_battle("victory")).grid(row=6, column=0, pady=10, padx=5)
        tk.Button(debug_window, text="战斗失败", command=lambda: self.end_battle("defeat")).grid(row=6, column=1, pady=10, padx=5)

    def play_bgm(self, file_path):
        """播放背景音乐"""
        if os.path.exists(file_path):
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play(-1)
        else:
            print(f"文件 {file_path} 未找到！")

    def on_close(self):
        self.end_battle("defeat")

    def redirect_stdout_to_battle_ui(self):
        sys.stdout = TextRedirector(self.log_text)

    def restore_default_stdout(self):
        """恢复系统默认的标准输出"""
        sys.stdout = self.default_stdout  # 恢复默认输出

    def end_battle(self, result):
        pygame.mixer.music.stop()
        if not self.battle_over:
            self.battle_over = True

        # 清空战斗属性加成
        self.player.reset_medicine_effects()
        self.player.reset_skill_bonuses()
        self.battle.clear_all_buffs()

        if hasattr(self, "log_text") and self.log_text.winfo_exists():
            self.log_action(f"战斗结果: {result}")
        self.auto_battle = False
        self.auto_battle_button.config(text="开启自动战斗")
        # 打印掉落物总结
        total_drops = []
        for enemy in self.battle.defeated_enemies:
            drops = self.battle.process_enemy_drops(enemy)
            total_drops.extend(drops)
        # 显示获得的所有掉落物
        if total_drops:
            self.log_action("\n战斗结束，获得以下掉落物:")
            for item_name, quantity in total_drops:
                self.log_action(f"{item_name} x {quantity}")
        # 恢复默认输出
        self.restore_default_stdout()
        self.window.after(2000, self.window.destroy)  # 2秒后关闭窗口
        self.on_battle_end_callback(result)  # 回调通知战斗结束


class TextRedirector:
    """重定向 print 输出到指定的 tkinter Text 控件"""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        """在 ScrolledText 小部件中写入文本"""
        if self.text_widget and self.text_widget.winfo_exists():  # 检查 text_widget 是否存在
            self.text_widget.config(state=tk.NORMAL)  # 允许修改
            self.text_widget.insert(tk.END, text)  # 插入新文本
            self.text_widget.config(state=tk.DISABLED)  # 禁止用户输入
            self.text_widget.yview(tk.END)  # 滚动到文本末尾
        else:
            import logging
            logging.warning("Text widget 已经被销毁，无法写入文本。")

    def flush(self):
        pass
