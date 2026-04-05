from library.material_library import material_library
from library.equipment_library import equipment_library
from library.medicine_library import medicine_library
from library.product_library import product_library
from all.synthesis_recipes import synthesis_recipes


def can_synthesize(player, target_material_number, quantity=1):
    if target_material_number not in synthesis_recipes:
        return False, "无此合成配方"

    required_materials = synthesis_recipes[target_material_number]["materials"]
    for material_number, required_quantity in required_materials.items():
        if player.get_material_quantity(material_number) < required_quantity * quantity:
            return False, "材料不足或配方不正确"

    return True, "可以合成"


def get_synthesis_result(target_material_number):
    if target_material_number in material_library:
        return material_library[target_material_number]
    elif target_material_number in equipment_library:
        return equipment_library[target_material_number]
    elif target_material_number in medicine_library:
        return medicine_library[target_material_number]
    elif target_material_number in product_library:
        return medicine_library[target_material_number]
    else:
        raise KeyError(f"合成目标 {target_material_number} 不存在于已知库中")


def synthesize(player, target_material_number, quantity=1):
    can_synth, message = can_synthesize(player, target_material_number, quantity)
    if not can_synth:
        return False, message

    required_materials = synthesis_recipes[target_material_number]["materials"]
    for material_number, required_quantity in required_materials.items():
        if not player.decrease_material_quantity(material_number, required_quantity * quantity):
            return False, "材料减少失败"

    result_item = get_synthesis_result(target_material_number)
    result_item_copy = result_item.__class__(**result_item.__dict__)  # 复制结果物品对象
    result_item_copy.quantity = synthesis_recipes[target_material_number]["result_quantity"] * quantity
    player.add_to_inventory(result_item_copy)
    player.clear_synthesis_slots()
    return True, "合成成功"


def get_available_synthesis_targets(player):
    available_targets = []
    for target_material_number, recipe in synthesis_recipes.items():
        required_materials = recipe["materials"]
        if all(player.get_material_quantity(material_number) >= required_quantity for material_number, required_quantity in required_materials.items()):
            available_targets.append(target_material_number)
    return available_targets

