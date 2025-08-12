import random
from all.gamestate import game_state


class Item:
    def __init__(self, number, name, description, quality, price, quantity):
        self.number = number
        self.name = name
        self.description = description
        self.quality = quality
        self.price = price
        self.quantity = quantity

    def use(self, user, target):
        pass  # Specific effect implemented in subclasses


class Equipment(Item):
    def __init__(self, number, name, description, quality, category, price, quantity, hp, mp, attack, defense, speed,
                 crit, crit_damage, resistance, penetration, target_type=None, target_scope=None, effect_duration=None,
                 effect_changes=None, cost=None):
        super().__init__(number, name, description, quality, price, quantity)
        self.category = category  # e.g., "武器", "防具", "饰品", "法宝"
        self.hp = hp
        self.mp = mp
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.crit = crit
        self.crit_damage = crit_damage
        self.resistance = resistance
        self.penetration = penetration

        # 如果是法宝，则初始化技能效果相关属性
        if category == "法宝":
            self.target_type = target_type
            self.target_scope = target_scope
            self.effect_duration = effect_duration
            self.effect_changes = effect_changes
            self.cost = cost

    def apply_attributes(self, player):
        player.max_hp += self.hp
        player.max_mp += self.mp
        player.attack += self.attack
        player.defense += self.defense
        player.speed += self.speed
        player.crit += self.crit
        player.crit_damage += self.crit_damage
        player.resistance += self.resistance
        player.penetration += self.penetration

    def remove_attributes(self, player):
        player.max_hp -= self.hp
        player.max_mp -= self.mp
        player.attack -= self.attack
        player.defense -= self.defense
        player.speed -= self.speed
        player.crit -= self.crit
        player.crit_damage -= self.crit_damage
        player.resistance -= self.resistance
        player.penetration -= self.penetration

    def use(self, user, target):
        if user.hp <= 0:
            print(f"{user.name} 无法行动，因为他的 HP 为 0 或更低。")
            return

        if self.category != "法宝":
            print(f"{self.name} 不是法宝，无法使用。")
            return

        if isinstance(target, list):
            for t in target:
                self.apply_equipment_effect(user, t)
        else:
            self.apply_equipment_effect(user, target)

    def apply_equipment_effect(self, user, target):
        # 扣除法宝消耗
        for attr, value in self.cost.items():
            if getattr(user, attr) >= value:
                setattr(user, attr, getattr(user, attr) - value)
            else:
                print(f"{user.name} 没有足够的 {attr} 来使用法宝 {self.name}")
                return

        # 确保 target 是 Player 或 Enemy 对象
        if not hasattr(target, 'remove_buffs_by_type'):
            print(f"{target.name} 不是有效的目标，无法使用法宝 {self.name}。")
            return

        # 处理法宝效果
        for attr, effect_change in self.effect_changes.items():
            if attr == "hp" and isinstance(effect_change, dict):
                # 检查 source 是 user 还是 target
                if effect_change.get("source") == "target":
                    base_value = getattr(target, effect_change["attribute"])
                else:
                    base_value = getattr(user, effect_change.get("attribute", "attack"))

                # 根据属性类型调用不同的逻辑
                if effect_change["attribute"] in ["attack", "defense"]:
                    # 基于攻击或防御的技能需要调用计算伤害函数
                    skill_multiplier = effect_change.get("multiplier", 1.0)
                    damage = user.calculate_damage(target, base_value, skill_multiplier=skill_multiplier, is_skill=True)
                    target.hp = max(0, target.hp - damage)
                    print(f"{user.name} 使用了法宝 {self.name} 对 {target.name}，造成了 {damage:.2f} 点伤害。")
                else:
                    # 普通伤害或真实伤害直接影响
                    multiplier = effect_change.get("multiplier", 1.0)
                    change = base_value * multiplier
                    target.hp = max(0, target.hp - change)
                    if change >= 0:
                        print(f"{user.name} 使用了技能 {self.name} 对 {target.name}，造成了 {change:.2f} 点 {attr} 真实伤害！")
                    else:
                        change = -change
                        print(f"{user.name} 使用了技能 {self.name} 对 {target.name}，回复了 {change:.2f}点血量！")

            elif attr == "buff":
                for buff_change in effect_change:
                    if buff_change["action"] == "add":
                        chance = buff_change.get("chance", 1.0)  # 默认 100% 概率
                        if random.random() <= chance:
                            new_buff = Buff(buff_change["name"], buff_change["type"], user, target,
                                            buff_change["duration"], buff_change["effect"])
                            target.add_buff(new_buff)
                            print(f"{target.name} 获得了 {buff_change['name']} buff。")
                        else:
                            print(f"{target.name} 未能获得 {buff_change['name']} buff。")
                    elif buff_change["action"] == "remove":
                        if buff_change["type"] == "all":
                            target.remove_all_buffs()
                        elif buff_change["type"] == "debuff":
                            target.remove_buffs_by_type("debuff")
                        elif buff_change["type"] == "buff":
                            target.remove_buffs_by_type("buff")
                        elif "name" in buff_change:
                            target.remove_buff(buff_name=buff_change["name"])
                        else:
                            target.remove_buff(buff_type=buff_change["type"])
                        print(f"{target.name} 移除了 {buff_change.get('name', buff_change['type'])} buff。")
            else:
                if isinstance(effect_change, dict):
                    base_value = getattr(user, effect_change.get('attribute', 'hp'))
                    multiplier = effect_change.get('multiplier', 1.0)
                    change = base_value * multiplier
                else:
                    change = effect_change
                setattr(target, attr,
                        max(0, min(getattr(target, attr) + change, target.max_hp if attr == 'hp' else target.max_mp)))
                print(f"{user.name} 使用了法宝 {self.name} 对 {target.name}，造成了 {change:.2f} 点 {attr} 变化。")

    def __str__(self):
        return f"{self.name} (ID: {self.number}, 数量: {self.quantity})"


class Medicine(Item):
    def __init__(self, number, name, description, quality, price, quantity, effect_changes):
        super().__init__(number, name, description, quality, price, quantity)
        self.effect_changes = effect_changes  # 记录药品的效果

    def use(self, user, target=None):
        if self.quantity > 0:
            self.apply_medicine_effect(user)  # 将效果应用到用户
            self.quantity -= 1  # 使用一次药品，数量减1
            if self.quantity == 0:
                print(f"{self.name} 已经用完。")
        else:
            print(f"{self.name} 数量不足，无法使用。")

    def apply_medicine_effect(self, user):
        for attr, effect in self.effect_changes.items():
            if attr in ["hp", "mp"]:
                # 直接影响 hp 或 mp
                self.apply_direct_effect(user, attr, effect)
            else:
                # 其他属性影响药品属性汇总
                self.apply_medicine_summary_effect(user, attr, effect)

        print(f"{user.name} 使用了药品 {self.name}，{self.description}")

    def apply_direct_effect(self, user, attr, effect):
        if isinstance(effect, dict):
            source = effect.get("source", "user")
            attribute = effect.get("attribute", attr)
            multiplier = effect.get("multiplier", 1.0)

            base_value = getattr(user, attribute) if source == "user" else 0
            value = base_value * multiplier
        else:
            value = effect

        # 更新玩家的当前 hp 或 mp
        setattr(user, attr, getattr(user, attr) + value)
        print(f"{user.name} 的 {attr} 增加了 {value} 点。")

    def apply_medicine_summary_effect(self, user, attr, effect):
        # 药品属性汇总字段，例如 medicine_attack, medicine_defense 等
        medicine_attr = f"medicine_{attr}"

        # 判断药品属性是否存在于玩家类中
        if hasattr(user, medicine_attr):
            if isinstance(effect, dict):
                source = effect.get("source", "user")
                attribute = effect.get("attribute", attr)
                multiplier = effect.get("multiplier", 1.0)

                base_value = getattr(user, attribute) if source == "user" else 0
                value = base_value * multiplier
            else:
                value = effect

            # 更新对应的药品属性汇总字段
            setattr(user, medicine_attr, getattr(user, medicine_attr) + value)
            print(f"{user.name} 的 {medicine_attr} 增加了 {value} 点。")
        else:
            print(f"玩家没有属性: {medicine_attr}，无法应用 {self.name} 的效果。")


class Material(Item):
    def __str__(self):
        return f"{self.name} (ID: {self.number}, 数量: {self.quantity})"


class Skill(Item):
    def __init__(self, number, name, description, quality, price, quantity, target_type, target_scope, frequency,
                 effect_changes, cost):
        super().__init__(number, name, description, quality, price, quantity)
        self.target_type = target_type
        self.target_scope = target_scope
        self.frequency = frequency
        self.effect_changes = effect_changes
        self.cost = cost

    def use(self, user, target):
        if user.hp <= 0:
            print(f"{user.name} 无法行动，因为他的 HP 为 0 或更低。")
            return

        # 检查技能使用次数
        if self.frequency is not None:
            if self.frequency <= 0:
                print(f"灵力枯竭，该地灵力已经无法支持 {user.name} 使用技能 {self.name}")
                return
            else:
                print(f"{self.name} 的剩余使用次数: {self.frequency}")

        # 计算技能消耗
        for attr, cost_change in self.cost.items():
            if isinstance(cost_change, dict):
                base_value = getattr(user, cost_change.get('attribute', 'hp'))
                multiplier = cost_change.get('multiplier', 1.0)
                cost = base_value * multiplier
            else:
                cost = cost_change

            if getattr(user, attr) >= cost:
                setattr(user, attr, getattr(user, attr) - cost)
                print(f"{user.name} 使用技能 {self.name} 消耗了 {cost:.2f} 点 {attr}。")
            else:
                print(f"{user.name} 没有足够的 {attr} 来使用技能 {self.name}")
                return

        # 确定目标
        if self.target_type == "ally" and self.target_scope == "user":
            targets = [user]  # 目标为使用者自身
        else:
            targets = self.get_targets(user) if self.target_scope == "all" else [target]

        flat_targets = [item for sublist in targets for item in sublist] if isinstance(targets[0], list) else targets

        # 应用技能效果
        for t in flat_targets:
            self.apply_skill_effect(user, t)

        # 减少技能的剩余使用次数
        if self.frequency is not None:
            self.frequency -= 1
            print(f"{self.name} 的使用次数减少为: {self.frequency}")

    def get_targets(self, user):
        if user.battle is None:
            print(f"Error: {user.name} 没有绑定到一个有效的战斗实例。")
            return []
        if self.target_type == "ally" and self.target_scope == "user":
            return [[user]]  # 返回使用者自身作为目标

        if self.target_type == "enemy":
            if type(user).__name__ in ["Enemy", "Boss"]:
                # 敌人和Boss作用于玩家和队友
                targets = [user.battle.player] + user.battle.allies
            elif type(user).__name__ in ["Player", "Ally"]:
                # 玩家和队友作用于敌人和Boss
                targets = user.battle.enemies
        elif self.target_type == "ally":
            if type(user).__name__ in ["Enemy", "Boss"]:
                # 敌人和Boss作用于自己和其他敌人或Boss
                targets = [user] + [enemy for enemy in user.battle.enemies if type(enemy).__name__ in ["Enemy", "Boss"]]
            elif type(user).__name__ in ["Player", "Ally"]:
                # 玩家和队友作用于自己和玩家队友
                targets = [user] + [user.battle.player] + user.battle.allies
        return [targets]

    def apply_skill_effect(self, user, target):
        def get_base_value(effect_change, user, target):
            if isinstance(effect_change, (int, float)):
                return effect_change
            if effect_change.get("source") == "target":
                return getattr(target, effect_change["attribute"])
            return getattr(user, effect_change.get("attribute", "attack"))

        def apply_hp_change(effect_change, user, target):
            base_value = get_base_value(effect_change, user, target)
            multiplier = effect_change.get("multiplier", 1.0) if isinstance(effect_change, dict) else 1.0

            if isinstance(effect_change, dict) and effect_change.get("attribute") in ["attack", "defense"]:
                # 处理普通伤害
                damage = user.calculate_damage(target, base_value, skill_multiplier=multiplier, is_skill=True)
                target.hp = max(0, target.hp - damage)
                print(f"{user.name} 使用了技能 {self.name} 对 {target.name}，造成了 {damage:.2f} 点伤害。")
            else:
                # 处理真实伤害或治疗
                change = base_value * multiplier
                target.hp = max(0, target.hp - change)
                if change >= 0:
                    print(f"{user.name} 使用了技能 {self.name} 对 {target.name}，造成了 {change:.2f} 点真实伤害。")
                else:
                    print(f"{user.name} 使用了技能 {self.name} 对 {target.name}，回复了 {-change:.2f} 点血量。")

        def apply_buff_change(effect_change, target):
            for buff_change in effect_change:
                action = buff_change["action"]
                if action == "add" and random.random() <= buff_change.get("chance", 1.0):
                    new_buff = Buff(buff_change["name"], buff_change["type"], user, target,
                                    buff_change["duration"], buff_change["effect"])
                    target.add_buff(new_buff)
                    print(f"{target.name} 获得了 {buff_change['name']} buff。")
                elif action == "remove":
                    if buff_change["type"] == "all":
                        target.remove_all_buffs()
                    else:
                        target.remove_buffs_by_type(buff_change["type"] or buff_change.get("name"))
                    print(f"{target.name} 移除了 {buff_change.get('name', buff_change['type'])} buff。")

        def apply_general_change(effect_change, target, attr):
            base_value = get_base_value(effect_change, user, target)
            change = effect_change.get("value", base_value * effect_change.get('multiplier', 1.0))

            target_type = type(target).__name__
            if target_type == "Player":
                skill_attr = f'skill_{attr}'
                if hasattr(target, skill_attr):
                    setattr(target, skill_attr, getattr(target, skill_attr, 0) + change)
                    print(f"{user.name} 使用了技能 {self.name}，对 {target.name} 的 {attr} 累积了 {change:.2f} 点变化。")
            elif target_type in ["Enemy", "Boss", "Ally"] and hasattr(target, attr):
                setattr(target, attr, max(0, getattr(target, attr) + change))
                print(f"{user.name} 使用了技能 {self.name}，对 {target.name} 的 {attr} 造成了 {change:.2f} 点变化。")
            else:
                print(f"警告: {target.name} 没有 {attr} 属性，无法应用技能效果。")

        # 主流程
        for attr, effect_change in self.effect_changes.items():
            # 检查 effect_change 是否是列表，如果是，逐一应用
            if isinstance(effect_change, list):
                for single_change in effect_change:
                    if attr == "hp":
                        apply_hp_change(single_change, user, target)
                    elif attr == "buff":
                        apply_buff_change([single_change], target)
                    else:
                        apply_general_change(single_change, target, attr)
            else:
                if attr == "hp":
                    apply_hp_change(effect_change, user, target)
                elif attr == "buff":
                    apply_buff_change(effect_change, target)
                else:
                    apply_general_change(effect_change, target, attr)

    def __str__(self):
        return f"{self.name} (ID: {self.number}, 数量: {self.quantity})"


class Product(Item):
    def __init__(self, number, name, description, quality, price, quantity, target_type, target_scope, effect_changes):
        super().__init__(number, name, description, quality, price, quantity)
        self.target_type = target_type
        self.target_scope = target_scope
        self.effect_changes = effect_changes

    def apply_effect(self, user, target, summon_func=None):
        for attr, effect_change in self.effect_changes.items():
            if attr == "hp" and isinstance(effect_change, dict) and effect_change["attribute"] in ["attack", "defense"]:
                base_value = getattr(user, effect_change.get("attribute", "attack"))
                multiplier = effect_change.get("multiplier", 1.0)
                damage = user.calculate_damage(target, base_value, multiplier, is_skill=True)
                target.hp = max(0, target.hp - damage)
                print(f"{user.name} 使用了道具 {self.name} 对 {target.name}，造成了 {damage:.2f} 点伤害。")
            elif attr == "buff":
                for buff_change in effect_change:
                    if buff_change["action"] == "add":
                        chance = buff_change.get("chance", 1.0)
                        if random.random() <= chance:
                            new_buff = Buff(buff_change["name"], buff_change["type"], user, target,
                                            buff_change["duration"], buff_change["effect"])
                            target.add_buff(new_buff)
                            print(f"{target.name} 获得了 {buff_change['name']} buff。")
                        else:
                            print(f"{target.name} 未能获得 {buff_change['name']} buff。")
                    elif buff_change["action"] == "remove":
                        if buff_change["type"] == "all":
                            target.remove_all_buffs()
                        elif buff_change["type"] == "debuff":
                            target.remove_buffs_by_type("debuff")
                        else:
                            target.remove_buff(buff_change["buff"])
                        print(f"{target.name} 移除了 {buff_change['type']} buff。")
            elif attr == "summon":
                if summon_func:
                    summon_func(user, effect_change)
                    self.quantity += 1  # 召唤令为非一次性物品
                else:
                    print("召唤功能未定义或未传递召唤函数。")
            else:
                if isinstance(effect_change, dict):
                    base_value = getattr(user, effect_change.get('attribute', 'hp'))
                    multiplier = effect_change.get('multiplier', 1.0)
                    change = base_value * multiplier
                else:
                    change = effect_change
                setattr(target, attr,
                        max(0, min(getattr(target, attr) + change, target.max_hp if attr == 'hp' else target.max_mp)))
                print(f"{user.name} 使用了道具 {self.name} 对 {target.name}，造成了 {change:.2f} 点 {attr} 变化。")

    def use(self, user, target, summon_func=None):
        if self.quantity > 0:
            self.apply_effect(user, target, summon_func=summon_func)
            self.quantity -= 1
            if self.quantity == 0:
                user.inventory = [item for item in user.inventory if
                                  not (item.number == self.number and item.quantity == 0)]
        else:
            print(f"{self.name} 数量不足，无法使用。")

    def __str__(self):
        return f"{self.name} (ID: {self.number}, 数量: {self.quantity})"


class Warp(Item):
    def __init__(self, number, name, description, quality, price, quantity, target_map_number):
        super().__init__(number, name, description, quality, price, quantity)
        self.target_map_number = target_map_number  # 目标地图编号

    def use(self, user, target=None):
        if self.quantity > 0:
            print(f"使用 {self.name} 将玩家传送到地图 {self.target_map_number}")
            game_state.move_player_to_map(self.target_map_number)
            self.quantity = 1  # 使用后强制为1，保证折跃令可以一直使用
            if self.quantity == 0:
                print(f"{self.name} 出现错误。")
        else:
            print(f"{self.name} 数量不足，无法使用。")


class Buff:
    def __init__(self, name, buff_type, user, target, duration, effect):
        self.name = name
        self.buff_type = buff_type
        self.user = user
        self.target = target
        self.duration = duration
        self.original_duration = duration  # 初始化时保存原始持续时间
        self.effect = effect
        self.applied = False
        self.original_values = {}

    def apply_effect(self):
        attribute = self.effect["attribute"]

        if "value" in self.effect:
            value = self.effect["value"]
            change = value

            if hasattr(self.target, attribute):
                if not self.applied:
                    # 存储原始值和增量值
                    self.original_values[attribute] = getattr(self.target, attribute)
                    setattr(self.target, attribute, getattr(self.target, attribute) + change)
                    self.applied = True
                    print(f"{self.name} buff 生效: {self.target.name} {attribute} {change:+}")
                elif attribute in ["hp", "mp"]:
                    # 对于 HP 和 MP，每次都进行增量变化
                    setattr(self.target, attribute, max(0, getattr(self.target, attribute) + change))
                    print(f"{self.name} buff 生效: {self.target.name} {attribute} {change:+} ({getattr(self.target, attribute)}/{getattr(self.target, 'max_' + attribute, 'N/A')} {attribute})")
        else:
            # 处理不需要 "value" 的 buff 例如眩晕、麻痹、沉默
            if attribute == "dizzy":
                self.target.dizzy_rounds = max(self.target.dizzy_rounds, self.duration)
                print(f"{self.name} buff 生效: {self.target.name} 正 眩晕 持续 {self.duration} 回合.")
            elif attribute == "paralysis":
                self.target.paralysis_rounds = max(self.target.paralysis_rounds, self.duration)
                print(f"{self.name} buff 生效: {self.target.name} 正 麻痹 持续 {self.duration} 回合.")
            elif attribute == "silence":
                self.target.silence_rounds = max(self.target.silence_rounds, self.duration)
                print(f"{self.name} buff 生效: {self.target.name} 正 沉默 持续 {self.duration} 回合.")
            elif attribute == "blind":
                self.target.blind_rounds = max(self.target.blind_rounds, self.duration)
                print(f"{self.name} buff 生效: {self.target.name} 正 致盲 持续 {self.duration} 回合.")

    def is_expired(self):
        return self.duration == 0

    def decrement_duration(self):
        self.duration -= 1
        if self.duration < 0:
            self.duration = 0
        return self.duration <= 0

    def remove_effect(self):
        attribute = self.effect["attribute"]
        if "value" in self.effect and attribute not in ["hp", "mp"]:
            # 仅当 buff 属性不是 hp 或 mp 时才恢复原始值
            if self.applied:
                original_value = self.original_values.get(attribute)
                current_value = getattr(self.target, attribute)
                change = current_value - original_value

                setattr(self.target, attribute, original_value)
                print(f"{self.name} buff 移除: {self.target.name} {attribute} 恢复至 {original_value}")

                # 更新增量值以考虑其他非 Buff 的变化
                self.original_values[attribute] = current_value - change
                self.applied = False
        elif attribute == "dizzy":
            self.target.dizzy_rounds = 0
            print(f"{self.name} buff 到期移除: {self.target.name} 不再眩晕")
        elif attribute == "paralysis":
            self.target.paralysis_rounds = 0
            print(f"{self.name} buff 到期移除: {self.target.name} 不再麻痹")
        elif attribute == "silence":
            self.target.silence_rounds = 0
            print(f"{self.name} buff 到期移除: {self.target.name} 不再沉默")
        elif attribute == "blind":
            self.target.blind_rounds = 0
            print(f"{self.name} buff 到期移除: {self.target.name} 不再致盲")

    def __str__(self):
        target_name = self.target.name if self.target else "未知目标"
        return f"{self.name} buff 在 {target_name} 持续 {self.duration}/{self.original_duration} 回合"