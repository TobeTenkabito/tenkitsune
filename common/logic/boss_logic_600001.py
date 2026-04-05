import random


def boss_logic(boss, battle):
    # 初始权重
    weights = {
        'summon': 0,
        'skill': 0,
        'equipment': 1,
        'attack': 0
    }

    # 检查召唤的小怪血量
    for enemy in battle.enemies:
        if enemy.hp > 0 and enemy.number in boss.summon_list:
            if enemy.hp < enemy.max_hp * 0.5:
                weights = {
                    'summon': 0.3,
                    'skill': 0.5,
                    'equipment': 0.1,
                    'attack': 0.1
                }
                break

    # 根据权重选择行动
    action = random.choices(
        population=['summon', 'skill', 'equipment', 'attack'],
        weights=[weights['summon'], weights['skill'], weights['equipment'], weights['attack']],
        k=1
    )[0]

    if action == 'summon' and len(battle.enemies) < 5:
        summoned_enemies = boss.summon()
        battle.enemies.extend(summoned_enemies)
        battle.turn_order.extend(summoned_enemies)
        battle.update_turn_order()
        print(f"{boss.name} 召唤了小怪！")
    elif action == 'skill':
        if boss.skills:
            skill = random.choice(boss.skills)
            if skill.target_scope == "all":
                if skill.target_type == "enemy":
                    targets = [battle.player] + battle.allies
                elif skill.target_type == "ally":
                    targets = battle.enemies
            else:
                if skill.target_type == "enemy":
                    targets = [random.choice([battle.player] + battle.allies)]
                elif skill.target_type == "ally":
                    targets = [random.choice(battle.enemies)]
            boss.use_skill(skill, targets)
    elif action == 'equipment':
        if boss.equipment:
            equipment = random.choice(boss.equipment)
            if equipment.target_scope == "all":
                if equipment.target_type == "enemy":
                    targets = [battle.player] + battle.allies
                elif equipment.target_type == "ally":
                    targets = battle.enemies
            else:
                if equipment.target_type == "enemy":
                    targets = [random.choice([battle.player] + battle.allies)]
                elif equipment.target_type == "ally":
                    targets = [random.choice(battle.enemies)]
            boss.use_equipment(equipment, targets)
    else:
        target = random.choice([battle.player] + battle.allies)
        boss.perform_attack(target)
