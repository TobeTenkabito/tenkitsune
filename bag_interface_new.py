# interface/bag_interface_new.py
import logging
from typing import Dict, Any
from common.character.player import Equipment, Skill


class BagInterface:
    def __init__(self, player, game_state=None):
        self.player = player
        self.game_state = game_state  # 可选，用于状态管理
        self.logger = logging.getLogger('BagInterface')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('game.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_bag_menu(self) -> Dict[str, Any]:
        """返回背包系统主菜单选项"""
        self.logger.info("Fetching bag system menu")
        return {
            "status": "success",
            "title": "玩家背包界面",
            "options": [
                {"id": 1, "text": "查看装备栏"},
                {"id": 2, "text": "查看技能栏"},
                {"id": 3, "text": "查看背包栏"},
                {"id": 4, "text": "装备/卸下装备"},
                {"id": 5, "text": "装备/卸下技能"},
                {"id": 6, "text": "返回游戏主界面"}
            ]
        }

    def get_equipment(self) -> Dict[str, Any]:
        """返回当前装备栏中的物品"""
        self.logger.info("Fetching equipment")
        if self.player.equipment:
            items = [
                {"number": item.number, "name": item.name, "description": item.description, "category": item.category}
                for item in self.player.equipment
            ]
            return {"status": "success", "items": items}
        return {"status": "success", "message": "装备栏为空", "items": []}

    def get_skills(self) -> Dict[str, Any]:
        """返回当前技能栏中的技能"""
        self.logger.info("Fetching skills")
        if self.player.skills:
            skills = [
                {"number": skill.number, "name": skill.name, "description": skill.description}
                for skill in self.player.skills
            ]
            return {"status": "success", "skills": skills}
        return {"status": "success", "message": "技能栏为空", "skills": []}

    def get_inventory(self) -> Dict[str, Any]:
        """返回背包中的物品"""
        self.logger.info("Fetching inventory")
        if self.player.inventory:
            items = [
                {"number": item.number, "name": item.name, "quantity": item.quantity, "description": item.description}
                for item in self.player.inventory
            ]
            return {"status": "success", "items": items}
        return {"status": "success", "message": "背包为空", "items": []}

    def get_equipment_menu(self) -> Dict[str, Any]:
        """返回装备管理子菜单"""
        self.logger.info("Fetching equipment management menu")
        return {
            "status": "success",
            "title": "装备管理",
            "options": [
                {"id": 1, "text": "装备物品"},
                {"id": 2, "text": "卸下物品"},
                {"id": 3, "text": "返回背包界面"}
            ]
        }

    def get_skills_menu(self) -> Dict[str, Any]:
        """返回技能管理子菜单"""
        self.logger.info("Fetching skills management menu")
        return {
            "status": "success",
            "title": "技能管理",
            "options": [
                {"id": 1, "text": "装备技能"},
                {"id": 2, "text": "卸下技能"},
                {"id": 3, "text": "返回背包界面"}
            ]
        }

    def equip_item(self, item_number: int) -> Dict[str, Any]:
        """从背包中装备物品"""
        self.logger.info(f"Attempting to equip item {item_number}")
        equipment_items = [item for item in self.player.inventory if isinstance(item, Equipment) and item.number == item_number]
        if not equipment_items:
            self.logger.error(f"Item {item_number} not found or not equippable")
            return {"error": f"背包中没有编号为 {item_number} 的可装备物品"}

        item = equipment_items[0]
        equipment_types = {"武器": 0, "防具": 0, "饰品": 0, "法宝": 0}
        for eq in self.player.equipment:
            if eq.category in equipment_types:
                equipment_types[eq.category] += 1

        if item.category in ["武器", "防具", "饰品"]:
            if equipment_types[item.category] >= 1:
                self.logger.error(f"Cannot equip {item.name}: {item.category} slot full")
                return {"error": f"{item.category} 已经装备，无法再装备 {item.name}"}
        elif item.category == "法宝":
            if equipment_types["法宝"] >= 3:
                self.logger.error(f"Cannot equip {item.name}: Talisman limit reached")
                return {"error": "法宝数量已达上限，无法再装备"}

        self.player.equipment.append(item)
        item.apply_attributes(self.player)
        self.player.inventory.remove(item)
        self.logger.info(f"Equipped item {item.name}")
        # 可能的跨界面信号
        return {
            "status": "success",
            "message": f"装备了 {item.name}",
            "next_action": "task" if item.is_task_related else None  # 示例：任务相关物品
        }

    def unequip_item(self, item_number: int) -> Dict[str, Any]:
        """卸下装备并返回到背包"""
        self.logger.info(f"Attempting to unequip item {item_number}")
        for item in self.player.equipment:
            if item.number == item_number:
                item.remove_attributes(self.player)
                self.player.equipment.remove(item)
                self.player.inventory.append(item)
                self.logger.info(f"Unequipped item {item.name}")
                return {"status": "success", "message": f"卸下了 {item.name}"}
        self.logger.error(f"Item {item_number} not found in equipment")
        return {"error": f"装备栏中没有编号为 {item_number} 的物品"}

    def equip_skill(self, skill_number: int) -> Dict[str, Any]:
        """从背包中装备技能"""
        self.logger.info(f"Attempting to equip skill {skill_number}")
        if len(self.player.skills) >= 9:
            self.logger.error("Skill slots full")
            return {"error": "技能栏已满，无法再装备新的技能"}

        available_skills = [item for item in self.player.inventory if isinstance(item, Skill) and item.number == skill_number]
        if not available_skills:
            self.logger.error(f"Skill {skill_number} not found or not equippable")
            return {"error": f"背包中没有编号为 {skill_number} 的可装备技能"}

        skill = available_skills[0]
        self.player.skills.append(skill)
        self.player.inventory.remove(skill)
        self.logger.info(f"Equipped skill {skill.name}")
        # 可能的跨界面信号
        return {
            "status": "success",
            "message": f"装备了技能 {skill.name}",
            "next_action": "cultivation" if skill.is_cultivation_related else None  # 示例：修炼相关技能
        }

    def unequip_skill(self, skill_number: int) -> Dict[str, Any]:
        """卸下技能并返回到背包"""
        self.logger.info(f"Attempting to unequip skill {skill_number}")
        for skill in self.player.skills:
            if skill.number == skill_number:
                self.player.skills.remove(skill)
                self.player.inventory.append(skill)
                self.logger.info(f"Unequipped skill {skill.name}")
                return {"status": "success", "message": f"卸下了技能 {skill.name}"}
        self.logger.error(f"Skill {skill_number} not found in skills")
        return {"error": f"技能栏中没有编号为 {skill_number} 的技能"}