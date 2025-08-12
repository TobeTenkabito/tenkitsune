from .enemy import Enemy
from library.enemy_library import enemy_library
import random
import copy


class Boss:
    def __init__(self, number, name, description, level, hp, mp, max_hp, max_mp, attack, defense, speed, crit, crit_damage, resistance,
                 penetration, drops, chance_drops, exp_drops,
                 skills=None, equipment=None, summon_list=None, logic_module=None):
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
        self.crit = crit
        self.crit_damage = crit_damage
        self.resistance = resistance
        self.penetration = penetration
        self.drops = drops
        self.chance_drops = chance_drops if chance_drops else []
        self.exp_drops = exp_drops
        self.skills = skills if skills is not None else []
        self.equipment = equipment if equipment is not None else []
        self.summon_list = summon_list if summon_list is not None else []
        self.logic_module = logic_module
        self.dizzy_rounds = 0
        self.paralysis_rounds = 0
        self.silence_rounds = 0
        self.blind_rounds = 0
        self.sustained_effects = []
        self.buffs = []
        self.battle = None

    def __deepcopy__(self, memo):
        # 创建一个新的 Boss 实例，通过构造函数传入深拷贝的属性
        new_boss = type(self)(
            self.number,
            self.name,
            self.description,
            self.level,
            self.hp,
            self.mp,
            self.max_hp,
            self.max_mp,
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
            copy.deepcopy(self.skills, memo),
            copy.deepcopy(self.equipment, memo),
            self.summon_list  # 召唤列表不进行深拷贝，按需求可以修改
        )

        new_boss.dizzy_rounds = self.dizzy_rounds
        new_boss.paralysis_rounds = self.paralysis_rounds
        new_boss.silence_rounds = self.silence_rounds
        new_boss.blind_rounds = self.blind_rounds
        new_boss.sustained_effects = copy.deepcopy(self.sustained_effects, memo)
        new_boss.buffs = copy.deepcopy(self.buffs, memo)
        new_boss.logic_module = self.logic_module
        new_boss.battle = self.battle
        return new_boss

    def use_equipment(self, equipment, target):
        equipment.use(self, target)

    def summon(self):
        summoned_enemies = []
        for enemy_id in self.summon_list:
            template_enemy = enemy_library[enemy_id]
            new_enemy = Enemy(
                number=template_enemy.number,
                name=template_enemy.name,
                description=template_enemy.description,
                level=template_enemy.level,
                max_hp=template_enemy.max_hp,
                max_mp=template_enemy.max_mp,
                hp=template_enemy.hp,
                mp=template_enemy.mp,
                attack=template_enemy.attack,
                defense=template_enemy.defense,
                speed=template_enemy.speed,
                crit=template_enemy.crit,
                crit_damage=template_enemy.crit_damage,
                resistance=template_enemy.resistance,
                penetration=template_enemy.penetration,
                drops=copy.deepcopy(template_enemy.drops),
                chance_drops=copy.deepcopy(template_enemy.chance_drops),
                exp_drops=template_enemy.exp_drops,
                skills=copy.deepcopy(template_enemy.skills)
            )
            new_enemy.battle = self.battle
            summoned_enemies.append(new_enemy)
        return summoned_enemies

    def execute_logic(self, battle):
        if self.logic_module:
            self.logic_module.boss_logic(self, battle)

    def remove_buffs_by_type(self, buff_type):
        buffs_to_remove = [buff for buff in self.buffs if buff.buff_type == buff_type]

        for buff in buffs_to_remove:
            buff.remove_effect()  # 调用 remove_effect 恢复属性
            self.buffs.remove(buff)  # 然后再从列表中移除该 buff

        if buffs_to_remove:
            print(f"{self.name} 移除了所有的 {buff_type} buffs。")
        else:
            print(f"{self.name} 没有 {buff_type} 类型的 buffs 需要移除。")

    def can_use_skill(self):
        if self.silence_rounds > 0:
            print(f"{self.name} 被沉默，无法使用技能。")
            return False
        return True

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

    def boss_action(self, battle):
        self.execute_logic(battle)

    def add_buff(self, new_buff):
        if self.buffs is not None:
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
        else:
            print("该boss修为高深莫测，无法被添加buff")

    def abolish_buffs(self):
        self.buffs = None

    def refresh_buffs(self):
        self.buffs = []

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