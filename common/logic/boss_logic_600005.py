import random
from library.skill_library import skill_library


def boss_logic(boss, battle):
    # 判断血量是否大于等于 60%
    if boss.hp >= boss.max_hp * 0.6:
        # 初始化权重
        weights = {
            'summon': 0.5,  # 50% 概率召唤小怪
            'skill_220019_220020': 0.5  # 50% 概率使用 skill_library[220019] 或 skill_library[220020]
        }

        # 根据权重选择行动
        action = random.choices(
            population=['summon', 'skill_220019_220020'],
            weights=[weights['summon'], weights['skill_220019_220020']],
            k=1
        )[0]

        if action == 'summon' and len(battle.enemies) < 5:
            # 召唤小怪
            summoned_enemies = boss.summon()
            battle.enemies.extend(summoned_enemies)
            battle.turn_order.extend(summoned_enemies)
            battle.update_turn_order()
            print(f"{boss.name} 召唤了小怪！")

        elif action == 'skill_220019_220020':
            last_skill_used = getattr(boss, 'last_skill_used', None)
            if last_skill_used == skill_library[220019]:
                skill = skill_library[220020]
            else:
                skill = skill_library[220019]
            targets = determine_targets(skill, battle)
            boss.use_skill(skill, targets)
            boss.last_skill_used = skill  # 保存上次使用的技能

    else:
        # 当血量小于 60%
        weights = {
            'attack': 0.3,  # 30% 概率普攻
            'skill_220021': 0.7  # 70% 概率使用 skill_library[220021]
        }

        action = random.choices(
            population=['attack', 'skill_220021'],
            weights=[weights['attack'], weights['skill_220021']],
            k=1
        )[0]

        if action == 'attack':
            # 普通攻击
            target = random.choice([battle.player] + battle.allies)
            boss.perform_attack(target)
        elif action == 'skill_220021':
            # 使用技能 skill_library[220021]
            skill = skill_library[220021]
            targets = determine_targets(skill, battle)
            boss.use_skill(skill, targets)


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
