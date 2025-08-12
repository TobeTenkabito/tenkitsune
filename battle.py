from common.character.player import Player
from .item import Skill, Equipment, Medicine, Product, Material, Warp
from library.material_library import material_library
from library.equipment_library import equipment_library
from library.product_library import product_library
from library.warp_library import warp_library
from library.medicine_library import medicine_library
from library.skill_library import skill_library
from common.character.boss import Boss
from common.character.ally import Ally
import random
import copy


class Battle:
    def __init__(self, player, allies, enemies):
        self.player = player
        self.allies = [copy.deepcopy(ally) for ally in allies]
        self.enemies = [copy.deepcopy(enemy) for enemy in enemies]
        # 确保至少有玩家或敌人存在，否则报错
        if not self.player and not self.enemies:
            raise ValueError("没有玩家或敌人，无法开始战斗")
        self.defeated_enemies = []  # 用于存储被击败的敌人
        self.turn_order = []
        self.auto_battle = False  # 添加自动战斗标志
        # 将 battle 属性添加到所有参与者
        if self.player is not None:
            self.player.battle = self
        for ally in self.allies:
            ally.battle = self
        for enemy in self.enemies:
            enemy.battle = self
        # 为技能创建战斗中的副本
        if self.player:
            self.player.battle_skills = [copy.deepcopy(skill) for skill in self.player.skills]
            self.player.battle = self
        for ally in self.allies:
            ally.battle_skills = [copy.deepcopy(skill) for skill in ally.skills]
            ally.battle = self
        for enemy in self.enemies:
            enemy.battle_skills = [copy.deepcopy(skill) for skill in enemy.skills]
            enemy.battle = self
        self.determine_turn_order()

    def determine_turn_order(self):
        participants = [p for p in ([self.player] + self.allies + self.enemies) if p is not None]
        # 打印每个参与者的信息，确认他们是否有 `speed` 属性
        for p in participants:
            if not hasattr(p, 'speed'):
                print(f"错误: {p.name} 缺少 speed 属性")
                raise ValueError(f"{p.name} 缺少 speed 属性，无法计算回合顺序")
        self.turn_order = sorted(participants, key=lambda x: x.speed, reverse=True)
        print(f"回合顺序: {[p.name for p in self.turn_order]}")

    def display_player_status(self):
        print(f"\n玩家状态: {self.player}")
        for ally in self.allies:
            print(f"\n队友状态: {ally}")

    def check_hp_mp_limits(self):
        # 预留10%的最大生命值作为护盾
        if self.player.hp > 1.1*self.player.max_hp:
            self.player.hp = 1.1*self.player.max_hp
        if self.player.mp > self.player.max_mp:
            self.player.mp = self.player.max_mp

        for ally in self.allies:
            if ally.hp > 1.1*ally.max_hp:
                ally.hp = 1.1*ally.max_hp
            if ally.mp > ally.max_mp:
                ally.mp = ally.max_mp

        for enemy in self.enemies:
            if enemy.hp > 1.1*enemy.max_hp:
                enemy.hp = 1.1*enemy.max_hp
            if enemy.mp > enemy.max_mp:
                enemy.mp = enemy.max_mp

    def player_action(self):
        if self.auto_battle:
            self.auto_action()
            return True

        while True:
            self.display_player_status()
            print(f"{self.player.name} 的回合！请选择行动:")
            print("1. 攻击")
            print("2. 使用技能")
            print("3. 使用法宝")
            print("4. 使用药品")
            print("5. 使用道具")
            print("6. 开启/关闭自动战斗")
            print("7. 返回上一级")
            print("8. 结束战斗")
            choice = input("请输入选项编号: ")

            if choice == '1':
                target = self.choose_target("enemy")
                if target:
                    self.player.perform_attack(target)
                return True
            if choice == '2':
                skills = [item for item in self.player.battle_skills if isinstance(item, Skill)]
                if not skills:
                    print("你没有技能可以使用。")
                    continue
                skill = self.choose_skill_or_equipment(skills)
                if skill:
                    target = self.choose_target(skill.target_type, skill.target_scope)
                    if target:
                        self.player.use_skill(skill, target)
                return True
            elif choice == '3':  # 使用法宝
                # 只展示装备区内的法宝
                equipments = [item for item in self.player.equipment if
                              isinstance(item, Equipment) and item.category == "法宝"]
                if not equipments:
                    print("你没有法宝可以使用。")
                    continue
                equipment = self.choose_skill_or_equipment(equipments)
                if equipment:
                    target = self.choose_target(equipment.target_type, equipment.target_scope)
                    if target:
                        self.player.use_equipment(equipment, target)
                return True
            elif choice == '4':
                medicines = [item for item in self.player.inventory if isinstance(item, Medicine)]
                if not medicines:
                    print("你没有药品可以使用。")
                    continue
                medicine = self.choose_skill_or_equipment(medicines)
                if medicine:
                    target = self.choose_target("ally")
                    if target:
                        self.player.use_medicine(medicine, target)
                return True
            elif choice == '5':
                products = [item for item in self.player.inventory if isinstance(item, Product)]
                if not products:
                    print("你没有道具可以使用。")
                    continue
                product = self.choose_skill_or_equipment(products)
                if product:
                    target = self.choose_target("enemy")
                    if target:
                        self.player.use_product(product, target)
                return True
            elif choice == '6':
                self.auto_battle = not self.auto_battle
                status = "开启" if self.auto_battle else "关闭"
                print(f"自动战斗已{status}")
                return True
            elif choice == '7':
                return "back"
            elif choice == '8':  # 新增结束战斗逻辑
                if all(enemy.hp <= 0 for enemy in self.enemies):
                    print("战斗结束！即将进入结算...")
                    return "end_battle"
                else:
                    print("现在还不是结束战斗的时候，敌人尚未全部被击败。")
            else:
                print("无效的选择。请重试。")

    def choose_target(self, target_type="enemy", target_scope="single"):
        # 如果目标是用户自己，则直接返回用户
        if target_type == "ally" and target_scope == "user":
            return self.player

        while True:
            if target_scope == "all":
                print("选择目标:")
                print("1. 全体")
                print("0. 返回上一级")
                choice = int(input("请输入选项编号: "))
                if choice == 0:
                    return None
                elif choice == 1:
                    if target_type == "enemy":
                        return self.enemies
                    elif target_type == "ally":
                        return [self.player] + self.allies
            else:
                if target_type == "enemy":
                    print("选择攻击的敌人:")
                    for i, enemy in enumerate(self.enemies):
                        if enemy.hp > 0:
                            print(f"{i + 1}. {enemy.name} (HP: {enemy.hp}/{enemy.max_hp})")
                    print("0. 返回上一级")
                    choice = int(input("请输入选项编号: "))
                    if choice == 0:
                        return None
                    return self.enemies[choice - 1]
                elif target_type == "ally":
                    print("选择目标:")
                    print(f"1. {self.player.name} (HP: {self.player.hp}/{self.player.max_hp})")
                    for i, ally in enumerate(self.allies):
                        print(f"{i + 2}. {ally.name} (HP: {ally.hp}/{ally.max_hp})")
                    print("0. 返回上一级")
                    choice = int(input("请输入选项编号: "))
                    if choice == 0:
                        return None
                    if choice == 1:
                        return self.player
                    return self.allies[choice - 2]

    def choose_skill_or_equipment(self, items):
        while True:
            print("选择使用的技能、法宝或道具:")
            for i, item in enumerate(items):
                print(f"{i + 1}. {item.name} - {item.description}")
            print("0. 返回上一级")
            choice = int(input("请输入选项编号: "))
            if choice == 0:
                return None
            return items[choice - 1]

    def enemy_action(self, enemy):
        if enemy.hp <= 0:
            return

        if isinstance(enemy, Boss):
            if len(self.enemies) < 5:
                enemy.boss_action(self)
            else:
                print(f"{enemy.name} 无法召唤更多小怪，因为场上敌人数量已达上限。")
                enemy.perform_attack(random.choice([self.player] + self.allies))  # 攻击玩家或队友
        else:
            if enemy.battle_skills and random.random() < 0.5:  # 50% 的概率使用技能
                skill = random.choice(enemy.battle_skills)
                targets = [self.player] + self.allies if skill.target_scope == "all" and skill.target_type == "enemy" else [random.choice([self.player] + self.allies)]
                enemy.use_skill(skill, targets)
            else:
                enemy.perform_attack(random.choice([self.player] + self.allies))  # 攻击玩家或队友

    def ally_action(self, ally):
        if ally.hp <= 0:
            return

        if ally.battle_skills and random.random() < 0.5:  # 50% 的概率使用技能
            skill = random.choice(ally.battle_skills)
            if skill.target_scope == "all":
                target = self.enemies if skill.target_type == "enemy" else [self.player] + self.allies
            else:
                target = random.choice(self.enemies) if self.enemies else None
            if target:
                ally.use_skill(skill, target)
        else:
            if self.enemies:
                target = random.choice(self.enemies)
                ally.perform_attack(target)

    def check_battle_status(self):
        # 战斗失败条件：玩家和所有队友的 HP 都为 0 或更低
        if self.player.hp <= 0 and all(ally.hp <= 0 for ally in self.allies):
            print("玩家和队友战败!")
            return "loss"

        # 战斗胜利条件：所有敌人都被移除
        if len(self.enemies) == 0:
            print("玩家和队友胜利!")
            return "win"

        return "ongoing"

    # 战斗逻辑处理
    def run_battle(self):
        # 将当前 battle 对象分配给所有队友和敌人
        for ally in self.allies:
            ally.battle = self  # 设置每个 ally 的 battle 引用
        for enemy in self.enemies:
            enemy.battle = self  # 设置每个 enemy 的 battle 引用
        self.determine_turn_order()
        battle_status = "ongoing"
        turn_count = 1

        while battle_status == "ongoing":
            print(f"\n第 {turn_count} 回合开始!")
            print("当前回合顺序:", [p.name for p in self.turn_order])  # 行动条

            # 回合开始检查属性
            self.apply_buffs()
            self.player.update_stats()
            self.check_hp_mp_limits()

            i = 0
            while i < len(self.turn_order):
                participant = self.turn_order[i]
                if participant.hp > 0:
                    if participant.dizzy_rounds > 0:
                        print(f"{participant.name} 被眩晕，无法行动。")
                        participant.dizzy_rounds -= 1
                    elif participant.paralysis_rounds > 0 and random.random() < 0.5:
                        print(f"{participant.name} 被麻痹，无法行动。")
                    elif isinstance(participant, Player):
                        player_action_result = self.player_action()
                        if player_action_result == "back":
                            continue
                        elif player_action_result == "end_battle":
                            battle_status = "win"
                            break
                    elif isinstance(participant, Ally):
                        self.ally_action(participant)
                    else:
                        self.enemy_action(participant)

                    # 检查战斗状态（每个行动后都需要检查一次）
                    battle_status = self.check_battle_status()
                    if battle_status != "ongoing":
                        break

                i += 1

            if battle_status == "ongoing":
                self.remove_dead_participants()
                self.update_turn_order()

                turn_count += 1

        # 清除所有 Buff
        self.clear_all_buffs()

        # 重置药品效果
        for participant in self.turn_order:
            if isinstance(participant, Player):
                participant.reset_medicine_effects()
                participant.reset_skill_bonuses()

        # 战斗结束后统一处理
        if battle_status == "win":
            self.process_victory()
            return battle_status
        elif battle_status == "loss":
            print("你被击败了。")
            return battle_status

    def process_victory(self):
        enemy_defeat_summary = {}
        total_exp = 0

        # 遍历已击败的敌人，统计数据（经验、掉落、击败的敌人）
        for enemy in self.defeated_enemies:
            # 累加经验值（这里仅做统计，实际经验已经在击败敌人时发放）
            total_exp += enemy.exp_drops

            # 统计击败的敌人种类
            enemy_name = enemy.name
            if enemy_name in enemy_defeat_summary:
                enemy_defeat_summary[enemy_name] += 1
            else:
                enemy_defeat_summary[enemy_name] = 1

        # 打印总结：获得总经验
        print(f"获得总经验: {total_exp}")

        # 打印总结：击败的敌人统计
        print("\n击败的敌人统计:")
        for enemy_name, count in enemy_defeat_summary.items():
            print(f"{enemy_name}: {count} 个")

        # 战斗结束后，检查任务完成状态（仅检查任务状态，实际更新已经在击败时完成）
        self.player.update_tasks_after_battle()

        # 打印玩家状态更新后的信息
        print("\n战斗结束后的玩家状态:")
        print(self.player)

        # 打印玩家背包状态
        print("\n玩家背包状态:")
        self.player.display_inventory()

    def apply_buffs(self):
        for participant in self.turn_order:
            if hasattr(participant, "buffs"):
                for buff in participant.buffs[:]:
                    if buff.target is None:
                        print(f"警告: Buff {buff.name} 没有可选目标.")
                        continue
                    buff.apply_effect()
                    if buff.decrement_duration() or buff.is_expired():
                        buff.remove_effect()
                        participant.buffs.remove(buff)
                        print(f"{buff.name} buff 移除: {participant.name} 不再被 {buff.name} 影响")
                    else:
                        print(buff)

    def clear_all_buffs(self):
        for participant in [self.player] + self.allies + self.enemies:
            participant.remove_all_buffs()
            print(f"所有 Buff 已被清除: {participant.name}")

    def update_turn_order(self):
        participants = ([self.player] + [ally for ally in self.allies if ally.hp > 0] +
                        [enemy for enemy in self.enemies if enemy.hp > 0])
        self.turn_order = sorted(participants, key=lambda x: x.speed, reverse=True)
        print("更新后的回合顺序:", [p.name for p in self.turn_order])

    # 移除死亡实例
    def remove_dead_participants(self):
        for enemy in self.enemies[:]:
            if enemy.hp <= 0:
                self.player.gain_exp(enemy.exp_drops)
                self.player.check_tasks_for_kill(enemy)
                self.process_enemy_drops(enemy)
                self.defeated_enemies.append(enemy)
                self.enemies.remove(enemy)

        self.allies = [ally for ally in self.allies if ally.hp > 0]

        if self.player.hp <= 0:
            print(f"{self.player.name} 已经倒下！")

    # 处理死亡掉落
    def process_enemy_drops(self, enemy):
        drop_summary = {}

        # 处理固定掉落
        for drop_number, quantity in enemy.drops:
            drop_summary[drop_number] = drop_summary.get(drop_number, 0) + quantity

        # 处理概率掉落
        for drop_number, quantity, chance in enemy.chance_drops:
            if random.random() < chance:
                drop_summary[drop_number] = drop_summary.get(drop_number, 0) + quantity

        # 处理所有掉落物，并返回掉落的物品和数量
        drops = []

        for drop_number, total_quantity in drop_summary.items():
            item = self.get_item_by_id(drop_number)

            if item is None:
                print(f"无法识别的掉落物 ID: {drop_number}")
                continue

            # 深拷贝物品，确保实例独立
            new_item = copy.deepcopy(item)

            # 处理不同类型的物品
            if isinstance(new_item, (Material, Product)):
                new_item.quantity = total_quantity
                self.player.add_to_inventory(new_item)
                drops.append((new_item.name, total_quantity))
                print(f"获得物品: {new_item.name} x {total_quantity}")

            elif isinstance(new_item, Equipment):
                for _ in range(total_quantity):
                    equipment_copy = copy.copy(new_item)
                    self.player.add_equipment(equipment_copy)
                    drops.append((new_item.name, 1))
                    print(f"获得装备: {new_item.name}")

            elif isinstance(new_item, (Medicine, Warp, Skill)):
                # 对于这些物品，可以优化为一次添加，避免多次循环
                for _ in range(total_quantity):
                    item_copy = copy.copy(new_item)
                    self.player.add_to_inventory(item_copy)
                    drops.append((new_item.name, 1))
                    print(f"获得物品: {new_item.name}")

        return drops

    def get_item_by_id(self, item_id):
        if item_id in material_library:
            return material_library[item_id]
        elif item_id in equipment_library:
            return equipment_library[item_id]
        elif item_id in product_library:
            return product_library[item_id]
        elif item_id in warp_library:
            return warp_library[item_id]
        elif item_id in medicine_library:
            return medicine_library[item_id]
        elif item_id in skill_library:
            return skill_library[item_id]
        else:
            return None

    # 自动战斗
    def auto_action(self):
        def process_drops(enemy):
            drops = self.process_enemy_drops(enemy)
            return drops

        def get_base_value(effect_change, user, target):
            """
            根据 effect_change 中的 source 和 attribute，获取对应的 base_value。
            如果 source 是 'target'，则从 target 获取属性；否则从 user 获取属性。
            """
            if effect_change.get("source") == "target":
                return getattr(target, effect_change["attribute"], 0)  # 如果属性不存在，返回0
            return getattr(user, effect_change.get("attribute", "attack"), 0)  # 默认使用 'attack' 属性

        def calculate_skill_value(skill, user, target):
            """
            计算技能的收益/伤害值，结合消耗。返回净收益值。
            """
            total_value = 0
            total_cost = 0

            for attr, effect_change in skill.effect_changes.items():
                if attr == "hp":
                    # 计算普通伤害或真实伤害
                    base_value = get_base_value(effect_change, user, target)
                    multiplier = effect_change.get("multiplier", 1.0)

                    if effect_change["attribute"] in ["attack", "defense"]:
                        # 处理普通伤害
                        try:
                            damage = user.calculate_damage(target, base_value, skill_multiplier=multiplier,
                                                           is_skill=True)
                            total_value += max(0, damage)  # 正数表示伤害
                        except Exception as e:
                            print(f"计算普通伤害时出错: {e}")
                    else:
                        # 处理真实伤害或治疗
                        change = base_value * multiplier
                        if skill.target_type == "enemy":
                            total_value += max(0, change)  # 正数表示伤害
                        elif skill.target_type == "ally":
                            total_value += max(0, -change)  # 负数表示治疗

                # 计算消耗
                for cost_attr, cost_change in skill.cost.items():
                    if isinstance(cost_change, dict):
                        base_cost = getattr(user, cost_change.get('attribute', 'hp'))
                        multiplier = cost_change.get('multiplier', 1.0)
                        cost = base_cost * multiplier
                    else:
                        cost = cost_change

                    # 成本为正数时消耗资源，成本为负数时恢复资源
                    if cost >= 0:
                        total_cost += cost  # 正成本表示消耗
                    else:
                        total_value += abs(cost)  # 负成本表示恢复效果

            net_value = total_value - total_cost
            return net_value

        def choose_best_skill():
            """
            根据技能的价值和消耗，选择最优技能。
            """
            best_skill = None
            best_value = -float('inf')  # 初始化为负无穷大
            best_target = None

            # 遍历玩家的战斗中的技能副本
            for skill in self.player.battle_skills:
                # 跳过使用次数为 0 的技能
                if skill.frequency is not None and skill.frequency <= 0:
                    continue

                # 寻找技能目标
                target = self.choose_auto_target(skill.target_type, skill.target_scope)
                if not target:
                    continue

                # 计算技能的净收益
                try:
                    skill_value = calculate_skill_value(skill, self.player, target)
                except Exception as e:
                    print(f"计算技能 {skill.name} 的价值时出错: {e}")
                    continue

                # 忽略消耗大于当前资源的技能
                for cost_attr, cost_change in skill.cost.items():
                    try:
                        cost_value = cost_change if isinstance(cost_change, (int, float)) else getattr(self.player,
                                                                                                       cost_change.get(
                                                                                                           'attribute',
                                                                                                           'hp')) * cost_change.get(
                            'multiplier', 1.0)
                        if cost_value > getattr(self.player, cost_attr):
                            continue  # 跳过消耗超过当前资源的技能
                    except Exception as e:
                        print(f"检查技能 {skill.name} 消耗时出错: {e}")
                        continue

                # 判断是否选择当前技能
                if skill_value > best_value:
                    best_value = skill_value
                    best_skill = skill
                    best_target = target

            return best_skill, best_target

        # 优先考虑自身血量情况，若低于30%，优先考虑治疗技能
        if self.player.hp < 0.3 * self.player.max_hp:
            for skill in self.player.battle_skills:
                if skill.target_type == "ally" and "hp" in skill.effect_changes and skill.frequency != 0:
                    target = self.choose_auto_target("ally", skill.target_scope)
                    if target and target.hp < target.max_hp:
                        self.player.use_skill(skill, target)  # 使用战斗副本中的技能
                        return

        # 寻找最优技能
        best_skill, best_target = choose_best_skill()
        if best_skill and best_target:
            self.player.use_skill(best_skill, best_target)  # 使用战斗副本中的技能
            if isinstance(best_target, list):
                for each_target in best_target:
                    if each_target.hp <= 0:
                        self.enemies.remove(each_target)
                        process_drops(each_target)
            return

        # 如果没有合适的技能，进行普通攻击
        if self.enemies:
            target = self.choose_auto_target("enemy")
            if target:
                self.player.perform_attack(target)
                if not isinstance(target, list) and target.hp <= 0:
                    self.enemies.remove(target)
                    process_drops(target)

    def choose_auto_target(self, target_type="enemy", target_scope="single"):
        if target_scope == "all":
            if target_type == "enemy":
                return self.enemies
            elif target_type == "ally":
                return [self.player] + self.allies
        else:
            if target_type == "enemy":
                available_targets = [enemy for enemy in self.enemies if enemy.hp > 0]
                return random.choice(available_targets) if available_targets else None
            elif target_type == "ally":
                available_targets = [self.player] + [ally for ally in self.allies if ally.hp > 0]
                return random.choice(available_targets) if available_targets else None
