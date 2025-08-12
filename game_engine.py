import copy
import random
import json
import os
import importlib
import logging
from typing import Dict, Any
from common.interface.bag_interface import BagInterface
from common.interface.bag_interface_new import BagInterface
from common.interface.cultivation_interface_new import CultivationInterface
from common.interface.synthesis_interface import show_synthesis_interface
from common.interface.synthesis_interface_new import SynthesisInterface
from common.interface.lottery_interface import LotteryInterface
from common.interface.task_interface_new import TaskInterface
from common.interface.market_interface import show_market_interface
from common.interface.market_interface_new import MarketInterface
from common.interface.npc_interface_new import NPCInterface
from common.interface.dungeon_interface_new import DungeonInterface
from common.interface.map_interface_new import MapInterface
from library.material_library import material_library
from library.npc_library import npc_library
from library.map_library import map_library
from library.lottery_library import lottery_library
from common.module.story import load_story_from_json, Chapter
from common.module.battle import Battle
from common.module.market import Market


class GameEngine:
    def __init__(self, game_state, dlc_manager):
        self.game_state = game_state
        self.dlc_manager = dlc_manager
        self.slot_number = None
        self.current_player = None
        self.debug = False
        self.lottery_pool = None
        self.market = Market()

        # 初始化日志
        self.logger = logging.getLogger('GameEngine')
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        # 文件处理器
        file_handler = logging.FileHandler('game.log', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)

    def choose_at_main(self):
        """Display the title screen and handle user choice."""
        self.logger.info("Displaying title screen")
        return {
            "title": "天狐修炼纪",
            "options": [
                {"id": 1, "text": "旅途开始"},
                {"id": 2, "text": "前尘忆梦（读档）"},
                {"id": 3, "text": "结束征程（退出）"}
            ]
        }

    def process_main_choice(self, choice):
        """Process the user's choice from the title screen."""
        if choice == 1:
            return self.begin_game_at_start()
        elif choice == 2:
            self.slot_number = self.choose_save_slot()
            self.current_player = self.load_game(self.slot_number)
            if self.current_player:
                return self.enter_main_screen()
            return {"error": "Failed to load game"}
        elif choice == 3:
            self.end_game()
        return {"error": "Invalid choice"}

    def begin_game_at_start(self):
        """Start a new game, initializing player, maps, NPCs, and inventory."""
        try:
            # Initialize player
            self.game_state.initialize_player(1, "白夙")
            self.current_player = self.game_state.get_player()
            self.logger.info(f"Player {self.current_player.name} initialized successfully")
            if not self.current_player:
                return {"error": "Player initialization failed"}

            # Initialize maps
            for map_number, map_obj in map_library.items():
                self.game_state.add_map(map_number, map_obj)

            # Initialize NPCs
            for npc_number, npc_obj in npc_library.items():
                self.game_state.add_npc(npc_number, npc_obj)

            # Set initial inventory
            coin = material_library[100000]
            coin.quantity += 99
            self.current_player.add_to_inventory(coin)
            beidou = material_library[120000]
            beidou.quantity += 199
            self.current_player.add_to_inventory(beidou)

            self.slot_number = self.choose_save_slot()
            return self.enter_main_screen()
        except Exception as e:
            return {"error": f"Failed to start new game: {str(e)}"}

    def load_game_from_memory(self):
        """Show available save slots for loading a game."""
        slots = []
        for i in range(1, 6):
            save_file = self.get_save_file_path(i)
            slots.append({
                "slot": i,
                "status": "Saved" if os.path.exists(save_file) else "Empty"
            })
        return {"save_slots": slots}

    def player_condition(self):
        """Return the current player's status and map information."""
        if not self.current_player:
            return {"error": "No player loaded"}
        current_map = self.game_state.get_map(self.current_player.map_location)
        return {
            "player": {
                "name": self.current_player.name,
                "level": self.current_player.level,
                "exp": self.current_player.exp,
                "max_exp": self.current_player.max_exp,
                "hp": self.current_player.hp,
                "max_hp": self.current_player.max_hp,
                "mp": self.current_player.mp,
                "max_mp": self.current_player.max_mp,
                "attack": self.current_player.attack,
                "defense": self.current_player.defense,
                "speed": self.current_player.speed,
                "cultivation_point": self.current_player.cultivation_point
            },
            "map": {
                "name": current_map.name if current_map else "Unknown",
                "id": self.current_player.map_location
            }
        }

    def action_system(self):
        """Display the main game interface with available actions."""
        if not self.current_player:
            return {"error": "No player loaded"}
        return {
            "title": "游戏主界面",
            "player_info": self.player_condition(),
            "actions": [
                {"id": 1, "text": "背包互动"},
                {"id": 2, "text": "修为互动"},
                {"id": 3, "text": "合成互动"},
                {"id": 4, "text": "抽奖互动"},
                {"id": 5, "text": "集市互动"},
                {"id": 6, "text": "探索地图"},
                {"id": 7, "text": "闭关修炼"},
                {"id": 8, "text": "保存游戏"},
                {"id": 9, "text": "读档游戏"},
                {"id": 10, "text": "离开游戏"},
                {"id": 0, "text": "故事模式"}
            ]
        }

    def process_action(self, action_id):
        """Process the selected action from the main interface."""
        if not self.current_player:
            return {"error": "No player loaded"}

        if action_id == 1:
            return BagInterface(self.current_player).show_bag_interface()
        elif action_id == 2:
            cultivation_interface = CultivationInterface(self.current_player.cultivation_system, self.game_state)
            return cultivation_interface.get_cultivation_menu()
        elif action_id == 3:
            return show_synthesis_interface(self.current_player)
        elif action_id == 4:
            lottery_pool = lottery_library[1]
            return LotteryInterface(self.current_player).show_lottery_interface(lottery_pool)
        elif action_id == 5:
            return show_market_interface(self.current_player)
        elif action_id == 6:
            return self.explore_current_map()
        elif action_id == 7:
            return self.start_training()
        elif action_id == 8:
            return self.save_game(self.current_player, self.slot_number)
        elif action_id == 9:
            self.slot_number = self.choose_save_slot()
            self.current_player = self.load_game(self.slot_number)
            if self.current_player:
                return self.enter_main_screen()
            return {"error": "Failed to load game"}
        elif action_id == 10:
            self.end_game()
        elif action_id == 0:
            return self.start_story(self.slot_number)
        return {"error": "Invalid action"}

    def explore_current_map(self):
        """Explore the current map."""
        current_map = self.game_state.get_map(self.current_player.map_location)
        if current_map:
            return {
                "status": "success",
                "map_name": current_map.name,
                "exploration": current_map.explore()
            }
        return {
            "error": f"Unable to explore map: {self.current_player.map_location}"
        }

    def start_training(self):
        """Train the player, increasing stats based on cultivation."""
        if not self.current_player:
            return {"error": "No player loaded"}

        self.current_player.hp = max(0, self.current_player.hp)
        coefficient = random.randint(800, 1200) / 1000
        train_exp = (100 + 0.02 * self.current_player.max_exp + 10 * self.current_player.level) * coefficient
        train_hp = 0.1 * self.current_player.max_hp * coefficient
        train_mp = 0.1 * self.current_player.max_mp * coefficient
        self.current_player.hp += train_hp
        self.current_player.mp += train_mp
        self.current_player.gain_exp(train_exp)
        self.current_player.update_stats()

        return {
            "status": "success",
            "message": f"{self.current_player.name} 修炼结束",
            "results": {
                "exp_gained": train_exp,
                "hp_restored": train_hp,
                "mp_restored": train_mp,
                "efficiency": coefficient
            }
        }

    def start_story(self, slot_number):
        """Enter story mode, allowing chapter selection or continuation."""
        from common.module.story import StoryManager
        if not self.current_player:
            return {"error": "No player loaded"}

        dynamic_battle = Battle(player=self.current_player, allies=[], enemies=[])
        chapters = self.define_chapters(self.current_player, dynamic_battle)
        story_manager = StoryManager(self.current_player, chapters)

        def save_callback():
            self.save_game(self.current_player, slot_number)

        return {
            "title": "故事模式",
            "options": [
                {"id": 1, "text": "从本章开头开始"},
                {"id": 2, "text": "从保存节点开始"},
                {"id": 3, "text": "返回上一级"}
            ],
            "callback": lambda choice: self.process_story_choice(choice, story_manager, save_callback)
        }

    def process_story_choice(self, choice, story_manager, save_callback):
        """Process the story mode choice."""
        if choice == 1:
            selected_chapter = story_manager.select_chapter()
            if selected_chapter:
                return story_manager.start_chapter_from_beginning(save_callback=save_callback)
            return {"error": "Chapter not selected or locked"}
        elif choice == 2:
            return story_manager.continue_from_saved_node(save_callback=save_callback)
        elif choice == 3:
            return self.enter_main_screen()
        return {"error": "Invalid choice"}

    def define_chapters(self, player, dynamic_battle):
        """Define the chapters for story mode."""
        chapters = []
        for i in range(1, 5):
            chapter = Chapter(i, f"第{i}章", None, None)
            load_story_from_json(f'chapter/chapter{i}.json', player, dynamic_battle, chapter=chapter)
            chapter.is_completed = player.story_progress["chapters_completed"].get(str(i), False)
            chapters.append(chapter)
        return chapters

    def enter_main_screen(self):
        """Enter the main game screen, returning the action system interface."""
        if not self.current_player:
            return {"error": "No player loaded"}
        current_map = self.game_state.get_map(self.current_player.map_location)
        if not current_map:
            return {"error": f"Failed to load map: {self.current_player.map_location}"}
        return self.action_system()

    def get_save_file_path(self, slot_number):
        """Return the file path for a save slot."""
        return f"data/save/save_slot_{slot_number}.json"

    def show_save_slots(self):
        """Display available save slots (already implemented)."""
        print("\n可用存档列表:")
        for i in range(1, 6):
            save_file = self.get_save_file_path(i)
            if os.path.exists(save_file):
                print(f"{i}. 存档 {i} (已保存)")
            else:
                print(f"{i}. 存档 {i} (空)")

    def choose_save_slot(self):
        """Prompt user to choose a save slot (already implemented)."""
        while True:
            self.show_save_slots()
            print("如果您是第一次进入游戏，输入的存档位将作为故事模式进度的保存位置。")
            choice = input("请输入存档编号 (1-5): ")
            if choice.isdigit() and 1 <= int(choice) <= 5:
                return int(choice)
            else:
                print("无效选择，请输入1到5之间的数字。")

    def save_game(self, player, slot_number):
        """Save the game state to the specified slot."""
        if not player:
            return {"error": "No player to save"}

        save_file = self.get_save_file_path(slot_number)
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
                "traits": {k: v.__dict__ for k, v in (player.traits or {}).items()},
                "applied_traits": list(player.applied_traits),
                "equipment": [
                    {"item_number": equip.number, "quantity": equip.quantity}
                    for equip in player.equipment
                ],
                "skill": [skill.number for skill in player.skills],
                "inventory": [
                    {
                        "item_type": type(item).__name__,
                        "item_number": item.number,
                        "quantity": item.quantity
                    }
                    for item in player.inventory
                ],
                "completed_tasks": player.completed_tasks,
                "accepted_tasks": [
                    {"task_number": task.number, "kill_counts": task.kill_counts}
                    for task in player.accepted_tasks
                ],
                "ready_to_complete_tasks": [
                    {"task_number": task.number}
                    for task in player.ready_to_complete_tasks
                ],
                "defeated_enemies": player.defeated_enemies,
                "highest_floor": player.highest_floor,
                "dungeon_clears": player.dungeon_clears,
                "dungeons_cleared": list(player.dungeons_cleared),
                "talked_to_npcs": list(player.talked_to_npcs),
                "npcs_removed": list(player.npcs_removed),
                "given_items": {
                    npc_id: {
                        "item_number": item_number,
                        "quantity": quantity
                    }
                    for npc_id, items in player.given_items.items()
                    for item_number, quantity in items.items()
                },
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
                    "crit": self.current_player.medicine_crit,
                    "crit_damage": self.current_player.medicine_crit_damage,
                    "resistance": self.current_player.medicine_resistance,
                    "penetration": self.current_player.medicine_penetration
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
                "cultivation_system": {
                    "current_xinfa_line": (
                        1 if player.cultivation_system.current_xinfa_line == player.cultivation_system.skill_ids_line1
                        else 2 if player.cultivation_system.current_xinfa_line == player.cultivation_system.skill_ids_line2
                        else 3 if player.cultivation_system.current_xinfa_line == player.cultivation_system.skill_ids_line3
                        else 4 if player.cultivation_system.current_xinfa_line == player.cultivation_system.skill_ids_line4
                        else None
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
            "npcs_affection": {
                npc_id: npc.affection for npc_id, npc in npc_library.items()
            },
            "story_progress": {
                "current_chapter": player.story_progress["current_chapter"],
                "current dissection": player.story_progress["current_node"],
                "chapters_completed": player.story_progress["chapters_completed"],
                "completed_nodes": player.story_progress["completed_nodes"],
            }
        }

        with open(save_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=4)

        return {"status": "success", "message": f"Game saved to slot {slot_number}"}

    def load_game(self, slot_number):
        """Load the game state from the specified slot."""
        from common.module.item import Equipment, Skill, Medicine, Product, Warp, Material
        from common.character.player import Player
        from library.skill_library import skill_library
        from library.material_library import material_library
        from library.medicine_library import medicine_library
        from library.warp_library import warp_library
        from library.product_library import product_library
        from library.equipment_library import equipment_library
        from library.task_library import task_library
        save_file = self.get_save_file_path(slot_number)
        if not os.path.exists(save_file):
            return None

        with open(save_file, 'r', encoding='utf-8') as file:
            save_data = json.load(file)
            player_data = save_data.get("player", {})

            # Initialize player
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

            # Restore inventory
            for item_data in player_data["inventory"]:
                item_type = item_data["item_type"]
                item_number = item_data["item_number"]
                quantity = item_data["quantity"]

                if item_type == "Equipment":
                    equipment_data = equipment_library[item_number]
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
                        target_type=equipment_data.target_type if hasattr(equipment_data, 'target_type') else None,
                        target_scope=equipment_data.target_scope if hasattr(equipment_data, 'target_scope') else None,
                        effect_duration=equipment_data.effect_duration if hasattr(equipment_data,
                                                                                  'effect_duration') else None,
                        effect_changes=equipment_data.effect_changes if hasattr(equipment_data,
                                                                                'effect_changes') else None,
                        cost=equipment_data.cost if hasattr(equipment_data, 'cost') else None
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

            # Restore equipment and skills
            for equip_data in player_data["equipment"]:
                equipment = equipment_library[equip_data["item_number"]]
                player.add_to_equipment(copy.deepcopy(equipment))
            for skill_number in player_data["skill"]:
                skill = skill_library[skill_number]
                player.add_to_skill(copy.deepcopy(skill))

            # Restore tasks
            player.accepted_tasks = [
                task_library[task_data["task_number"]] for task_data in player_data.get("accepted_tasks", [])
            ]
            player.ready_to_complete_tasks = [
                task_library[task_data["task_number"]] for task_data in player_data.get("ready_to_complete_tasks", [])
            ]
            player.completed_tasks = player_data.get("completed_tasks", [])

            # Restore other player data
            player.defeated_enemies = player_data["defeated_enemies"]
            player.highest_floor = player_data["highest_floor"]
            player.dungeon_clears = player_data["dungeon_clears"]
            player.dungeons_cleared = set(player_data["dungeons_cleared"])
            player.talked_to_npcs = set(player_data["talked_to_npcs"])
            player.npcs_removed = set(player_data.get('npcs_removed', []))
            player.given_items = player_data["given_items"]

            # Restore attributes
            for attr_type in ["task", "dungeon", "cultivation", "medicine", "skill"]:
                attrs = player_data[f"{attr_type}_attributes"]
                for key, value in attrs.items():
                    setattr(player, f"{attr_type}_{key}", value)

            # Restore cultivation system
            cultivation_data = player_data.get("cultivation_system", {})
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
            player.cultivation_system.current_xinfa_level = cultivation_data.get("current_xinfa_level", 0)
            player.cultivation_system.used_points = cultivation_data.get("used_points", 0)
            player.cultivation_system.unused_points = cultivation_data.get("unused_points", 0)
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

            # Update player stats
            player.update_stats()
            player.load_cultivation_from_save_data(save_data)

            # Restore NPC affection
            npcs_affection = save_data.get("npcs_affection", {})
            for npc_id, affection in npcs_affection.items():
                if npc_id in npc_library:
                    npc_library[npc_id].affection = affection

            # Restore story progress
            story_data = save_data.get("story_progress", {})
            if story_data:
                player.story_progress = story_data
                if "completed_nodes" not in player.story_progress:
                    player.story_progress["completed_nodes"] = []
                if "chapters_completed" not in player.story_progress:
                    player.story_progress["chapters_completed"] = {"1": False, "2": False, "3": False, "4": False}
            else:
                player.story_progress = {
                    "current_chapter": 1,
                    "current_node": 1,
                    "completed_nodes": [],
                    "chapters_completed": {"1": False, "2": False, "3": False, "4": False}
                }

            # Set player in game state
            self.game_state.set_player(player)
            self.current_player = player

            # Reload maps and NPCs
            for map_number, map_obj in map_library.items():
                self.game_state.add_map(map_number, map_obj)
            for npc_number, npc_obj in npc_library.items():
                if npc_number not in self.game_state.player.npcs_removed:
                    self.game_state.add_npc(npc_number, npc_obj)

            # Remove NPCs from maps
            for map_obj in self.game_state.maps.values():
                for npc in map_obj.npcs[:]:
                    if npc.number in self.game_state.player.npcs_removed:
                        map_obj.npcs.remove(npc)

            # Restore DLC traits
            try:
                dlc_module = importlib.import_module('dlc.dlc_traits')
                dlc_traits = dlc_module.DLCTraits()
            except (ModuleNotFoundError, AttributeError):
                dlc_traits = None

            player.applied_traits = set(player_data["applied_traits"])
            if player_data["traits"]:
                player.traits = {}
                trait_module = importlib.import_module("dlc.dlc_traits.traits")
                Trait = getattr(trait_module, "Trait")
                for trait_name, trait_data in player_data["traits"].items():
                    player.traits[trait_name] = Trait(**trait_data)
            else:
                player.traits = None

            if dlc_traits:
                dlc_traits.register_trait_hooks(player)

            player.update_stats()
            return player

    def end_game(self):
        """End the game and exit."""
        return {"status": "game_ended", "message": "结束征程，感谢你的游戏！"}

    def debug_mod(self):
        self.debug = not self.debug
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        self.logger.info(f"Debug mode {'enabled' if self.debug else 'disabled'}")
        return {"status": "success", "debug_mode": self.debug}

    def dlc_mode(self):
        """Handle DLC-specific actions."""

        def show_traits(self):
            for dlc in self.dlc_manager.dlc_modules:
                if hasattr(dlc, 'show_traits'):
                    return dlc.show_traits(self.current_player)
            return {"error": "No DLC traits available"}

        return {"show_traits": show_traits}

    # 任务交互界面
    def process_task_choice(self, choice: int, task_number: int = None):
        """处理任务系统选择"""
        if not self.current_player:
            return {"error": "No player loaded"}
        task_interface_new = TaskInterface(self.current_player, self.game_state)
        if choice == 1:
            return task_interface_new.get_current_tasks()
        elif choice == 2:
            return task_interface_new.get_completed_tasks()
        elif choice == 3:
            return task_interface_new.get_available_tasks()
        elif choice == 4:
            return self.action_system()  # 返回主界面
        elif choice == 5 and task_number is not None:
            return task_interface_new.accept_task(task_number)  # 接取任务
        return {"error": "Invalid task choice"}

    # 处理背包界面
    def process_bag_choice(self, choice: int, number: int = None):
        """处理背包系统选择"""
        if not self.current_player:
            return {"error": "No player loaded"}
        bag_interface = BagInterface(self.current_player, self.game_state)
        self.logger.info(f"Processing bag choice {choice} with number {number}")

        if choice == 1:
            return bag_interface.get_equipment()
        elif choice == 2:
            return bag_interface.get_skills()
        elif choice == 3:
            return bag_interface.get_inventory()
        elif choice == 4:
            return bag_interface.get_equipment_menu()
        elif choice == 5:
            return bag_interface.get_skills_menu()
        elif choice == 6:
            return self.action_system()  # 返回主界面
        elif choice == 7 and number is not None:  # 装备物品
            result = bag_interface.equip_item(number)
            # 处理跨界面信号
            if result.get("next_action") == "task":
                return TaskInterface(self.current_player, self.game_state).get_task_menu()
            return result
        elif choice == 8 and number is not None:  # 卸下物品
            return bag_interface.unequip_item(number)
        elif choice == 9 and number is not None:  # 装备技能
            result = bag_interface.equip_skill(number)
            if result.get("next_action") == "cultivation":
                return CultivationInterface(self.current_player.cultivation_system, self.game_state).get_cultivation_menu()
            return result
        elif choice == 10 and number is not None:  # 卸下技能
            return bag_interface.unequip_skill(number)
        return {"error": "Invalid bag choice"}

    # 抽奖界面
    def process_lottery_choice(self, choice: int):
        """处理抽奖系统选择"""
        if not self.current_player:
            return {"error": "No player loaded"}
        if not self.lottery_pool:
            return {"error": "Lottery pool not initialized"}
        lottery_interface = LotteryInterface(self.current_player)
        self.logger.info(f"Processing lottery choice {choice}")

        if choice == 1:
            result = lottery_interface.perform_lottery(1, self.lottery_pool)
            return self._handle_lottery_result(result)
        elif choice == 2:
            result = lottery_interface.perform_lottery(10, self.lottery_pool)
            return self._handle_lottery_result(result)
        elif choice == 3:
            result = lottery_interface.perform_lottery(100, self.lottery_pool)
            return self._handle_lottery_result(result)
        elif choice == 0:
            return self.action_system()  # 返回主界面
        return {"error": "Invalid lottery choice"}

    # 抽奖池
    def _handle_lottery_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """处理抽奖结果，更新背包并协调跨界面交互"""
        if "error" in result:
            return result
        if result.get("next_action") == "bag" and "reward_items" in result:
            bag_interface = BagInterface(self.current_player, self.game_state)
            for item in result["reward_items"]:
                self.current_player.add_to_inventory(item)  # 或通过 BagInterface 添加
            self.logger.info("Rewards added to inventory")
            return bag_interface.get_inventory()  # 显示更新后的背包
        if result.get("next_action") == "task":
            return TaskInterface(self.current_player, self.game_state).get_task_menu()
        return result

    # 市场界面
    def process_market_choice(self, choice: int, data: dict = None):
        """处理市场系统选择"""
        if not self.current_player:
            return {"error": "No player loaded"}
        market_interface = MarketInterface(self.current_player, self.market, self.game_state)
        self.logger.info(f"Processing market choice {choice} with data {data}")

        if choice == 1 and data and "item_number" in data and "quantity" in data:
            result = market_interface.sell_item(data["item_number"], data["quantity"])
            if result.get("next_action") == "bag":
                return BagInterface(self.current_player, self.game_state).get_inventory()
            return result
        elif choice == 2 and data and "item_number" in data and "quantity" in data:
            result = market_interface.buy_item(data["item_number"], data["quantity"])
            if result.get("next_action") == "bag":
                bag = BagInterface(self.current_player, self.game_state)
                if result.get("task_trigger"):
                    return TaskInterface(self.current_player, self.game_state).get_task_menu()
                return bag.get_inventory()
            return result
        elif choice == 3:
            return market_interface.refresh_market()
        elif choice == 0:
            return self.action_system()  # 返回主界面
        elif choice == 4:
            return market_interface.get_market_items()
        return {"error": "Invalid market choice"}

    # 合成界面
    def process_synthesis_choice(self, choice: int, data: dict = None):
        """处理合成系统选择"""
        if not self.current_player:
            return {"error": "No player loaded"}
        synthesis_interface = SynthesisInterface(self.current_player, self.game_state)
        self.logger.info(f"Processing synthesis choice {choice} with data {data}")

        if choice == 1 and data and "material_number" in data:
            return synthesis_interface.select_synthesis_target(data["material_number"])
        elif choice in [2, 3, 4] and data and "item_number" in data and "quantity" in data:
            slot_index = choice - 2  # 映射到 slot_index (0, 1, 2)
            return synthesis_interface.set_synthesis_slot(slot_index, data["item_number"], data["quantity"])
        elif choice == 5 and data and "material_number" in data and "quantity" in data:
            result = synthesis_interface.synthesize_item(data["material_number"], data["quantity"])
            if result.get("next_action") == "bag":
                bag = BagInterface(self.current_player, self.game_state)
                if result.get("task_trigger"):
                    return TaskInterface(self.current_player, self.game_state).get_task_menu()
                return bag.get_inventory()
            return result
        elif choice == 6:
            return self.action_system()  # 返回主界面
        elif choice == 7:
            page = data.get("page", 0) if data else 0
            return synthesis_interface.get_synthesis_targets(page=page)
        elif choice == 8:
            return synthesis_interface.get_inventory()
        return {"error": "Invalid synthesis choice"}

    # npc
    def process_npc_interaction(self, npc_id: int) -> Dict[str, Any]:
        """进入 NPC 交互"""
        self.logger.info(f"Processing NPC interaction for NPC ID {npc_id}")
        npc = self.game_state.get_npc(npc_id)  # 假设从 game_state 获取
        if not npc:
            return {"error": f"NPC {npc_id} not found"}
        return NPCInterface(self.current_player, npc, self.game_state).get_interact_menu()

    def process_npc_choice(self, npc_id: int, choice: int, data: dict = None) -> Dict[str, Any]:
        """处理 NPC 交互选择"""
        if not self.current_player:
            return {"error": "No player loaded"}
        npc = self.game_state.get_npc(npc_id)
        if not npc:
            return {"error": f"NPC {npc_id} not found"}
        npc_interface = NPCInterface(self.current_player, npc, self.game_state)
        self.logger.info(f"Processing NPC choice {choice} for NPC {npc.name} with data {data}")

        if choice == 1:
            return npc_interface.handle_daily_dialogue()
        elif choice == 2:
            task_index = data.get("task_index") if data else None
            if task_index is not None:
                return npc_interface.accept_task(task_index)
            return {
                "status": "success",
                "message": npc.get_task_dialogue_based_on_affection(),
                "tasks": [
                    {"index": i, "name": task.name}
                    for i, task in enumerate(npc.get_available_tasks())
                ]
            }
        elif choice == 3:
            return npc_interface.complete_task_dialogue()
        elif choice == 4:
            return npc_interface.deliver_task()
        elif choice == 5:
            item_index = data.get("item_index") if data else None
            quantity = data.get("quantity") if data else None
            if item_index is not None and quantity is not None:
                return npc_interface.give_gift(item_index, quantity)
            return npc_interface.get_inventory()
        elif choice == 6:
            exchange_index = data.get("exchange_index") if data else None
            if exchange_index is not None:
                return npc_interface.handle_exchange(exchange_index)
            return {
                "status": "success",
                "message": f"{npc.name} 提供以下物品进行交易：",
                "exchange_items": [
                    {
                        "index": i,
                        "offered_item": offered_item.name,
                        "required_item": details["item"].name,
                        "required_quantity": details["quantity"]
                    }
                    for i, (offered_item, details) in enumerate(npc.exchange.items())
                ]
            }
        elif choice == 7:
            return self.action_system()  # 返回主界面
        elif choice == 8:
            module_choice = data.get("module_choice") if data else None
            if module_choice is not None:
                if module_choice == 1:
                    return MarketInterface(self.current_player, self.market, self.game_state).get_market_menu()
                elif module_choice == 2:
                    result = npc_interface.start_battle()
                    if result.get("result") == "win":
                        kill = data.get("kill") if data else None
                        if kill is not None:
                            return npc_interface.handle_battle_result(kill)
                    return result
                elif module_choice == 3:
                    return SynthesisInterface(self.current_player, self.game_state).get_synthesis_menu()
                elif module_choice == 4:
                    return npc_interface.get_interact_menu()
            return npc_interface.get_function_modules()
        return {"error": "Invalid NPC choice"}

    # 秘境
    def process_dungeon_choice(self, choice: int, data: dict = None) -> Dict[str, Any]:
        """处理秘境交互选择"""
        if not self.current_player:
            return {"error": "No player loaded"}
        dungeon_interface = DungeonInterface(self.current_player, self.game_state)
        self.logger.info(f"Processing dungeon choice {choice} with data {data}")

        if choice == 1:
            dungeon_id = data.get("dungeon_id") if data else None
            if dungeon_id is not None:
                return dungeon_interface.enter_dungeon(dungeon_id)
            return dungeon_interface.get_dungeon_menu()
        elif choice == 2:
            dungeon_id = data.get("dungeon_id") if data else None
            floor_number = data.get("floor_number") if data else None
            if dungeon_id is not None and floor_number is not None:
                result = dungeon_interface.enter_floor(dungeon_id, floor_number)
                if result.get("next_action") == "bag":
                    return BagInterface(self.current_player, self.game_state).get_inventory()
                elif result.get("next_action") == "npc":
                    return self.process_npc_interaction(result["npc_id"])
                elif result.get("next_action") == "map":
                    return MapInterface.get_map_menu(self.game_state)
                elif result.get("rewards"):
                    task_updated = any(task.check_completion(self.current_player) for task in self.current_player.accepted_tasks)
                    if task_updated:
                        return TaskInterface(self.current_player, self.game_state).get_task_menu()
                return result
            return {"error": "缺少 dungeon_id 或 floor_number"}
        return {"error": "Invalid dungeon choice"}

    def process_map_choice(self, choice: int, data: dict = None) -> Dict[str, Any]:
        """处理地图交互选择"""
        if not self.current_player:
            return {"error": "No player loaded"}
        map_interface = MapInterface(self.current_player, self.game_state)
        self.logger.info(f"Processing map choice {choice} with data {data}")

        if choice == 1:  # 探索地图
            map_id = data.get("map_id") if data else None
            if map_id is not None:
                return map_interface.explore_area(map_id)
            return map_interface.get_map_menu()
        elif choice == 2:  # 与 NPC 交互
            map_id = data.get("map_id") if data else None
            npc_id = data.get("npc_id") if data else None
            if map_id is not None and npc_id is not None:
                result = map_interface.interact_with_npc(map_id, npc_id)
                if result.get("next_action") == "npc":
                    return self.process_npc_interaction(result["npc_id"])
                return result
            return {"error": "缺少 map_id 或 npc_id"}
        elif choice == 3:  # 采集物品
            map_id = data.get("map_id") if data else None
            item_name = data.get("item_name") if data else None
            if map_id is not None and item_name is not None:
                result = map_interface.collect_item(map_id, item_name)
                if result.get("status") == "success":
                    task_updated = any(task.check_completion(self.current_player) for task in self.current_player.accepted_tasks)
                    if task_updated:
                        return TaskInterface(self.current_player, self.game_state).get_task_menu()
                if result.get("next_action") == "bag":
                    return BagInterface(self.current_player, self.game_state).get_inventory()
                return result
            return {"error": "缺少 map_id 或 item_name"}
        elif choice == 4:  # 开始战斗
            map_id = data.get("map_id") if data else None
            battle_index = data.get("battle_index") if data else None
            if map_id is not None and battle_index is not None:
                result = map_interface.start_battle(map_id, battle_index)
                if result.get("next_action") == "map":
                    return map_interface.get_map_menu()
                return result
            return {"error": "缺少 map_id 或 battle_index"}
        elif choice == 5:  # 进入秘境
            map_id = data.get("map_id") if data else None
            dungeon_id = data.get("dungeon_id") if data else None
            if map_id is not None and dungeon_id is not None:
                result = map_interface.enter_dungeon(map_id, dungeon_id)
                if result.get("next_action") == "dungeon":
                    return DungeonInterface(self.current_player, self.game_state).enter_dungeon(dungeon_id)
                return result
            return {"error": "缺少 map_id 或 dungeon_id"}
        elif choice == 6:  # 查看邻接地图
            map_id = data.get("map_id") if data else None
            if map_id is not None:
                map_obj = self.game_state.get_map(map_id)
                if map_obj:
                    return {
                        "status": "success",
                        "message": f"邻接地图 - {map_obj.name}",
                        "adjacent_maps": [
                            {"id": map_id, "distance": info["distance"], "direction": info["direction"]}
                            for map_id, info in map_obj.adjacent_maps.items()
                        ]
                    }
                return {"error": f"地图 {map_id} 不存在"}
            return {"error": "缺少 map_id"}
        return {"error": "Invalid map choice"}
