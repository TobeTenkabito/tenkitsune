from common.module.item import Material
from common.module.synthesis import synthesize, get_synthesis_result, get_available_synthesis_targets
from library.material_library import material_library
from all.synthesis_recipes import synthesis_recipes


def display_inventory(player):
    inventory_dict = {}
    for item in player.inventory:
        if item.name in inventory_dict:
            inventory_dict[item.name] += item.quantity
        else:
            inventory_dict[item.name] = item.quantity

    print("背包:")
    for i, (name, quantity) in enumerate(inventory_dict.items(), start=1):
        print(f"{i}. {name} x {quantity}")


def choose_material(player, slot_index):
    display_inventory(player)
    choice = int(input(f"选择放入栏位 {slot_index + 1} 的材料编号: ")) - 1
    inventory_dict = {i: item for i, item in enumerate(player.inventory)}

    if 0 <= choice < len(inventory_dict):
        material = inventory_dict[choice]
        if isinstance(material, Material):
            quantity = int(input(f"选择放入栏位 {slot_index + 1} 的材料数量 (1-{material.quantity}): "))
            if 1 <= quantity <= material.quantity:
                material_copy = Material(material.number, material.name, material.description, material.quality, material.price, quantity)
                player.set_synthesis_slot(slot_index, material_copy)
                print(f"{material.name} x {quantity} 已放入栏位 {slot_index + 1}.")
            else:
                print("无效的数量。")
        else:
            print("请选择有效的材料。")
    else:
        print("无效的选择。")


def choose_synthesis_target(player):
    available_targets = get_available_synthesis_targets(player)
    if not available_targets:
        print("当前没有可合成的物品。")
        return None

    per_page = 7
    page = 0

    while True:
        start = page * per_page
        end = start + per_page
        targets_on_page = available_targets[start:end]

        print("可合成的物品:")
        for i, target_material_number in enumerate(targets_on_page, start=1):
            item = get_synthesis_result(target_material_number)
            required_materials_str = ", ".join([f"{material_library[material_number].name} x {quantity}" for material_number, quantity in synthesis_recipes[target_material_number]["materials"].items()])
            print(f"{i}. {item.name} - 需要材料: {required_materials_str}")

        print("8. 上一页")
        print("9. 下一页")
        print("0. 返回")

        choice = int(input("选择要合成的物品编号: "))

        if choice == 0:
            return None
        elif choice == 8:
            if page > 0:
                page -= 1
        elif choice == 9:
            if end < len(available_targets):
                page += 1
        elif 1 <= choice <= len(targets_on_page):
            return targets_on_page[choice - 1]
        else:
            print("无效的选择。")


def show_synthesis_interface(player):
    target_material_number = None

    while True:
        print("\n合成界面:")
        for i, slot in enumerate(player.synthesis_slots):
            if slot:
                print(f"栏位 {i + 1}: {slot.name} x {slot.quantity}")
            else:
                print(f"栏位 {i + 1}: 空")

        print("1. 选择要合成的物品")
        print("2. 选择栏位 1 的材料")
        print("3. 选择栏位 2 的材料")
        print("4. 选择栏位 3 的材料")
        print("5. 合成")
        print("6. 返回")

        choice = int(input("请输入选项编号: "))

        if choice == 1:
            target_material_number = choose_synthesis_target(player)
            if target_material_number:
                required_materials = synthesis_recipes[target_material_number]["materials"]
                for slot_index, (material_number, quantity) in enumerate(required_materials.items()):
                    material = material_library[material_number]
                    material_copy = Material(material.number, material.name, material.description, material.quality, material.price, quantity)
                    player.set_synthesis_slot(slot_index, material_copy)
        elif choice == 2:
            choose_material(player, 0)
        elif choice == 3:
            choose_material(player, 1)
        elif choice == 4:
            choose_material(player, 2)
        elif choice == 5:
            if target_material_number:
                max_quantity = min(player.get_material_quantity(material_number) // quantity for material_number, quantity in synthesis_recipes[target_material_number]["materials"].items())
                synthesis_quantity = int(input(f"请输入要合成的数量: "))
                if 1 <= synthesis_quantity <= max_quantity:
                    success, message = synthesize(player, target_material_number, synthesis_quantity)
                    print(message)
                else:
                    print("无效的数量。")
            else:
                print("请先选择要合成的物品。")
        elif choice == 6:
            break
        else:
            print("无效的选择。")

