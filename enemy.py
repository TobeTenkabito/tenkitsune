import random
import uuid
import copy


class Enemy:
    def __init__(self, number, name, description, level, hp, mp, max_hp, max_mp, attack, defense, speed, crit, crit_damage, resistance,
                 penetration, drops, chance_drops, exp_drops, skills=None):
        self.number = number
        self.name = name
        self.description = description
        self.level = level
        self.hp = hp
        self.mp = mp
        self.max_hp = max_hp
        self.max_mp = max_mp
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.crit = crit  # Percentage
        self.crit_damage = crit_damage  # Percentage
        self.resistance = resistance
        self.penetration = penetration
        self.drops = drops  # [(item_number, quantity)]
        self.chance_drops = chance_drops if chance_drops else []
        self.exp_drops = exp_drops
        self.skills = skills if skills is not None else []
        self.battle_skills = []  # 战斗中动态技能处理
        self.equipment = []
        self.sustained_effects = []
        self.buffs = []  # 添加 buffs 属性
        self.dizzy_rounds = 0
        self.paralysis_rounds = 0
        self.silence_rounds = 0
        self.blind_rounds = 0
        self.battle = None  # 初始化 battle 属性
        self.unique_id = uuid.uuid4()  # 为每个敌人分配一个唯一ID
        self.module_object = None  # 假设有个模块对象导致 deep copy 问题

    def __deepcopy__(self, memo):
        # 自定义 deepcopy 方法
        # 手动拷贝非模块对象的属性，排除 module_object
        new_enemy = type(self)(
            self.number,
            self.name,
            self.description,
            self.level,
            self.max_hp,
            self.max_mp,
            self.hp,
            self.mp,
            self.attack,
            self.defense,
            self.speed,
            self.crit,
            self.crit_damage,
            self.resistance,
            self.penetration,
            copy.deepcopy(self.drops, memo),
            copy.deepcopy(self.chance_drops, memo),
            self.exp_drops,
            copy.deepcopy(self.skills, memo)
        )

        # 深拷贝其他状态和效果相关的属性
        new_enemy.dizzy_rounds = self.dizzy_rounds
        new_enemy.paralysis_rounds = self.paralysis_rounds
        new_enemy.silence_rounds = self.silence_rounds
        new_enemy.blind_rounds = self.blind_rounds
        new_enemy.sustained_effects = copy.deepcopy(self.sustained_effects, memo)
        new_enemy.buffs = copy.deepcopy(self.buffs, memo)

        # 将不可深拷贝的属性设为 None 或适当的值
        new_enemy.battle = self.battle
        new_enemy.module_object = None  # 假设 module_object 是个不可拷贝的模块

        return new_enemy

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

    def use_equipment(self, equipment, target):
        if self.hp <= 0:
            print(f"{self.name} 无法行动，因为他的 HP 为 0 或更低。")
            return

        if equipment.category == "法宝":
            # 扣除消耗
            for attr, value in equipment.cost.items():
                if getattr(self, attr) >= value:
                    setattr(self, attr, getattr(self, attr) - value)
                else:
                    print(f"{self.name} 没有足够的 {attr} 来使用 {equipment.name}")
                    return

            if isinstance(target, list):
                for t in target:
                    self.apply_equipment_effect(equipment, t)
            else:
                self.apply_equipment_effect(equipment, target)

    def apply_equipment_effect(self, equipment, target):
        for attr, effect_change in equipment.effect_changes.items():
            if attr == "hp" and isinstance(effect_change, dict) and effect_change["attribute"] in ["attack", "defense"]:
                base_value = getattr(self, effect_change.get("attribute", "attack"))
                skill_multiplier = effect_change.get("multiplier", 1.0)
                damage = self.calculate_damage(target, base_value, skill_multiplier=skill_multiplier, is_skill=True)
                target.hp = max(0, target.hp - damage)
                print(f"{self.name} 使用了法宝 {equipment.name} 对 {target.name}，造成了 {damage:.2f} 点伤害。")
            else:
                if isinstance(effect_change, dict):
                    base_value = getattr(self, effect_change.get('attribute', 'hp'))
                    multiplier = effect_change.get('multiplier', 1.0)
                    change = base_value * multiplier
                else:
                    change = effect_change
                setattr(target, attr, max(0, min(getattr(target, attr) + change, target.max_hp if attr == 'hp' else target.max_mp)))
                print(f"{self.name} 使用了法宝 {equipment.name} 对 {target.name}，造成了 {change:.2f} 点 {attr} 变化。")

    def add_buff(self, new_buff):
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

    def remove_buffs_by_type(self, buff_type):
        buffs_to_remove = [buff for buff in self.buffs if buff.buff_type == buff_type]

        for buff in buffs_to_remove:
            buff.remove_effect()  # 调用 remove_effect 恢复属性
            self.buffs.remove(buff)  # 然后再从列表中移除该 buff

        if buffs_to_remove:
            print(f"{self.name} 移除了所有的 {buff_type} buffs。")
        else:
            print(f"{self.name} 没有 {buff_type} 类型的 buffs 需要移除。")

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

    def remove_all_buffs(self):
        for buff in self.buffs:
            buff.remove_effect()  # 确保每个 Buff 被正确移除并恢复属性
        self.buffs = []  # 清空 Buff 列表

    def can_use_skill(self):
        if self.silence_rounds > 0:
            print(f"{self.name} 被沉默，无法使用技能。")
            return False
        return True

    def use_skill(self, skill, target):
        if not self.can_use_skill():
            return
        skill.use(self, target)

    def __str__(self):
        return (f"Enemy({self.number}, {self.name}, {self.description}, Level: {self.level}, HP: {self.hp}/{self.max_hp}, MP: {self.mp}/{self.max_mp}, ATK: {self.attack}, "
                f"DEF: {self.defense}, SPD: {self.speed}, CRIT: {self.crit}%, CRIT DMG: {self.crit_damage}%, RES: {self.resistance}%, PEN: {self.penetration}%)")
