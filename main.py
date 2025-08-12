import copy
import time
import sys
import random
import json
import os
import importlib
from all.gamestate import game_state
from common.interface.bag_interface import BagInterface
from common.interface.cultivation_interface import CultivationInterface
from common.interface.synthesis_interface import show_synthesis_interface
from common.interface.lottery_interface import LotteryInterface
from common.interface.market_interface import show_market_interface
from library.material_library import material_library
from library.npc_library import npc_library
from library.map_library import map_library
from library.lottery_library import lottery_library
from common.module.story import load_story_from_json, Chapter
from common.module.battle import Battle


def show_title_screen():
    print("======= 天狐修炼纪 =======")
    print("1. 旅途开始")
    print("2. 前尘忆梦（读档）")
    print("3. 结束征程（退出）")
    print("==========================")
    choice = input("请选择: ")

    if choice == '1':
        start_new_game()
    elif choice == '2':
        slot_number = choose_save_slot()
        player = load_game(slot_number)
        if player:
            enter_main_screen(player, slot_number)
    elif choice == '3':
        end_game()
    else:
        print("无效选项，请重试。")
        show_title_screen()


def start_new_game():
    print("旅途开始……")

    # 初始化玩家
    player_name = "白夙"
    game_state.initialize_player(1, player_name)  # 创建玩家
    player = game_state.get_player()
    if player:
        print(f"玩家 {player.name} 初始化成功！")
    else:
        print("Error: 玩家初始化失败！")

    # 初始化地图
    try:
        for map_number, map_obj in map_library.items():
            game_state.add_map(map_number, map_obj)
        print("全局地图初始化成功")
    except Exception as e:
        print(f"全局地图初始化失败: {e}")

    # 初始化npc
    try:
        for npc_number, npc_obj in npc_library.items():
            game_state.add_npc(npc_number, npc_obj)
        print("全局npc初始化成功")
    except Exception as e:
        print(f"全局npc初始化失败: {e}")

    # 设置玩家背包初始物品
    player = game_state.get_player()
    if player is None:
        print("Error: Player is None after initialization!")
    else:
        coin = material_library[100000]
        coin.quantity += 99
        player.add_to_inventory(coin)
        beidou = material_library[120000]
        beidou.quantity += 199
        player.add_to_inventory(beidou)
        print(f"获得 {coin.name} x100")

    slot_number = choose_save_slot()

    enter_main_screen(player, slot_number)


def enter_main_screen(player, slot_number):
    current_map = game_state.get_map(player.map_location)
    if not current_map:
        print(f"未能加载玩家所在地图: {player.map_location}")
    else:
        print(f"玩家当前所在地图: {current_map.name}")
    while True:
        print("\n======= 游戏主界面 =======")
        show_player_info(player)
        print("1. 背包互动")
        print("2. 修为互动")
        print("3. 合成互动")
        print("4. 抽奖互动")
        print("5. 集市互动")
        print("6. 探索地图")
        print("7. 闭关修炼")
        print("8. 保存游戏")
        print("9. 读档游戏")
        print("10. 离开游戏")
        print("0. 故事模式")
        print("==========================")
        choice = input("请选择功能: ")

        if choice == '1':
            BagInterface(player).show_bag_interface()
        elif choice == '2':
            cultivation_interface = CultivationInterface(player.cultivation_system)
            cultivation_interface.show_cultivation_interface()
        elif choice == '3':
            show_synthesis_interface(player)
        elif choice == '4':
            lottery_pool = lottery_library[1]
            LotteryInterface(player).show_lottery_interface(lottery_pool)
        elif choice == '5':
            show_market_interface(player)
        elif choice == '6':
            explore_current_map(player)
        elif choice == '7':
            train_player(player)
        elif choice == '8':
            save_game_menu(player)
        elif choice == '9':
            load_game_menu()
        elif choice == '10':
            end_game()
        elif choice == '0':
            go_story(player, slot_number)
        else:
            print("无效选项，请重试。")


def explore_current_map(player):
    current_map = game_state.get_map(player.map_location)
    if current_map:
        print(f"正在探索地图: {current_map.name}")
        current_map.explore()
    else:
        print(f"无法探索当前地图。玩家所在地图编号: {player.map_location}")


def show_player_info(player):
    current_map = game_state.get_map(player.map_location)
    print(f"玩家: {player.name}")
    print(f"等级: {player.level}")
    print(f"经验: {player.exp}/{player.max_exp}")
    print(f"生命值: {player.hp}/{player.max_hp}")
    print(f"法力值: {player.mp}/{player.max_mp}")
    print(f"攻击: {player.attack}")
    print(f"防御: {player.defense}")
    print(f"速度: {player.speed}")
    print(f"修为点: {player.cultivation_point}")
    print(f"当前地图: {current_map.name}")


def train_player(player):
    print("你开始修炼……")
    time.sleep(1)
    player.hp = max(0, player.hp)  # 如果已经死亡，先重置生命
    coefficient = random.randint(800, 1200)/1000
    train_exp = (100 + 0.02 * player.max_exp + 10 * player.level) * coefficient
    train_hp = 0.1 * player.max_hp * coefficient
    train_mp = 0.1 * player.max_mp * coefficient
    player.hp += train_hp
    player.mp += train_mp
    player.gain_exp(train_exp)
    player.update_stats()
    print(f"{player.name} 修炼结束，获得经验 {train_exp} 点！回复气血{train_hp}点，回复法力{train_mp}点！,本次修炼效率为{coefficient}")
    result = (
        f"{player.name} 修炼结束，获得经验 {train_exp:.2f} 点！"
        f"回复气血 {train_hp:.2f} 点，回复法力 {train_mp:.2f} 点！"
        f"本次修炼效率为 {coefficient:.2f}"
    )
    return result


def go_story(player, slot_number):
    from common.module.story import StoryManager

    # 创建一个空的动态战斗
    dynamic_battle = Battle(player=player, allies=[], enemies=[])

    # 定义章节列表
    chapters = define_chapters(player, dynamic_battle)

    # 初始化 StoryManager
    story_manager = StoryManager(player, chapters)

    # 保存回调函数，包含存档槽编号
    def save_callback():
        # 保存当前进度时，将 player 和 slot_number 传递给 save_game 函数
        save_game(player, slot_number)

    # 玩家选择如何开始故事模式
    print("你进入了故事模式。")
    print("1. 从本章开头开始")
    print("2. 从保存节点开始")
    print("3. 返回上一级")

    choice = input("请选择选项: ")

    if choice == "1":
        # 让玩家选择章节
        selected_chapter = story_manager.select_chapter()
        if selected_chapter:
            # 从本章开头开始，传入保存回调函数
            story_manager.start_chapter_from_beginning(save_callback=save_callback)
        else:
            print("章节未选择或未解锁。")
    elif choice == "2":
        # 从保存的节点开始，传入保存回调函数
        story_manager.continue_from_saved_node(save_callback=save_callback)
    elif choice == "3":
        return
    else:
        print("无效的选项，请重新选择。")


# 在此处添加剧情文本和修改
def define_chapters(player, dynamic_battle):
    chapters = []

    # 定义第一章
    chapter1 = Chapter(1, "第一章", None, None)
    load_story_from_json('chapter/chapter1.json', player, dynamic_battle, chapter=chapter1)

    # 从玩家的 story_progress 中同步章节状态
    chapter1.is_completed = player.story_progress["chapters_completed"].get("1", False)
    chapters.append(chapter1)

    chapter2 = Chapter(2, "第二章", None, None)
    load_story_from_json('chapter/chapter2.json', player, dynamic_battle, chapter=chapter2)

    chapter2.is_completed = player.story_progress["chapters_completed"].get("2", False)
    chapters.append(chapter2)

    chapter3 = Chapter(3, "第三章", None, None)
    load_story_from_json('chapter/chapter3.json', player, dynamic_battle, chapter=chapter3)

    chapter3.is_completed = player.story_progress["chapters_completed"].get("3", False)
    chapters.append(chapter3)

    chapter4 = Chapter(4, "第四章", None, None)
    load_story_from_json('chapter/chapter4.json', player, dynamic_battle, chapter=chapter4)

    chapter4.is_completed = player.story_progress["chapters_completed"].get("4", False)
    chapters.append(chapter4)

    return chapters


def get_save_file_path(slot_number):
    return f"data/save/save_slot_{slot_number}.json"


def show_save_slots():
    print("\n可用存档列表:")
    for i in range(1, 6):  # 显示5个存档位
        save_file = get_save_file_path(i)
        if os.path.exists(save_file):
            print(f"{i}. 存档 {i} (已保存)")
        else:
            print(f"{i}. 存档 {i} (空)")


def choose_save_slot():
    while True:
        show_save_slots()  # 显示存档列表
        print("如果您是第一次进入游戏，输入的存档位将作为故事模式进度的保存位置。")
        choice = input("请输入存档编号 (1-5): ")
        if choice.isdigit() and 1 <= int(choice) <= 5:
            return int(choice)  # 返回选择的存档位编号
        else:
            print("无效选择，请输入1到5之间的数字。")


def save_game_menu(player):
    print("保存游戏")
    slot_number = choose_save_slot()  # 选择存档位
    save_game(player, slot_number)    # 保存到对应的存档


def save_game(player, slot_number):
    save_file = get_save_file_path(slot_number)  # 生成文件路径

    save_data = {
        "player": {
            "number": player.number,
            "name": player.name,
            "level": player.level,
            "base_hp": player.base_hp,
            "base_mp": player.base_mp,
            "base_attack": player.base_attack,
            "base_defense": player.base_defense,
            "base_speed": player.base_speed,
            "base_crit": player.base_crit,
            "base_crit_damage": player.base_crit_damage,
            "base_resistance": player.base_resistance,
            "base_penetration": player.base_penetration,
            "max_exp": player.max_exp,
            "max_hp": player.max_hp,
            "max_mp": player.max_mp,
            "exp": player.exp,
            "hp": player.hp,
            "mp": player.mp,
            "attack": player.attack,
            "defense": player.defense,
            "speed": player.speed,
            "crit": player.crit,
            "crit_damage": player.crit_damage,
            "resistance": player.resistance,
            "penetration": player.penetration,
            "map_location": player.map_location,
            "cultivation_point": player.cultivation_point,
            # dlc特质
            "traits": {k: v.__dict__ for k, v in (player.traits or {}).items()},  # 保存 traits 内容
            "applied_traits": list(player.applied_traits),  # 保存已应用特质的名称

            "equipment": [
                {
                    "item_number": equip.number,
                    "quantity": equip.quantity
                }
                for equip in player.equipment
            ],
            "skill": [
                skill.number for skill in player.skills
            ],
            "inventory": [
                {
                    "item_type": type(item).__name__,
                    "item_number": item.number,
                    "quantity": item.quantity
                }
                for item in player.inventory
            ],
            "completed_tasks": player.completed_tasks,  # 保存已完成任务
            "accepted_tasks": [{"task_number": task.number, "kill_counts": task.kill_counts}
                               for task in player.accepted_tasks],  # 保存已接受任务
            "ready_to_complete_tasks": [{"task_number": task.number}
                                        for task in player.ready_to_complete_tasks],
            "defeated_enemies": player.defeated_enemies,  # 记录已击败敌人
            "highest_floor": player.highest_floor,  # 记录秘境最高层数
            "dungeon_clears": player.dungeon_clears,  # 记录每个秘境的通关状态
            "dungeons_cleared": list(player.dungeons_cleared),  # 已通关的秘境
            "talked_to_npcs": list(player.talked_to_npcs),  # 已对话的 NPC 编号
            "npcs_removed": list(player.npcs_removed) if player.npcs_removed else [],  # 移除的npc
            "given_items": {
                npc_id: {
                    "item_number": item_number,
                    "quantity": quantity
                }
                for npc_id, items in player.given_items.items()
                for item_number, quantity in items.items()
            },
            # 汇总属性
            "task_attributes": {
                "hp": player.task_hp,
                "mp": player.task_mp,
                "attack": player.task_attack,
                "defense": player.task_defense,
                "speed": player.task_speed,
                "crit": player.task_crit,
                "crit_damage": player.task_crit_damage,
                "resistance": player.task_resistance,
                "penetration": player.task_penetration
            },
            "dungeon_attributes": {
                "hp": player.dungeon_hp,
                "mp": player.dungeon_mp,
                "attack": player.dungeon_attack,
                "defense": player.dungeon_defense,
                "speed": player.dungeon_speed,
                "crit": player.dungeon_crit,
                "crit_damage": player.dungeon_crit_damage,
                "resistance": player.dungeon_resistance,
                "penetration": player.dungeon_penetration
            },
            "cultivation_attributes": {
                "hp": player.cultivation_hp,
                "mp": player.cultivation_mp,
                "attack": player.cultivation_attack,
                "defense": player.cultivation_defense,
                "speed": player.cultivation_speed,
                "crit": player.cultivation_crit,
                "crit_damage": player.cultivation_crit_damage,
                "resistance": player.cultivation_resistance,
                "penetration": player.cultivation_penetration
            },
            "medicine_attributes": {
                "hp": player.medicine_hp,
                "mp": player.medicine_mp,
                "attack": player.medicine_attack,
                "defense": player.medicine_defense,
                "speed": player.medicine_speed,
                "crit": player.medicine_crit,
                "crit_damage": player.medicine_crit_damage,
                "resistance": player.medicine_resistance,
                "penetration": player.medicine_penetration
            },
            "skill_attributes": {
                "mp": player.skill_mp,
                "attack": player.skill_attack,
                "defense": player.skill_defense,
                "speed": player.skill_speed,
                "crit": player.skill_crit,
                "crit_damage": player.skill_crit_damage,
                "resistance": player.skill_resistance,
                "penetration": player.skill_penetration
            },
            # Cultivation system (心法) 保存
            "cultivation_system": {
                # 保存心法线编号，1 表示 skill_ids_line1, 2 表示 skill_ids_line2
                "current_xinfa_line": (
                    1 if player.cultivation_system.current_xinfa_line == player.cultivation_system.skill_ids_line1
                    else 2 if player.cultivation_system.current_xinfa_line == player.cultivation_system.skill_ids_line2
                    else 3 if player.cultivation_system.current_xinfa_line == player.cultivation_system.skill_ids_line3
                    else 4 if player.cultivation_system.current_xinfa_line == player.cultivation_system.skill_ids_line4
                    else None  # 如果没有选择心法线，设置为 None
                ),
                "current_xinfa_level": player.cultivation_system.current_xinfa_level,
                "used_points": player.cultivation_system.used_points,
                "unused_points": player.cultivation_system.unused_points,
                "cultivation_data": {
                    element: {
                        "level": data["level"],
                        "attributes_per_level": data.get("attributes_per_level", {})
                    }
                    for element, data in player.cultivation_system.cultivation_data.items()
                }
            }
        },
        # npc存储
        "npcs_affection": {
            npc_id: npc.affection for npc_id, npc in npc_library.items()
        },
        "story_progress": {
            "current_chapter": player.story_progress["current_chapter"],
            "current_node": player.story_progress["current_node"],
            "chapters_completed": player.story_progress["chapters_completed"],
            "completed_nodes": player.story_progress["completed_nodes"],
        }
    }
    print(f"存档中的 npcs_removed: {player.npcs_removed}")
    with open(save_file, 'w') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=4)
    print(f"游戏已保存到存档位 {slot_number}.")


def load_game_menu():
    print("读取游戏")

    # 列出可用的存档位
    for i in range(1, 6):
        save_file = f"data/save/save_slot_{i}.json"
        if os.path.exists(save_file):
            print(f"{i}. 存档 {i} (已保存)")
        else:
            print(f"{i}. 存档 {i} (空)")

    slot_number = input("请选择存档编号 (1-5): ")

    if slot_number.isdigit() and 1 <= int(slot_number) <= 5:
        slot_number = int(slot_number)
        player = load_game(slot_number)  # 从指定存档位加载游戏
        if player:
            enter_main_screen(player, slot_number)  # 加载成功后进入主界面
        else:
            print("无法加载游戏，存档可能已损坏。")
    else:
        print("无效的存档编号，请重试。")


def load_game(slot_number):
    from common.module.item import Equipment, Skill, Medicine, Product, Warp, Material
    from common.character.player import Player
    from library.skill_library import skill_library
    from library.material_library import material_library
    from library.medicine_library import medicine_library
    from library.warp_library import warp_library
    from library.product_library import product_library
    from library.equipment_library import equipment_library
    from library.task_library import task_library

    save_file = get_save_file_path(slot_number)
    if not os.path.exists(save_file):
        print(f"存档 {slot_number} 不存在。")
        return None

    with open(save_file, 'r', encoding='GBK') as file:
        save_data = json.load(file)

        player_data = save_data.get("player", {})

        # 初始化玩家对象
        player = Player(player_data["number"], player_data["name"])
        player.level = player_data["level"]
        player.base_hp = player_data["base_hp"]
        player.base_mp = player_data["base_mp"]
        player.base_attack = player_data["base_attack"]
        player.base_defense = player_data["base_defense"]
        player.base_speed = player_data["base_speed"]
        player.base_crit = player_data["base_crit"]
        player.base_crit_damage = player_data["base_crit_damage"]
        player.base_resistance = player_data["base_resistance"]
        player.base_penetration = player_data["base_penetration"]
        player.max_exp = player_data["max_exp"]
        player.max_hp = player_data["max_hp"]
        player.max_mp = player_data["max_mp"]
        player.exp = player_data["exp"]
        player.hp = player_data["hp"]
        player.mp = player_data["mp"]
        player.attack = player_data["attack"]
        player.defense = player_data["defense"]
        player.speed = player_data["speed"]
        player.crit = player_data["crit"]
        player.crit_damage = player_data["crit_damage"]
        player.resistance = player_data["resistance"]
        player.penetration = player_data["penetration"]
        player.map_location = player_data["map_location"]
        player.cultivation_point = player_data["cultivation_point"]

        # 恢复玩家的物品（装备、技能、背包）
        for item_data in player_data["inventory"]:
            item_type = item_data["item_type"]
            item_number = item_data["item_number"]
            quantity = item_data["quantity"]

            if item_type == "Equipment":
                equipment_data = equipment_library[item_number]
                if equipment_data.category == "法宝":
                    new_item = Equipment(
                        number=equipment_data.number,
                        name=equipment_data.name,
                        description=equipment_data.description,
                        quality=equipment_data.quality,
                        category=equipment_data.category,
                        price=equipment_data.price,
                        quantity=quantity,
                        hp=equipment_data.hp,
                        mp=equipment_data.mp,
                        attack=equipment_data.attack,
                        defense=equipment_data.defense,
                        speed=equipment_data.speed,
                        crit=equipment_data.crit,
                        crit_damage=equipment_data.crit_damage,
                        resistance=equipment_data.resistance,
                        penetration=equipment_data.penetration,
                        target_type=equipment_data.target_type,
                        target_scope=equipment_data.target_scope,
                        effect_duration=equipment_data.effect_duration,
                        effect_changes=equipment_data.effect_changes,
                        cost=equipment_data.cost
                    )
                else:  # 处理其他类别的装备
                    new_item = Equipment(
                        number=equipment_data.number,
                        name=equipment_data.name,
                        description=equipment_data.description,
                        quality=equipment_data.quality,
                        category=equipment_data.category,
                        price=equipment_data.price,
                        quantity=quantity,
                        hp=equipment_data.hp,
                        mp=equipment_data.mp,
                        attack=equipment_data.attack,
                        defense=equipment_data.defense,
                        speed=equipment_data.speed,
                        crit=equipment_data.crit,
                        crit_damage=equipment_data.crit_damage,
                        resistance=equipment_data.resistance,
                        penetration=equipment_data.penetration
                    )

            elif item_type == "Medicine":
                medicine_data = medicine_library[item_number]
                new_item = Medicine(
                    number=medicine_data.number,
                    name=medicine_data.name,
                    description=medicine_data.description,
                    quality=medicine_data.quality,
                    price=medicine_data.price,
                    quantity=quantity,
                    effect_changes=medicine_data.effect_changes
                )

            elif item_type == "Product":
                product_data = product_library[item_number]
                new_item = Product(
                    number=product_data.number,
                    name=product_data.name,
                    description=product_data.description,
                    quality=product_data.quality,
                    price=product_data.price,
                    quantity=quantity,
                    target_type=product_data.target_type,
                    target_scope=product_data.target_scope,
                    effect_changes=product_data.effect_changes
                )

            elif item_type == "Material":
                material_data = material_library[item_number]
                new_item = Material(
                    number=material_data.number,
                    name=material_data.name,
                    description=material_data.description,
                    quality=material_data.quality,
                    price=material_data.price,
                    quantity=quantity
                )

            elif item_type == "Skill":
                skill_data = skill_library[item_number]
                new_item = Skill(
                    number=skill_data.number,
                    name=skill_data.name,
                    description=skill_data.description,
                    price=skill_data.price,
                    quantity=quantity,
                    quality=skill_data.quality,
                    target_type=skill_data.target_type,
                    target_scope=skill_data.target_scope,
                    effect_changes=skill_data.effect_changes,
                    frequency=skill_data.frequency,
                    cost=skill_data.cost
                )

            elif item_type == "Warp":
                warp_data = warp_library[item_number]
                new_item = Warp(
                    number=warp_data.number,
                    name=warp_data.name,
                    description=warp_data.description,
                    price=warp_data.price,
                    quantity=quantity,
                    quality=warp_data.quality,
                    target_map_number=warp_data.target_map_number
                )

            player.add_to_inventory(copy.deepcopy(new_item))

        # 恢复装备和技能
        for equip_data in player_data["equipment"]:
            equipment = equipment_library[equip_data["item_number"]]
            player.add_to_equipment(copy.deepcopy(equipment))

        for skill_number in player_data["skill"]:
            skill = skill_library[skill_number]
            player.add_to_skill(copy.deepcopy(skill))

        # 恢复任务状态
        player.accepted_tasks = [
            task_library[task_data["task_number"]] for task_data in player_data.get("accepted_tasks", [])
        ]
        player.ready_to_complete_tasks = [
            task_library[task_data["task_number"]] for task_data in player_data.get("ready_to_complete_tasks", [])
        ]
        player.completed_tasks = player_data.get("completed_tasks", [])

        # 恢复击败的敌人、秘境信息、赠送物品、对话过的 NPC, 移除的npc 等
        player.defeated_enemies = player_data["defeated_enemies"]
        player.highest_floor = player_data["highest_floor"]
        player.dungeon_clears = player_data["dungeon_clears"]
        player.dungeons_cleared = set(player_data["dungeons_cleared"])
        player.talked_to_npcs = set(player_data["talked_to_npcs"])
        player.npcs_removed = set(player_data.get('npcs_removed', []))
        player.given_items = player_data["given_items"]

        # 恢复属性加成
        player.task_hp = player_data["task_attributes"]["hp"]
        player.task_mp = player_data["task_attributes"]["mp"]
        player.task_attack = player_data["task_attributes"]["attack"]
        player.task_defense = player_data["task_attributes"]["defense"]
        player.task_speed = player_data["task_attributes"]["speed"]
        player.task_crit = player_data["task_attributes"]["crit"]
        player.task_crit_damage = player_data["task_attributes"]["crit_damage"]
        player.task_resistance = player_data["task_attributes"]["resistance"]
        player.task_penetration = player_data["task_attributes"]["penetration"]

        player.dungeon_hp = player_data["dungeon_attributes"]["hp"]
        player.dungeon_mp = player_data["dungeon_attributes"]["mp"]
        player.dungeon_attack = player_data["dungeon_attributes"]["attack"]
        player.dungeon_defense = player_data["dungeon_attributes"]["defense"]
        player.dungeon_speed = player_data["dungeon_attributes"]["speed"]
        player.dungeon_crit = player_data["dungeon_attributes"]["crit"]
        player.dungeon_crit_damage = player_data["dungeon_attributes"]["crit_damage"]
        player.dungeon_resistance = player_data["dungeon_attributes"]["resistance"]
        player.dungeon_penetration = player_data["dungeon_attributes"]["penetration"]

        player.cultivation_hp = player_data["cultivation_attributes"]["hp"]
        player.cultivation_mp = player_data["cultivation_attributes"]["mp"]
        player.cultivation_attack = player_data["cultivation_attributes"]["attack"]
        player.cultivation_defense = player_data["cultivation_attributes"]["defense"]
        player.cultivation_speed = player_data["cultivation_attributes"]["speed"]
        player.cultivation_crit = player_data["cultivation_attributes"]["crit"]
        player.cultivation_crit_damage = player_data["cultivation_attributes"]["crit_damage"]
        player.cultivation_resistance = player_data["cultivation_attributes"]["resistance"]
        player.cultivation_penetration = player_data["cultivation_attributes"]["penetration"]

        player.medicine_hp = player_data["medicine_attributes"]["hp"]
        player.medicine_mp = player_data["medicine_attributes"]["mp"]
        player.medicine_attack = player_data["medicine_attributes"]["attack"]
        player.medicine_defense = player_data["medicine_attributes"]["defense"]
        player.medicine_speed = player_data["medicine_attributes"]["speed"]
        player.medicine_crit = player_data["medicine_attributes"]["crit"]
        player.medicine_crit_damage = player_data["medicine_attributes"]["crit_damage"]
        player.medicine_resistance = player_data["medicine_attributes"]["resistance"]
        player.medicine_penetration = player_data["medicine_attributes"]["penetration"]

        Player.skill_mp = player_data["skill_attributes"]["mp"]
        Player.skill_attack = player_data["skill_attributes"]["attack"]
        Player.skill_defense = player_data["skill_attributes"]["defense"]
        Player.skill_speed = player_data["skill_attributes"]["speed"]
        Player.skill_crit = player_data["skill_attributes"]["crit"]
        Player.skill_crit_damage = player_data["skill_attributes"]["crit_damage"]
        Player.skill_resistance = player_data["skill_attributes"]["resistance"]
        Player.skill_penetration = player_data["skill_attributes"]["penetration"]

        # 恢复心法系统
        cultivation_data = player_data.get("cultivation_system", {})

        # 恢复当前心法线 (1 表示 skill_ids_line1，2 表示 skill_ids_line2)
        if cultivation_data.get("current_xinfa_line") == 1:
            player.cultivation_system.current_xinfa_line = player.cultivation_system.skill_ids_line1
        elif cultivation_data.get("current_xinfa_line") == 2:
            player.cultivation_system.current_xinfa_line = player.cultivation_system.skill_ids_line2
        elif cultivation_data.get("current_xinfa_line") == 3:
            player.cultivation_system.current_xinfa_line = player.cultivation_system.skill_ids_line3
        elif cultivation_data.get("current_xinfa_line") == 4:
            player.cultivation_system.current_xinfa_line = player.cultivation_system.skill_ids_line4
        else:
            player.cultivation_system.current_xinfa_line = None

        # 恢复心法等级
        player.cultivation_system.current_xinfa_level = cultivation_data.get("current_xinfa_level", 0)

        # 恢复修为点
        player.cultivation_system.used_points = cultivation_data.get("used_points", 0)
        player.cultivation_system.unused_points = cultivation_data.get("unused_points", 0)

        print("0.正在恢复修为数据，原始数据为: ", cultivation_data)
        # 恢复五行培养数据，包括 level 和 attributes_per_level
        player.cultivation_system.cultivation_data = {
            element: {
                "level": data["level"],
                "attributes_per_level": {
                    int(level): attributes
                    for level, attributes in data.get("attributes_per_level", {}).items()
                }
            }
            for element, data in cultivation_data.get("cultivation_data", {}).items()
        }
        print("0.恢复后的修为数据: ", player.cultivation_system.cultivation_data)

        # 更新修为等级
        for element, data in cultivation_data["cultivation_data"].items():
            player.cultivation_system.cultivation_data[element]["level"] = data["level"]
            player.cultivation_system.cultivation_data[element]["attributes_per_level"] = data.get(
                "attributes_per_level", {})

        # 读档后手动更新玩家状态
        player.update_stats()
        player.load_cultivation_from_save_data(save_data)

        # 恢复 NPC 好感度
        npcs_affection = save_data.get("npcs_affection", {})
        for npc_id, affection in npcs_affection.items():
            if npc_id in npc_library:
                npc_library[npc_id].affection = affection
        # 恢复故事
        story_data = save_data.get("story_progress", {})
        if story_data:
            player.story_progress = story_data
            if "completed_nodes" not in player.story_progress:
                print("未找到已完成的节点，初始化")
                player.story_progress["completed_nodes"] = []

            if "chapters_completed" not in player.story_progress:
                print("未找到章节完成情况，初始化")
                player.story_progress["chapters_completed"] = {"1": False, "2": False, "3": False, "4": False}

        else:
            print("未找到故事进度，初始化")
            player.story_progress = {
                "current_chapter": 1,
                "current_node": 1,
                "completed_nodes": [],  # 初始化为空列表
                "chapters_completed": {"1": False, "2": False, "3": False, "4": False},  # 初始化章节完成情况
            }

        # 将玩家设置到全局游戏状态
        game_state.set_player(player)
        # 重新加载地图等数据
        for map_number, map_obj in map_library.items():
            game_state.add_map(map_number, map_obj)
        # 初始化 NPC，跳过已被移除的 NPC
        for npc_number, npc_obj in npc_library.items():
            if npc_number not in game_state.player.npcs_removed:
                game_state.add_npc(npc_number, npc_obj)
            else:
                print(f"跳过已被移除的 NPC: {npc_number}")

        # 在地图上移除已标记为移除的 NPC
        for map_obj in game_state.maps.values():
            # 检查每个地图的 NPC 列表，移除已被删除的 NPC
            for npc in map_obj.npcs[:]:  # 使用副本来避免修改时出错
                if npc.number in game_state.player.npcs_removed:
                    print(f"移除地图中的 NPC: {npc.name} (编号: {npc.number})")
                    map_obj.npcs.remove(npc)

        # dlc1特质
        try:
            dlc_module = importlib.import_module('dlc.dlc_traits')  # 动态导入DLC模块
            dlc_traits = dlc_module.DLCTraits()  # 实例化DLC特质类
        except ModuleNotFoundError:
            dlc_traits = None  # 如果DLC不存在，设为None
        except AttributeError:
            # 如果模块存在但不包含 DLCTraits 类，处理错误
            print("DLC模块存在，但未找到 DLCTraits 类。")
            dlc_traits = None

        player.applied_traits = set(player_data["applied_traits"])  # 恢复 applied_traits

        if player_data["traits"]:
            player.traits = {}
            trait_module = importlib.import_module("dlc.dlc_traits.traits")  # 动态导入
            Trait = getattr(trait_module, "Trait")  # 获取 Trait 类
            for trait_name, trait_data in player_data["traits"].items():
                player.traits[trait_name] = Trait(**trait_data)  # 动态实例化特质
        else:
            player.traits = None

        # 如果dlc_traits存在，则重新注册特质相关的钩子
        if dlc_traits:
            dlc_traits.register_trait_hooks(player)

        player.update_stats()

        print(f"Player set in GameState: {player}")
        return player


def end_game():
    print("结束征程，感谢你的游戏！")
    sys.exit()


# 游戏入口
if __name__ == "__main__":
    show_title_screen()
