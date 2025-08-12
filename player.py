import copy
from common.module.item import Equipment, Material, Product, Skill, Medicine, Warp
from common.module.cultivation import CultivationSystem
from library.ally_library import ally_library
from library.skill_library import skill_library
import random


class Player:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.level = 1
        self.exp = 0
        self.max_exp = 100
        self.base_hp = 100
        self.base_mp = 100
        self.base_attack = 100
        self.base_defense = 80
        self.base_speed = 50
        self.base_crit = 5
        self.base_crit_damage = 150
        self.base_resistance = 0
        self.base_penetration = 0
        self.cultivation_point = 0
        self.hp = self.base_hp
        self.mp = self.base_mp
        self.max_hp = self.base_hp
        self.max_mp = self.base_mp
        self.attack = self.base_attack
        self.defense = self.base_defense
        self.speed = self.base_speed
        self.crit = self.base_crit
        self.crit_damage = self.base_crit_damage
        self.resistance = self.base_resistance
        self.penetration = self.base_penetration
        self.equipment = []
        self.inventory = []
        self.skills = []
        self.battle_skills = []  # 战斗中动态技能处理
        self.sustained_effects = []
        self.buffs = []  # 添加 buffs 属性
        self.dizzy_rounds = 0
        self.paralysis_rounds = 0
        self.silence_rounds = 0
        self.blind_rounds = 0
        self.synthesis_slots = [None, None, None]  # 三个合成栏位
        self.battle = None  # 初始化 battle 属性
        self.completed_tasks = []  # 已完成任务
        self.accepted_tasks = []   # 当前接取任务
        self.ready_to_complete_tasks = []  # 新增，存储已完成但未交付的任务
        self.defeated_enemies = {}  # 跟踪每个任务击败的敌人
        self.highest_floor = {}  # 用于记录每个秘境的最高层数
        self.dungeon_clears = {}  # 存储每个秘境的通关状态
        self.dungeons_cleared = set()  # 记录已通关的秘境
        self.talked_to_npcs = set()  # 记录已经对话过的 NPC 编号
        self.given_items = {}  # 记录玩家赠送给 NPC 的物品
        self.npcs_removed = set()  # 记录已经移除的npc
        self.cultivation_system = CultivationSystem(self, skill_library)
        # 任务属性汇总
        self.task_hp = 0
        self.task_mp = 0
        self.task_attack = 0
        self.task_defense = 0
        self.task_speed = 0
        self.task_crit = 0
        self.task_crit_damage = 0
        self.task_resistance = 0
        self.task_penetration = 0
        # 秘境属性汇总
        self.dungeon_hp = 0
        self.dungeon_mp = 0
        self.dungeon_attack = 0
        self.dungeon_defense = 0
        self.dungeon_speed = 0
        self.dungeon_crit = 0
        self.dungeon_crit_damage = 0
        self.dungeon_resistance = 0
        self.dungeon_penetration = 0
        # 修为属性汇总
        self.cultivation_hp = 0
        self.cultivation_mp = 0
        self.cultivation_attack = 0
        self.cultivation_defense = 0
        self.cultivation_speed = 0
        self.cultivation_crit = 0
        self.cultivation_crit_damage = 0
        self.cultivation_resistance = 0
        self.cultivation_penetration = 0
        # 药品属性汇总
        self.medicine_hp = 0
        self.medicine_mp = 0
        self.medicine_attack = 0
        self.medicine_defense = 0
        self.medicine_speed = 0
        self.medicine_crit = 0
        self.medicine_crit_damage = 0
        self.medicine_resistance = 0
        self.medicine_penetration = 0
        # 战斗中技能属性汇总
        self.skill_mp = 0
        self.skill_attack = 0
        self.skill_defense = 0
        self.skill_speed = 0
        self.skill_crit = 0
        self.skill_crit_damage = 0
        self.skill_resistance = 0
        self.skill_penetration = 0
        # 记录玩家位置
        self.map_location = None
        # 记录天数
        self.days = 1
        # 记录故事模式
        self.story_progress = {
            "current_chapter": 1,
            "current_node": 1,
            "completed_nodes": [],
            "chapters_completed": {}
        }

        # dlc1
        self.traits = None
        self.applied_traits = set()
        # dlc2
        self.event = None
        self.event_happened = set()
        # 钩子列表（触发在属性更新后）
        self._after_update_hooks = []

    # 修为系统加载(必须)
    def load_cultivation_from_save_data(self, save_data):
        player_data = save_data.get("player", {})
        self.cultivation_point = player_data.get('cultivation_point', 0)
        cultivation_data = player_data.get("cultivation_system", {})
        self.cultivation_system.restore_from_save(cultivation_data)
        print(f"玩家 {self.name} 的修为系统已从存档中加载。")

    # 记录被移除的npc
    def mark_remove_npc(self, npc_number):
        self.npcs_removed.add(npc_number)

    # 更新故事
    def update_story_progress(self, chapter, node_id):
        self.story_progress["current_chapter"] = chapter
        self.story_progress["current_node"] = node_id
        self.story_progress["chapters_completed"] = {}

    def update_max_exp(self):
        if 1 <= self.level < 10:
            self.max_exp = self.level * 100  # 尘缘境 修炼者开始寻求超脱尘世之道
        elif 10 <= self.level < 20:
            self.max_exp = self.level * 500  # 明灵境 向内修炼灵脉，感悟宇宙的奥秘，灵气和体魄在此阶段得到提升
        elif 20 <= self.level < 30:
            self.max_exp = self.level * 1000  # 空明境 修炼者抛开内心杂念与执念，开始探索道法之力
        elif 30 <= self.level < 40:
            self.max_exp = self.level * 2000  # 灵寂境 灵魂与天地万物的寂静之处相通，能够感受到万物之灵，掌握更深层次的法则
        elif 40 <= self.level < 50:
            self.max_exp = self.level * 4000  # 煌道境 达到灵气如晨曦般透彻明亮的境界，能够明晰深邃黑暗中的大道真理
        elif 50 <= self.level < 60:
            self.max_exp = self.level * 8000  # 玄极境 达到自然灵脉修炼的极限，开始探索玄妙至极的奥秘，获得洞察天地万物的能力
        elif 60 <= self.level < 70:
            self.max_exp = self.level * 16000  # 元始境 回归灵气万物之源，窥见宇宙最初的力量，修炼者可以在这一境界重塑自我
        elif 70 <= self.level < 80:
            self.max_exp = self.level * 32000  # 涅槃境 为追寻大道舍弃肉体凡身，在涅槃火焰中重生，超越了肉体的生死，不入轮回
        elif 80 <= self.level < 90:
            self.max_exp = self.level * 64000  # 太虚境 灵、体、气均融入太虚之中，达到了无限的广袤与虚无，修炼者在此境界中真正实现了与道合一
        elif 90 <= self.level < 100:
            self.max_exp = self.level * 128000  # 天仙境 灵、体、气均通过太虚飞升仙界，掌握真正的道法之力
        elif 100 <= self.level < 200:
            self.max_exp = self.level * 256000  # 真仙境 灵、体、气尽去，修练者本身就是道法

    def gain_exp(self, amount):
        self.exp += amount

        # 可以连续升级
        while self.exp >= self.max_exp:
            self.exp -= self.max_exp
            self.level_up()
            self.update_max_exp()

        self.update_max_exp()

    def level_up(self):
        if self.level < 200:
            self.level += 1
            self.exp = self.exp
            self.base_hp = 100 + (self.level - 1) * 50  # 5050 7550 10050
            self.base_mp = 100 + (self.level - 1) * 20  # 2080 3080 4080
            self.base_attack = 100 + (self.level - 1) * 10  # 1090 1590 2090
            self.base_defense = 80 + (self.level - 1) * 5  # 575 845 1075
            self.base_speed = 50 + (self.level - 1) * 2  # 248 398 448
            self.cultivation_point += 1
            self.cultivation_system.unused_points = self.cultivation_point
            self.update_stats()
            print(f"{self.name} 升级到 {self.level} 级!")
        else:
            return self.level

    # 属性计算
    def update_stats(self):
        # 重置为基础属性
        self.max_hp = self.base_hp
        self.max_mp = self.base_mp
        self.attack = self.base_attack
        self.defense = self.base_defense
        self.speed = self.base_speed
        self.crit = self.base_crit
        self.crit_damage = self.base_crit_damage
        self.resistance = self.base_resistance
        self.penetration = self.base_penetration

        # 增加任务奖励的属性加成
        self.max_hp += self.task_hp
        self.max_mp += self.task_mp
        self.attack += self.task_attack
        self.defense += self.task_defense
        self.speed += self.task_speed
        self.crit += self.task_crit
        self.crit_damage += self.task_crit_damage
        self.resistance += self.task_resistance
        self.penetration = self.task_penetration

        # 增加秘境奖励的属性加成
        self.max_hp += self.dungeon_hp
        self.max_mp += self.dungeon_mp
        self.attack += self.dungeon_attack
        self.defense += self.dungeon_defense
        self.speed += self.dungeon_speed
        self.crit += self.dungeon_crit
        self.crit_damage += self.dungeon_crit_damage
        self.resistance += self.dungeon_resistance
        self.penetration = self.dungeon_penetration

        # 计算药品属性加成
        self.hp += self.medicine_hp
        self.mp += self.medicine_mp
        self.attack += self.medicine_attack
        self.defense += self.medicine_defense
        self.speed += self.medicine_speed
        self.crit += self.medicine_crit
        self.crit_damage += self.medicine_crit_damage
        self.resistance += self.medicine_resistance
        self.penetration += self.medicine_penetration

        # 计算修为属性加成
        self.max_hp += self.cultivation_hp
        self.max_mp += self.cultivation_mp
        self.attack += self.cultivation_attack
        self.defense += self.cultivation_defense
        self.speed += self.cultivation_speed
        self.crit += self.cultivation_crit
        self.crit_damage += self.cultivation_crit_damage
        self.resistance += self.cultivation_resistance
        self.penetration = self.cultivation_penetration

        # 计算技能属性加成
        self.mp += self.skill_mp
        self.attack += self.skill_attack
        self.defense += self.skill_defense
        self.speed += self.skill_speed
        self.crit += self.skill_crit
        self.crit_damage += self.skill_crit_damage
        self.resistance += self.skill_resistance
        self.penetration = self.skill_penetration

        # 计算装备的总属性加成
        for item in self.equipment:
            if isinstance(item, Equipment):
                self.max_hp += item.hp
                self.max_mp += item.mp
                self.attack += item.attack
                self.defense += item.defense
                self.speed += item.speed
                self.crit += item.crit
                self.crit_damage += item.crit_damage
                self.resistance += item.resistance
                self.penetration += item.penetration

        # 玩家不会因装备而死
        if self.max_hp < 0:
            self.max_hp = 1
        if self.max_mp < 0:
            self.max_mp = 1

        # 触发所有的钩子
        self._trigger_after_update_hooks()

        # 如果当前的 hp 和 mp 超过了最大值，进行修正
        self.hp = min(self.hp, self.max_hp)
        self.mp = min(self.mp, self.max_mp)

    # 任务获得属性
    def gain_task_attribute(self, attribute, value):
        if attribute == "hp":
            self.task_hp += value
        elif attribute == "mp":
            self.task_mp += value
        elif attribute == "attack":
            self.task_attack += value
        elif attribute == "defense":
            self.task_defense += value
        elif attribute == "speed":
            self.task_speed += value

        print(f"玩家的 {attribute} 增加了 {value} 点。")
        self.update_stats()

    # 秘境获得属性
    def gain_dungeon_attribute(self, attribute, value):
        if attribute == "hp":
            self.dungeon_hp += value
        elif attribute == "mp":
            self.dungeon_mp += value
        elif attribute == "attack":
            self.dungeon_attack += value
        elif attribute == "defense":
            self.dungeon_defense += value
        elif attribute == "speed":
            self.dungeon_speed += value

        print(f"玩家的 {attribute} 增加了 {value} 点（秘境奖励）。")
        self.update_stats()

    # 移除药品属性
    def reset_medicine_effects(self):
        self.medicine_hp = 0
        self.medicine_mp = 0
        self.medicine_attack = 0
        self.medicine_defense = 0
        self.medicine_speed = 0
        self.medicine_crit = 0
        self.medicine_crit_damage = 0
        self.medicine_resistance = 0
        self.medicine_penetration = 0
        print(f"{self.name} 的所有药品属性已重置。")

    # 移除技能属性
    def reset_skill_bonuses(self):
        self.skill_attack = 0
        self.skill_defense = 0
        self.skill_speed = 0
        self.skill_crit = 0
        self.skill_crit_damage = 0
        self.skill_resistance = 0
        self.skill_penetration = 0
        print(f"{self.name} 的所有技能影响已经移除。")

    def add_to_inventory(self, item):
        for inv_item in self.inventory:
            if inv_item.number == item.number:
                inv_item.quantity += item.quantity
                self.update_stats()
                return

        # 根据物品的类型（category）来区分不同装备
        if isinstance(item, Equipment):
            # 根据装备的类别传递不同的属性
            if item.category == "法宝":
                new_item = Equipment(
                    number=item.number,
                    name=item.name,
                    description=item.description,
                    quality=item.quality,
                    category=item.category,
                    price=item.price,
                    quantity=item.quantity,
                    hp=item.hp,
                    mp=item.mp,
                    attack=item.attack,
                    defense=item.defense,
                    speed=item.speed,
                    crit=item.crit,
                    crit_damage=item.crit_damage,
                    resistance=item.resistance,
                    penetration=item.penetration,
                    target_type=item.target_type,
                    target_scope=item.target_scope,
                    effect_duration=item.effect_duration,
                    effect_changes=item.effect_changes,
                    cost=item.cost
                )
            elif item.category == "武器" or item.category == "防具" or item.category == "饰品":
                # 这些装备不需要 `target_type`, `target_scope` 等属性
                new_item = Equipment(
                    number=item.number,
                    name=item.name,
                    description=item.description,
                    quality=item.quality,
                    category=item.category,
                    price=item.price,
                    quantity=item.quantity,
                    hp=item.hp,
                    mp=item.mp,
                    attack=item.attack,
                    defense=item.defense,
                    speed=item.speed,
                    crit=item.crit,
                    crit_damage=item.crit_damage,
                    resistance=item.resistance,
                    penetration=item.penetration
                )
        elif isinstance(item, Medicine):
            new_item = Medicine(
                number=item.number,
                name=item.name,
                description=item.description,
                quality=item.quality,
                price=item.price,
                quantity=item.quantity,
                effect_changes=item.effect_changes
            )
        elif isinstance(item, Product):
            new_item = Product(
                number=item.number,
                name=item.name,
                description=item.description,
                quality=item.quality,
                price=item.price,
                quantity=item.quantity,
                target_type=item.target_type,
                target_scope=item.target_scope,
                effect_changes=item.effect_changes
            )
        elif isinstance(item, Material):
            new_item = Material(
                number=item.number,
                name=item.name,
                description=item.description,
                quality=item.quality,
                price=item.price,
                quantity=item.quantity
            )
        elif isinstance(item, Skill):
            new_item = Skill(
                number=item.number,
                name=item.name,
                description=item.description,
                price=item.price,
                quantity=item.quantity,
                quality=item.quality,
                target_type=item.target_type,
                target_scope=item.target_scope,
                effect_changes=item.effect_changes,
                frequency=item.frequency,
                cost=item.cost
            )
        elif isinstance(item, Warp):
            new_item = Warp(
                number=item.number,
                name=item.name,
                description=item.description,
                price=item.price,
                quantity=item.quantity,
                quality=item.quality,
                target_map_number=item.target_map_number
            )

        self.inventory.append(new_item)
        print(f"已添加新的物品: {new_item.name}，数量: {new_item.quantity}")
        self.update_stats()

    # 检查背包物品
    def has_item(self, item):
        for inv_item in self.inventory:
            if inv_item.number == item.number:  # 通过物品编号进行比较
                return True
        return False

    def use_item(self, item_number, target=None):
        for item in self.inventory:
            if item.number == item_number:
                item.use(self, target)
                return
        print(f"未找到编号为 {item_number} 的道具。")

    # 检查是否有技能
    def has_skill(self, skill_number):
        # 检查背包中的技能
        for item in self.inventory:
            if item.number == skill_number:
                return True
        # 检查技能栏中的技能
        for skill in self.skills:
            if skill.number == skill_number:
                return True

        return False

    # 添加和移除技能
    def add_to_skill(self, item):
        # 检查技能栏是否已满
        if len(self.skills) >= 9:
            print(f"技能栏已满，无法再装备 {item.name}。")
            return

        # 添加技能并更新属性
        self.skills.append(item)
        self.update_stats()

    def remove_skill(self, skill_number):
        for skill in self.skills:
            if skill.number == skill_number:
                self.skills.remove(skill)
                print(f"已从技能栏移除技能 {skill.name}。")
                return True

        print(f"技能栏中没有编号为 {skill_number} 的技能。")
        return False

    def add_to_equipment(self, item):
        # 计算当前装备种类的数量
        equipment_types = {"武器": 0, "防具": 0, "饰品": 0, "法宝": 0}
        for eq in self.equipment:
            if eq.category in equipment_types:
                equipment_types[eq.category] += 1

        # 检查装备是否超出限制
        if item.category in ["武器", "防具", "饰品"]:
            if equipment_types[item.category] >= 1:
                print(f"{item.category} 已装备，无法再装备 {item.name}。")
                return
        elif item.category == "法宝":
            if equipment_types["法宝"] >= 3:
                print(f"法宝数量已达上限，无法再装备 {item.name}。")
                return

        # 添加装备并更新属性
        self.equipment.append(item)
        self.update_stats()

    # 计算伤害
    def calculate_damage(self, target, base_value, skill_multiplier=1.0, is_skill=False):
        # 计算是否暴击及暴击倍率
        is_critical = random.random() < self.crit / 100.0
        crit_multiplier = self.crit_damage / 100.0 if is_critical else 1.0

        # 计算理论伤害
        theoretical_damage = base_value * skill_multiplier * crit_multiplier

        # 等级压制逻辑
        level_difference = self.level - target.level
        level_suppression = 1.0
        if 20 > level_difference >= 10:
            level_suppression = 1.1  # 高等级对低等级增加10%伤害
        elif -20 < level_difference <= -10:
            level_suppression = 0.9  # 低等级对高等级减少10%伤害
        if 30 > level_difference >= 20:
            level_suppression = 1.2
        elif -30 < level_difference <= -20:
            level_suppression = 0.8
        if 40 > level_difference >= 30:
            level_suppression = 1.3
        elif -40 < level_difference <= -30:
            level_suppression = 0.7
        if 50 > level_difference >= 40:
            level_suppression = 1.4
        elif -50 < level_difference <= -40:
            level_suppression = 0.6
        if level_difference >= 50:
            level_suppression = 1.5
        elif level_difference <= -50:
            level_suppression = 0.5

        # 计算最终伤害
        final_damage = ((theoretical_damage - target.defense) * (1 + (self.penetration - target.resistance) / 100.0)
                        * level_suppression * random.randint(900, 1100)/1000)

        # 确保最终伤害不为负数
        final_damage = max(0.05 * self.attack, final_damage)

        # 打印暴击日志
        if is_critical:
            print(
                f"暴击! {self.name} 对 {target.name} 造成了 {final_damage:.2f} 点伤害（包括暴击倍率 {self.crit_damage}%）")

        return final_damage

    def perform_attack(self, target):
        if self.hp <= 0:
            print(f"{self.name} 无法行动，因为他的 HP 为 0 或更低。")
            return
        if self.blind_rounds > 0:
            print(f"{self.name} 被致盲，无法攻击。")
            return
        else:
            damage = self.calculate_damage(target, self.attack)
            target.hp -= damage
            print(f"{self.name} 攻击了 {target.name}，造成了 {damage:.2f} 点伤害。")
            return damage

    def use_skill(self, skill, target):
        if not self.can_use_skill():
            return
        if skill.target_scope == "all":
            if skill.target_type == "enemy":
                targets = self.battle.enemies
            else:
                targets = [self] + self.battle.allies
            skill.use(self, targets)
        else:
            skill.use(self, target)

    def use_medicine(self, medicine, target):
        if medicine.quantity > 0:
            medicine.use(self, target)  # Use medicine on selected target
            if medicine.quantity == 0:
                self.inventory.remove(medicine)  # 从库存中移除已用完的药品
        else:
            print(f"{medicine.name} 数量不足，无法使用。")

    # buff系统
    def add_buff(self, new_buff):
        # 添加buff
        existing_buff = next((buff for buff in self.buffs if buff.name == new_buff.name), None)
        if existing_buff:
            # 如果有同名 buff，更新其持续时间，但不重复应用属性效果
            existing_buff.duration = new_buff.original_duration
            print(f"{existing_buff.name} buff 被刷新，持续时间更新为 {existing_buff.duration} 回合")
        else:
            # 否则添加新的 buff
            new_buff.target = self  # 设置 buff 的目标为玩家
            self.buffs.append(new_buff)
            print(f"{self.name} 获得了 {new_buff.name} buff。")
            new_buff.apply_effect()  # 立即应用效果

    def remove_buff(self, buff_name=None, buff_type=None):
        if buff_name:
            # 找到并移除指定名称的 Buff，并恢复属性
            self.buffs = [b for b in self.buffs if b.name != buff_name or not b.remove_effect()]
            print(f"{self.name} 移除了 {buff_name} buff。")
        elif buff_type:
            # 找到并移除指定类型的 Buff，并恢复属性
            self.buffs = [b for b in self.buffs if b.buff_type != buff_type or not b.remove_effect()]
            print(f"{self.name} 移除了 {buff_type} 类型的 buffs。")
        else:
            print("未指定 buff 名字或类型，无法移除。")

    def remove_buffs_by_type(self, buff_type):
        buffs_to_remove = [buff for buff in self.buffs if buff.buff_type == buff_type]

        for buff in buffs_to_remove:
            buff.remove_effect()  # 调用 remove_effect 恢复属性
            self.buffs.remove(buff)  # 然后再从列表中移除该 buff

        if buffs_to_remove:
            print(f"{self.name} 移除了所有的 {buff_type} buffs。")
        else:
            print(f"{self.name} 没有 {buff_type} 类型的 buffs 需要移除。")

    def remove_all_buffs(self):
        for buff in self.buffs:
            buff.remove_effect()  # 确保每个 Buff 被正确移除并恢复属性
        self.buffs = []  # 清空 Buff 列表

    def use_equipment(self, equipment, target):
        if equipment.category == "法宝":
            equipment.use(self, target)
        else:
            print(f"{equipment.name} 不是法宝，不能使用。")

    def can_use_skill(self):
        if self.silence_rounds > 0:
            print(f"{self.name} 被沉默，无法使用技能。")
            return False
        return True

    # 材料处理逻辑
    def get_material_quantity(self, material_number):
        quantity = 0
        for item in self.inventory:
            if (isinstance(item, Material) or isinstance(item, Equipment)) and item.number == material_number:
                quantity += item.quantity
        return quantity

    def decrease_material_quantity(self, material_number, amount):
        total_decreased = 0
        for item in self.inventory[:]:
            if (isinstance(item, Material) and item.number == material_number) or (isinstance(item, Equipment) and item.number == material_number):
                if item.quantity > amount - total_decreased:
                    item.quantity -= amount - total_decreased
                    total_decreased = amount
                else:
                    total_decreased += item.quantity
                    self.inventory.remove(item)
                if total_decreased >= amount:
                    break
        return total_decreased >= amount

    # 合成系统
    def set_synthesis_slot(self, slot_index, material):
        if 0 <= slot_index < len(self.synthesis_slots):
            self.synthesis_slots[slot_index] = material

    def clear_synthesis_slots(self):
        self.synthesis_slots = [None, None, None]

    # 道具逻辑 AND 背包逻辑
    def use_product(self, product, target):
        if product.quantity > 0:
            product.use(self, target, summon_func=summon_func)
            if product.quantity == 0:
                self.inventory = [item for item in self.inventory if item.number != product.number]
        else:
            print(f"{product.name} 数量不足，无法使用。")

    def inventory_summary(self, item_type=None):
        summary = {}
        for item in self.inventory:
            if item_type is None or isinstance(item, item_type):
                if item.number in summary:
                    summary[item.number].quantity += item.quantity
                else:
                    # 创建一个新的 Item 对象并复制属性
                    if isinstance(item, Equipment):
                        # 根据装备的类别传递不同的属性
                        if item.category == "法宝":
                            new_item = Equipment(
                                number=item.number,
                                name=item.name,
                                description=item.description,
                                quality=item.quality,
                                category=item.category,
                                price=item.price,
                                quantity=item.quantity,
                                hp=item.hp,
                                mp=item.mp,
                                attack=item.attack,
                                defense=item.defense,
                                speed=item.speed,
                                crit=item.crit,
                                crit_damage=item.crit_damage,
                                resistance=item.resistance,
                                penetration=item.penetration,
                                target_type=item.target_type,
                                target_scope=item.target_scope,
                                effect_duration=item.effect_duration,
                                effect_changes=item.effect_changes,
                                cost=item.cost
                            )
                        elif item.category == "武器" or item.category == "防具" or item.category == "饰品":
                            # 这些装备不需要 `target_type`, `target_scope` 等属性
                            new_item = Equipment(
                                number=item.number,
                                name=item.name,
                                description=item.description,
                                quality=item.quality,
                                category=item.category,
                                price=item.price,
                                quantity=item.quantity,
                                hp=item.hp,
                                mp=item.mp,
                                attack=item.attack,
                                defense=item.defense,
                                speed=item.speed,
                                crit=item.crit,
                                crit_damage=item.crit_damage,
                                resistance=item.resistance,
                                penetration=item.penetration
                            )

                    elif isinstance(item, Medicine):
                        new_item = Medicine(
                            number=item.number,
                            name=item.name,
                            description=item.description,
                            quality=item.quality,
                            price=item.price,
                            quantity=item.quantity,
                            effect_changes=item.effect_changes
                        )
                    elif isinstance(item, Product):
                        new_item = Product(
                            number=item.number,
                            name=item.name,
                            description=item.description,
                            quality=item.quality,
                            price=item.price,
                            quantity=item.quantity,
                            target_type=item.target_type,
                            target_scope=item.target_scope,
                            effect_changes=item.effect_changes
                        )
                    elif isinstance(item, Material):
                        new_item = Material(
                            number=item.number,
                            name=item.name,
                            description=item.description,
                            quality=item.quality,
                            price=item.price,
                            quantity=item.quantity
                        )
                    elif isinstance(item, Skill):
                        new_item = Skill(
                            number=item.number,
                            name=item.name,
                            description=item.description,
                            price=item.price,
                            quantity=item.quantity,
                            quality=item.quality,
                            target_type=item.target_type,
                            target_scope=item.target_scope,
                            effect_changes=item.effect_changes,
                            frequency=item.frequency,
                            cost=item.cost
                        )
                    elif isinstance(item, Warp):
                        new_item = Warp(
                            number=item.number,
                            name=item.name,
                            description=item.description,
                            price=item.price,
                            quantity=item.quantity,
                            quality=item.quality,
                            target_map_number=item.target_map_number
                        )

                    summary[item.number] = new_item
        return summary

    # 获取背包中已有物品
    def get_inventory(self, item_type=None):
        if item_type:
            return [item for item in self.inventory if isinstance(item, item_type)]
        return self.inventory

    def display_inventory(self, item_type=None):
        print("背包:")
        inventory_summary = self.inventory_summary(item_type)
        for i, item in enumerate(inventory_summary.values(), 1):
            print(f"{i}. {item.name} x {item.quantity}")

    # 检测并返回指定物品实例
    def get_inventory_item(self, item_number):
        for item in self.inventory:
            if item.number == item_number:
                return item
        print(f"背包中没有编号为 {item_number} 的物品。")
        return None

    # 检测并返回指定物品数量
    def get_inventory_count(self, item_number):
        """返回玩家的物品数量"""
        for item in self.inventory:
            if item.number == item_number:
                return item.quantity  # 找到物品并返回数量
        return 0  # 若物品不在清单中，返回数量 0

    # 根据序号索引并返回编号
    def get_item_number_by_index(self, index):
        try:
            # 将用户输入的序号（从1开始）转换为列表索引（从0开始）
            item = self.inventory[index - 1]
            return item.number
        except IndexError:
            print("错误：索引超出范围。")
            return None
        except Exception as e:
            print(f"错误：{e}")
            return None

    def remove_from_inventory(self, item_number, quantity):
        for item in self.inventory:
            if item.number == item_number:
                if item.quantity >= quantity:
                    item.quantity -= quantity
                    if item.quantity <= 0:
                        self.inventory.remove(item)  # 如果数量为0或更少，完全移除该物品
                    print(f"已移除 {quantity} 个 {item.name}。")
                    return True
                else:
                    print(f"物品 {item.name} 的数量不足，无法移除 {quantity} 个。")
                    return False

        print(f"背包中没有编号为 {item_number} 的物品。")
        return False

    # 检查击杀
    def check_tasks_for_kill(self, defeated_enemy):
        """战斗中每击败一个敌人调用一次，更新任务状态"""
        for task in self.accepted_tasks:
            for condition in task.completion_conditions:
                if "kill" in condition:
                    kill_condition = condition["kill"]
                    enemy_id = kill_condition["enemy_id"]
                    required_count = kill_condition["count"]

                    # 检查击败的敌人是否符合任务要求
                    if defeated_enemy.number == enemy_id:
                        # 更新击败数量
                        current_count = kill_condition.get("current_count", 0)
                        kill_condition["current_count"] = current_count + 1
                        remaining = required_count - kill_condition["current_count"]
                        print(f"任务 '{task.name}' 更新: 已击败 {enemy_id} 剩余数量: {remaining}")

                        # 检查任务是否完成
                        if kill_condition["current_count"] >= required_count:
                            print(f"任务 '{task.name}' 完成条件已满足。")

    def update_tasks_after_battle(self):
        for task in self.accepted_tasks[:]:  # 使用副本来安全地移除已完成的任务
            if task.check_completion(self):
                print(f"任务 '{task.name}' 已完成！")
                task.complete(self)
            else:
                print(f"任务 '{task.name}' 未完成。")

    # 检查对话
    def talk_to_npc(self, npc_number):
        self.talked_to_npcs.add(npc_number)

    def has_talked_to_npc(self, npc_number):
        return npc_number in self.talked_to_npcs

    # 检查秘境
    def update_highest_floor(self, dungeon_id, floor_number):
        if dungeon_id not in self.highest_floor:
            self.highest_floor[dungeon_id] = floor_number
        else:
            self.highest_floor[dungeon_id] = max(self.highest_floor[dungeon_id], floor_number)
        print(f"玩家在此秘境的最高层数已更新为 {self.highest_floor[dungeon_id]}。")

    def mark_dungeon_cleared(self, dungeon_id):
        self.dungeons_cleared.add(dungeon_id)
        print(f"您神通广大，用出数个手段将秘境妖魔尽数斩杀，威震三界！")

    # 检查赠送
    def give_item_to_npc(self, npc_id, item_number, quantity):
        """记录玩家赠送给指定 NPC 的物品和数量"""
        if npc_id not in self.given_items:
            self.given_items[npc_id] = {}

        if item_number not in self.given_items[npc_id]:
            self.given_items[npc_id][item_number] = 0

        self.given_items[npc_id][item_number] += quantity

        print(f"玩家赠送 {quantity} 个物品（ID: {item_number}）给 NPC（ID: {npc_id}）")

    def get_item_given_to_npc(self, npc_id, item_number):
        """返回玩家已赠送给指定 NPC 的某个物品的数量"""
        if npc_id in self.given_items and item_number in self.given_items[npc_id]:
            return self.given_items[npc_id][item_number]
        return 0

    # dlc
    def register_after_update_hook(self, hook):
        """注册一个在属性更新后触发的钩子"""
        self._after_update_hooks.append(hook)

    def _trigger_after_update_hooks(self):
        """触发所有注册的钩子"""
        for hook in self._after_update_hooks:
            hook(self)

    def __str__(self):
        return (f"Player({self.number}, {self.name}, Level: {self.level}, Exp: {self.exp}, "
                f"HP: {self.hp}/{self.max_hp},MP: {self.mp}/{self.max_mp}, ATK: {self.attack}, "
                f"DEF: {self.defense}, SPD: {self.speed}, CRIT: {self.crit}%, CRIT DMG: {self.crit_damage}%, "
                f"RES: {self.resistance}%, PEN: {self.penetration}%)")


# 召唤相关
def summon_func(user, effect_change):
    summon_number = effect_change.get('number')

    if summon_number in ally_library:
        # 检测战斗中是否已存在相同的队友
        for ally in user.battle.allies:
            if ally.number == summon_number:
                summoned_ally = copy.copy(ally_library[summon_number])
                print(f"{summoned_ally.name} 已经在战斗中，无法再次召唤。")
                return

        summoned_ally = copy.copy(ally_library[summon_number])
        if len(user.battle.allies) < 3:  # 限制队友数量
            user.battle.allies.append(summoned_ally)
            user.battle.update_turn_order()  # 更新回合顺序
            print(f"{user.name} 召唤了 {summoned_ally.name} 进入战斗！")
        else:
            print("友方队伍已达到上限，无法召唤更多队友。")
    else:
        print("无效的召唤编号，无法召唤队友。")
