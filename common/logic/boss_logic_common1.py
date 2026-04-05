import random


def boss_logic(boss, battle):
    # 初始化权重
    if boss.hp > boss.max_hp * 0.5:
        weights = {
            'skill_or_equipment': 0.6,
            'attack': 0.4,
            'summon': 0
        }
    else:
        # Boss 血量 ≤ 50% 时
        weights = {
            'skill_or_equipment': 0.8,
            'summon': 0,
            'attack': 0.2
        }

    # 根据权重选择行动
    action = random.choices(
        population=['skill_or_equipment', 'attack', 'summon'],
        weights=[weights['skill_or_equipment'], weights['attack'], weights['summon']],
        k=1
    )[0]

    # 处理 Boss 的行为
    if action == 'summon' and len(battle.enemies) < 5:
        # 召唤小怪
        summoned_enemies = boss.summon()
        battle.enemies.extend(summoned_enemies)
        battle.turn_order.extend(summoned_enemies)
        battle.update_turn_order()
        print(f"{boss.name} 召唤了小怪！")

    elif action == 'skill_or_equipment':
        # 随机选择技能或法宝
        if boss.skills or boss.equipment:
            if random.random() < 0.5 and boss.skills:
                # 使用技能
                skill = random.choice(boss.skills)
                targets = determine_targets(skill, battle)
                boss.use_skill(skill, targets)
            elif boss.equipment:
                # 使用法宝
                equipment = random.choice(boss.equipment)
                targets = determine_targets(equipment, battle)
                boss.use_equipment(equipment, targets)

    elif action == 'attack':
        # 普攻
        target = random.choice([battle.player] + battle.allies)
        boss.perform_attack(target)


def determine_targets(ability, battle):
    if ability.target_scope == "all":
        if ability.target_type == "enemy":
            return [battle.player] + battle.allies
        elif ability.target_type == "ally":
            return battle.enemies
    else:
        if ability.target_type == "enemy":
            return [random.choice([battle.player] + battle.allies)]
        elif ability.target_type == "ally":
            return [random.choice(battle.enemies)]