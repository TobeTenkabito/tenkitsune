import logging
from typing import Dict, Any
from common.module.item import Material
from common.module.synthesis import synthesize, get_synthesis_result, get_available_synthesis_targets
from library.material_library import material_library
from all.synthesis_recipes import synthesis_recipes


class SynthesisInterface:
    def __init__(self, player, game_state=None):
        self.player = player
        self.game_state = game_state  # 可选，用于状态管理
        self.logger = logging.getLogger('SynthesisInterface')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('game.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_synthesis_menu(self) -> Dict[str, Any]:
        """返回合成系统菜单选项"""
        self.logger.info("Fetching synthesis system menu")
        return {
            "status": "success",
            "title": "合成系统",
            "options": [
                {"id": 1, "text": "选择要合成的物品"},
                {"id": 2, "text": "选择栏位 1 的材料"},
                {"id": 3, "text": "选择栏位 2 的材料"},
                {"id": 4, "text": "选择栏位 3 的材料"},
                {"id": 5, "text": "合成"},
                {"id": 6, "text": "返回主界面"}
            ],
            "synthesis_slots": [
                {
                    "slot": i + 1,
                    "name": slot.name if slot else "空",
                    "quantity": slot.quantity if slot else 0
                }
                for i, slot in enumerate(self.player.synthesis_slots)
            ]
        }

    def get_inventory(self) -> Dict[str, Any]:
        """返回背包物品列表"""
        self.logger.info("Fetching inventory for synthesis")
        inventory_dict = {}
        for item in self.player.inventory:
            if item.name in inventory_dict:
                inventory_dict[item.name] += item.quantity
            else:
                inventory_dict[item.name] = item.quantity

        items = [
            {
                "number": i + 1,
                "name": name,
                "quantity": quantity,
                "is_material": isinstance(self.player.inventory[i], Material)
            }
            for i, (name, quantity) in enumerate(inventory_dict.items())
        ]
        return {
            "status": "success",
            "items": items,
            "message": "背包物品列表" if items else "背包为空"
        }

    def get_synthesis_targets(self, page: int = 0, per_page: int = 7) -> Dict[str, Any]:
        """返回可合成的物品列表（支持分页）"""
        self.logger.info(f"Fetching synthesis targets for page {page}")
        available_targets = get_available_synthesis_targets(self.player)
        if not available_targets:
            self.logger.warning("No available synthesis targets")
            return {"status": "success", "items": [], "message": "当前没有可合成的物品", "total_pages": 0}

        start = page * per_page
        end = start + per_page
        targets_on_page = available_targets[start:end]

        items = [
            {
                "number": i + 1,
                "material_number": material_number,
                "name": get_synthesis_result(material_number).name,
                "required_materials": [
                    {"name": material_library[m_num].name, "quantity": qty}
                    for m_num, qty in synthesis_recipes[material_number]["materials"].items()
                ]
            }
            for i, material_number in enumerate(targets_on_page)
        ]
        total_pages = (len(available_targets) + per_page - 1) // per_page
        return {
            "status": "success",
            "items": items,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "message": "可合成物品列表" if items else "无更多物品"
        }

    def select_synthesis_target(self, material_number: int) -> Dict[str, Any]:
        """选择要合成的物品并自动填充合成槽"""
        self.logger.info(f"Selecting synthesis target {material_number}")
        if material_number not in synthesis_recipes:
            self.logger.error(f"Invalid synthesis target {material_number}")
            return {"error": "无效的合成目标"}

        try:
            required_materials = synthesis_recipes[material_number]["materials"]
            for slot_index, (m_num, quantity) in enumerate(required_materials.items()):
                material = material_library[m_num]
                material_copy = Material(
                    material.number, material.name, material.description,
                    material.quality, material.price, quantity
                )
                self.player.set_synthesis_slot(slot_index, material_copy)
            self.logger.info(f"Selected synthesis target {material_number}, slots updated")
            return {
                "status": "success",
                "message": f"已选择合成目标 {get_synthesis_result(material_number).name}",
                "synthesis_slots": [
                    {
                        "slot": i + 1,
                        "name": slot.name if slot else "空",
                        "quantity": slot.quantity if slot else 0
                    }
                    for i, slot in enumerate(self.player.synthesis_slots)
                ]
            }
        except Exception as e:
            self.logger.error(f"Failed to select synthesis target {material_number}: {str(e)}")
            return {"error": f"选择合成目标失败: {str(e)}"}

    def set_synthesis_slot(self, slot_index: int, item_number: int, quantity: int) -> Dict[str, Any]:
        """设置合成槽的材料"""
        self.logger.info(f"Setting synthesis slot {slot_index} with item {item_number}, quantity {quantity}")
        inventory_dict = {i + 1: item for i, item in enumerate(self.player.inventory)}
        item = inventory_dict.get(item_number)
        if not item:
            self.logger.error(f"Item {item_number} not found in inventory")
            return {"error": "背包中没有该物品"}

        if not isinstance(item, Material):
            self.logger.error(f"Item {item_number} is not a material")
            return {"error": "请选择有效的材料"}

        if quantity < 1 or quantity > item.quantity:
            self.logger.error(f"Invalid quantity {quantity} for item {item_number}")
            return {"error": f"无效的数量 (1-{item.quantity})"}

        try:
            material_copy = Material(
                item.number, item.name, item.description, item.quality, item.price, quantity
            )
            self.player.set_synthesis_slot(slot_index, material_copy)
            self.logger.info(f"Set slot {slot_index} with {item.name} x{quantity}")
            return {
                "status": "success",
                "message": f"{item.name} x{quantity} 已放入栏位 {slot_index + 1}",
                "synthesis_slots": [
                    {
                        "slot": i + 1,
                        "name": slot.name if slot else "空",
                        "quantity": slot.quantity if slot else 0
                    }
                    for i, slot in enumerate(self.player.synthesis_slots)
                ]
            }
        except Exception as e:
            self.logger.error(f"Failed to set synthesis slot {slot_index}: {str(e)}")
            return {"error": f"设置合成槽失败: {str(e)}"}

    def synthesize_item(self, material_number: int, quantity: int) -> Dict[str, Any]:
        """执行合成操作"""
        self.logger.info(f"Attempting to synthesize item {material_number} x{quantity}")
        if material_number not in synthesis_recipes:
            self.logger.error(f"Invalid synthesis target {material_number}")
            return {"error": "无效的合成目标"}

        try:
            max_quantity = min(
                self.player.get_material_quantity(m_num) // qty
                for m_num, qty in synthesis_recipes[material_number]["materials"].items()
            )
            if quantity < 1 or quantity > max_quantity:
                self.logger.error(f"Invalid synthesis quantity {quantity}, max: {max_quantity}")
                return {"error": f"无效的合成数量 (1-{max_quantity})"}

            success, message = synthesize(self.player, material_number, quantity)
            if success:
                self.logger.info(f"Synthesized item {material_number} x{quantity}: {message}")
                return {
                    "status": "success",
                    "message": message,
                    "next_action": "bag",  # 提示更新背包
                    "task_trigger": get_synthesis_result(material_number).is_task_related
                                    if hasattr(get_synthesis_result(material_number), "is_task_related")
                                    else False  # 示例：任务道具
                }
            else:
                self.logger.error(f"Failed to synthesize item {material_number}: {message}")
                return {"error": message}
        except Exception as e:
            self.logger.error(f"Synthesis failed for {material_number}: {str(e)}")
            return {"error": f"合成失败: {str(e)}"}