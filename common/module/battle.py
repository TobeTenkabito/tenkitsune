from common.character.player import Player
from .item import Skill, Equipment, Medicine, Product, Material, Warp
from common.character.boss import Boss
from common.character.ally import Ally
from core.registry import registry  # ← 替換所有 library import
import random
import copy


class Battle:
    def __init__(self, player, allies, enemies):
        self.player = player
        self.allies = [copy.deepcopy(ally) for ally in allies]
        self.enemies = [copy.deepcopy(enemy) for enemy in enemies]
        if not self.player and not self.enemies:
            raise ValueError("没有玩家或敌人，无法开始战斗")
        self.defeated_enemies = []
        self.turn_order = []
        self.auto_battle = False
        if self.player is not None:
            self.player.battle = self
        for ally in self.allies:
            ally.battle = self
        for enemy in self.enemies:
            enemy.battle = self
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
        for p in participants:
            if not hasattr(p, 'speed'):
                raise ValueError(f"{p.name} 缺少 speed 属性，无法计算回合顺序")
        self.turn_order = sorted(participants, key=lambda x: x.speed, reverse=True)
        print(f"回合顺序: {[p.name for p in self.turn_order]}")

    def display_player_status(self):
        print(f"\n玩家状态: {self.player}")
        for ally in self.allies:
            print(f"\n队友状态: {ally}")

    def check_hp_mp_limits(self):
        targets = (
            [self.player] if self.player else []
        ) + self.allies + self.enemies

        for p in targets:
            if p.hp > 1.1 * p.max_hp:
                p.hp = 1.1 * p.max_hp
            if p.mp > p.max_mp:
                p.mp = p.max_mp

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

            elif choice == '2':
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

            elif choice == '3':
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
                print(f"自动战斗已{'开启' if self.auto_battle else '关闭'}")
                return True

            elif choice == '7':
                return "back"

            elif choice == '8':
                if all(enemy.hp <= 0 for enemy in self.enemies):
                    print("战斗结束！即将进入结算...")
                    return "end_battle"
                else:
                    print("现在还不是结束战斗的时候，敌人尚未全部被击败。")

            else:
                print("无效的选择。请重试。")

    def choose_target(self, target_type="enemy", target_scope="single"):
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
                    return self.enemies if target_type == "enemy" else [self.player] + self.allies
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
                enemy.perform_attack(random.choice([self.player] + self.allies))
        else:
            if enemy.battle_skills and random.random() < 0.5:
                skill = random.choice(enemy.battle_skills)
                targets = (
                    [self.player] + self.allies
                    if skill.target_scope == "all" and skill.target_type == "enemy"
                    else [random.choice([self.player] + self.allies)]
                )
                enemy.use_skill(skill, targets)
            else:
                enemy.perform_attack(random.choice([self.player] + self.allies))

    def ally_action(self, ally):
        if ally.hp <= 0:
            return
        if ally.battle_skills and random.random() < 0.5:
            skill = random.choice(ally.battle_skills)
            if skill.target_scope == "all":
                target = self.enemies if skill.target_type == "enemy" else [self.player] + self.allies
            else:
                target = random.choice(self.enemies) if self.enemies else None
            if target:
                ally.use_skill(skill, target)
        else:
            if self.enemies:
                ally.perform_attack(random.choice(self.enemies))

    def check_battle_status(self):
        if self.player.hp <= 0 and all(ally.hp <= 0 for ally in self.allies):
            print("玩家和队友战败!")
            return "loss"
        if len(self.enemies) == 0:
            print("玩家和队友胜利!")
            return "win"
        return "ongoing"

    def run_battle(self):
        for ally in self.allies:
            ally.battle = self
        for enemy in self.enemies:
            enemy.battle = self
        self.determine_turn_order()
        battle_status = "ongoing"
        turn_count = 1

        while battle_status == "ongoing":
            print(f"\n第 {turn_count} 回合开始!")
            print("当前回合顺序:", [p.name for p in self.turn_order])

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

                    battle_status = self.check_battle_status()
                    if battle_status != "ongoing":
                        break
                i += 1

            if battle_status == "ongoing":
                self.remove_dead_participants()
                self.update_turn_order()
                turn_count += 1

        self.clear_all_buffs()

        for participant in self.turn_order:
            if isinstance(participant, Player):
                participant.reset_medicine_effects()
                participant.reset_skill_bonuses()

        if battle_status == "win":
            self.process_victory()
        elif battle_status == "loss":
            print("你被击败了。")

        return battle_status

    def process_victory(self):
        enemy_defeat_summary = {}
        total_exp = 0

        for enemy in self.defeated_enemies:
            total_exp += enemy.exp_drops
            enemy_defeat_summary[enemy.name] = enemy_defeat_summary.get(enemy.name, 0) + 1

        print(f"获得总经验: {total_exp}")
        print("\n击败的敌人统计:")
        for enemy_name, count in enemy_defeat_summary.items():
            print(f"{enemy_name}: {count} 个")

        self.player.update_tasks_after_battle()

        print("\n战斗结束后的玩家状态:")
        print(self.player)
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
        participants = (
            [self.player]
            + [ally for ally in self.allies if ally.hp > 0]
            + [enemy for enemy in self.enemies if enemy.hp > 0]
        )
        self.turn_order = sorted(participants, key=lambda x: x.speed, reverse=True)
        print("更新后的回合顺序:", [p.name for p in self.turn_order])

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

    def process_enemy_drops(self, enemy):
        drop_summary = {}

        for drop_number, quantity in enemy.drops:
            drop_summary[drop_number] = drop_summary.get(drop_number, 0) + quantity

        for drop_number, quantity, chance in enemy.chance_drops:
            if random.random() < chance:
                drop_summary[drop_number] = drop_summary.get(drop_number, 0) + quantity

        drops = []
        for drop_number, total_quantity in drop_summary.items():
            item = self.get_item_by_id(drop_number)
            if item is None:
                print(f"无法识别的掉落物 ID: {drop_number}")
                continue

            new_item = copy.deepcopy(item)

            if isinstance(new_item, (Material, Product)):
                new_item.quantity = total_quantity
                self.player.add_to_inventory(new_item)
                drops.append((new_item.name, total_quantity))
                print(f"获得物品: {new_item.name} x {total_quantity}")

            elif isinstance(new_item, Equipment):
                for _ in range(total_quantity):
                    self.player.add_equipment(copy.copy(new_item))
                    drops.append((new_item.name, 1))
                    print(f"获得装备: {new_item.name}")

            elif isinstance(new_item, (Medicine, Warp, Skill)):
                for _ in range(total_quantity):
                    self.player.add_to_inventory(copy.copy(new_item))
                    drops.append((new_item.name, 1))
                    print(f"获得物品: {new_item.name}")

        return drops

    def get_item_by_id(self, item_id):
        """
        通過 Registry 查找物品，替代原本的多個 library dict 查詢。
        查找順序：material → equipment → product → warp → medicine → skill
        """
        for category in ("material", "equipment", "product", "warp", "medicine", "skill"):
            item = registry.get(category, item_id)
            if item is not None:
                return item
        return None

    # ── 自動戰鬥 ──────────────────────────────────────────────

    def auto_action(self):
        def get_base_value(effect_change, user, target):
            if effect_change.get("source") == "target":
                return getattr(target, effect_change["attribute"], 0)
            return getattr(user, effect_change.get("attribute", "attack"), 0)

        def calculate_skill_value(skill, user, target):
            total_value = 0
            total_cost = 0

            for attr, effect_change in skill.effect_changes.items():
                if attr == "hp":
                    base_value = get_base_value(effect_change, user, target)
                    multiplier = effect_change.get("multiplier", 1.0)
                    if effect_change["attribute"] in ["attack", "defense"]:
                        try:
                            damage = user.calculate_damage(
                                target, base_value,
                                skill_multiplier=multiplier, is_skill=True
                            )
                            total_value += max(0, damage)
                        except Exception as e:
                            print(f"计算普通伤害时出错: {e}")
                    else:
                        change = base_value * multiplier
                        if skill.target_type == "enemy":
                            total_value += max(0, change)
                        elif skill.target_type == "ally":
                            total_value += max(0, -change)

                for cost_attr, cost_change in skill.cost.items():
                    if isinstance(cost_change, dict):
                        base_cost = getattr(user, cost_change.get('attribute', 'hp'))
                        cost = base_cost * cost_change.get('multiplier', 1.0)
                    else:
                        cost = cost_change
                    if cost >= 0:
                        total_cost += cost
                    else:
                        total_value += abs(cost)

            return total_value - total_cost

        def choose_best_skill():
            best_skill, best_value, best_target = None, -float('inf'), None
            for skill in self.player.battle_skills:
                if skill.frequency is not None and skill.frequency <= 0:
                    continue
                target = self.choose_auto_target(skill.target_type, skill.target_scope)
                if not target:
                    continue
                try:
                    skill_value = calculate_skill_value(skill, self.player, target)
                except Exception as e:
                    print(f"计算技能 {skill.name} 的价值时出错: {e}")
                    continue
                # 跳過消耗超過當前資源的技能
                skip = False
                for cost_attr, cost_change in skill.cost.items():
                    try:
                        cost_value = (
                            cost_change if isinstance(cost_change, (int, float))
                            else getattr(self.player, cost_change.get('attribute', 'hp'))
                                 * cost_change.get('multiplier', 1.0)
                        )
                        if cost_value > getattr(self.player, cost_attr):
                            skip = True
                            break
                    except Exception as e:
                        print(f"检查技能 {skill.name} 消耗时出错: {e}")
                        skip = True
                        break
                if skip:
                    continue
                if skill_value > best_value:
                    best_value, best_skill, best_target = skill_value, skill, target
            return best_skill, best_target

        # 血量低於 30% 優先治療
        if self.player.hp < 0.3 * self.player.max_hp:
            for skill in self.player.battle_skills:
                if skill.target_type == "ally" and "hp" in skill.effect_changes and skill.frequency != 0:
                    target = self.choose_auto_target("ally", skill.target_scope)
                    if target and target.hp < target.max_hp:
                        self.player.use_skill(skill, target)
                        return

        best_skill, best_target = choose_best_skill()
        if best_skill and best_target:
            self.player.use_skill(best_skill, best_target)
            if isinstance(best_target, list):
                for t in best_target:
                    if t.hp <= 0 and t in self.enemies:
                        self.enemies.remove(t)
                        self.process_enemy_drops(t)
            return

        # 無合適技能則普通攻擊
        if self.enemies:
            target = self.choose_auto_target("enemy")
            if target:
                self.player.perform_attack(target)
                if not isinstance(target, list) and target.hp <= 0 and target in self.enemies:
                    self.enemies.remove(target)
                    self.process_enemy_drops(target)

    def choose_auto_target(self, target_type="enemy", target_scope="single"):
        if target_scope == "all":
            return self.enemies if target_type == "enemy" else [self.player] + self.allies
        if target_type == "enemy":
            available = [e for e in self.enemies if e.hp > 0]
            return random.choice(available) if available else None
        elif target_type == "ally":
            available = [self.player] + [a for a in self.allies if a.hp > 0]
            return random.choice(available) if available else None
