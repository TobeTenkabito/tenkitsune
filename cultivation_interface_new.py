import logging
from typing import Dict, Any

ATTRIBUTE_TRANSLATION = {
    "cultivation_attack": "攻击",
    "cultivation_crit": "暴击",
    "cultivation_speed": "速度",
    "cultivation_penetration": "穿透",
    "cultivation_mp": "法力值",
    "cultivation_hp": "生命值",
    "cultivation_crit_damage": "暴击伤害",
    "cultivation_defense": "防御",
    "cultivation_resistance": "抗性"
}


class CultivationInterface:
    def __init__(self, cultivation_system, player, game_state=None):
        self.cultivation_system = cultivation_system
        self.player = player
        self.game_state = game_state  # 可选，用于状态管理
        self.logger = logging.getLogger('CultivationInterface')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('game.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_cultivation_menu(self) -> Dict[str, Any]:
        """返回修为系统主菜单选项"""
        self.logger.info("Fetching cultivation system menu")
        return {
            "status": "success",
            "title": "修为系统菜单",
            "options": [
                {"id": 1, "text": "分配修为点数"},
                {"id": 2, "text": "选择心法线"},
                {"id": 3, "text": "检查心法解锁"},
                {"id": 4, "text": "展示当前心法技能信息"},
                {"id": 5, "text": "重置修为和心法"},
                {"id": 6, "text": "退出菜单"}
            ]
        }

    def get_allocate_points_menu(self) -> Dict[str, Any]:
        """返回分配点数子菜单"""
        self.logger.info("Fetching allocate points menu")
        return {
            "status": "success",
            "title": "分配修为点数",
            "unused_points": self.cultivation_system.unused_points,
            "cultivation_point": self.cultivation_system.player.cultivation_point,
            "options": [
                {"id": 1, "text": "金"},
                {"id": 2, "text": "木"},
                {"id": 3, "text": "水"},
                {"id": 4, "text": "火"},
                {"id": 5, "text": "土"},
                {"id": 6, "text": "返回主菜单"}
            ]
        }

    def get_xinfa_line_menu(self) -> Dict[str, Any]:
        """返回选择心法路线子菜单"""
        self.logger.info("Fetching xinfa line menu")
        return {
            "status": "success",
            "title": "选择心法路线",
            "options": [
                {"id": 1, "text": "第一条心法线"},
                {"id": 2, "text": "第二条心法线"},
                {"id": 3, "text": "第三条心法线"},
                {"id": 0, "text": "返回主菜单"}
            ]
        }

    def get_element_attributes(self, element: str) -> Dict[str, Any]:
        """返回指定元素的修为属性"""
        self.logger.info(f"Fetching attributes for element {element}")
        data = self.cultivation_system.cultivation_data.get(element, {})
        current_level = data.get("level", 0)
        result = {
            "status": "success",
            "element": element,
            "current_level": current_level
        }

        if current_level == 0:
            result["message"] = "当前没有任何属性加成，请提升修为等级以获得加成"
            result["current_attributes"] = {}
        else:
            result["current_attributes"] = {
                ATTRIBUTE_TRANSLATION.get(attr, attr): value
                for attr, value in data.get('attributes_per_level', {}).get(current_level, {}).items()
            }

        if current_level < self.cultivation_system.max_level:
            next_level = current_level + 1
            result["next_level"] = next_level
            result["next_attributes"] = {
                ATTRIBUTE_TRANSLATION.get(attr, attr): value
                for attr, value in data.get('attributes_per_level', {}).get(next_level, {}).items()
            }
        else:
            result["message"] = result.get("message", "") + f"{element} 修为已达到最高等级"
            result["next_level"] = None
            result["next_attributes"] = {}

        return result

    def upgrade_element(self, element: str) -> Dict[str, Any]:
        """提升指定元素的修为"""
        self.logger.info(f"Attempting to upgrade element {element}")
        try:
            self.cultivation_system.upgrade(element)
            self.logger.info(f"Upgraded element {element} successfully")
            # 可能的跨界面信号
            return {
                "status": "success",
                "message": f"成功提升 {element} 修为",
                "next_action": "task" if self.cultivation_system.is_task_related(element) else None  # 示例
            }
        except Exception as e:
            self.logger.error(f"Failed to upgrade element {element}: {str(e)}")
            return {"error": f"无法提升 {element} 修为: {str(e)}"}

    def select_xinfa_line(self, line_number: int) -> Dict[str, Any]:
        """选择心法路线"""
        self.logger.info(f"Attempting to select xinfa line {line_number}")
        try:
            self.cultivation_system.select_xinfa_line(line_number)
            skills = self.get_xinfa_skills()
            self.logger.info(f"Selected xinfa line {line_number} successfully")
            return {
                "status": "success",
                "message": f"已选择心法路线 {line_number}",
                "skills": skills["skills"],
                "next_action": "task" if self.cultivation_system.is_xinfa_task_related(line_number) else None  # 示例
            }
        except Exception as e:
            self.logger.error(f"Failed to select xinfa line {line_number}: {str(e)}")
            return {"error": f"无法选择心法路线 {line_number}: {str(e)}"}

    def check_xinfa_unlock(self) -> Dict[str, Any]:
        """检查心法解锁状态"""
        self.logger.info("Checking xinfa unlock status")
        try:
            result = self.cultivation_system.check_xinfa_unlock()
            return {
                "status": "success",
                "unlock_status": result  # 假设 check_xinfa_unlock 返回解锁信息
            }
        except Exception as e:
            self.logger.error(f"Failed to check xinfa unlock: {str(e)}")
            return {"error": f"无法检查心法解锁状态: {str(e)}"}

    def get_xinfa_skills(self) -> Dict[str, Any]:
        """返回当前心法线技能信息"""
        self.logger.info("Fetching xinfa skills")
        if not self.cultivation_system.current_xinfa_line:
            self.logger.warning("No xinfa line selected")
            return {"status": "success", "message": "尚未选择心法线", "skills": []}

        skills = [
            {
                "level": level,
                "name": skill.name,
                "description": skill.description,
                "status": "已解锁" if level <= self.cultivation_system.current_xinfa_level else "未解锁"
            }
            for level, skill in self.cultivation_system.current_xinfa_line.items()
        ]
        return {"status": "success", "skills": skills}

    def reset_cultivation(self) -> Dict[str, Any]:
        """重置修为和心法"""
        self.logger.info("Attempting to reset cultivation")
        try:
            self.cultivation_system.reset()
            self.logger.info("Cultivation reset successfully")
            return {"status": "success", "message": "修为和心法已重置"}
        except Exception as e:
            self.logger.error(f"Failed to reset cultivation: {str(e)}")
            return {"error": f"无法重置修为和心法: {str(e)}"}