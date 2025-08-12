from common.module.item import Skill, Equipment, Medicine, Material, Product


class BagInterface:
    def __init__(self, player):
        self.player = player

    def show_bag_interface(self):
        while True:
            print("\n====== 玩家背包界面 ======")
            print("1. 查看装备栏")
            print("2. 查看技能栏")
            print("3. 查看背包栏")
            print("4. 装备/卸下装备")
            print("5. 装备/卸下技能")
            print("6. 返回游戏主界面")
            choice = input("请选择操作: ")

            if choice == '1':
                self.display_equipment()
            elif choice == '2':
                self.display_skills()
            elif choice == '3':
                self.display_inventory()
            elif choice == '4':
                self.manage_equipment()
            elif choice == '5':
                self.manage_skills()
            elif choice == '6':
                break
            else:
                print("无效的选择，请重试。")

    def display_equipment(self):
        """显示当前装备栏中的物品"""
        print("\n====== 玩家装备栏 ======")
        if self.player.equipment:
            for i, item in enumerate(self.player.equipment, 1):
                print(f"{i}. {item.name} - {item.description}")
        else:
            print("装备栏为空。")

    def display_skills(self):
        """显示当前技能栏中的技能"""
        print("\n====== 玩家技能栏 ======")
        if self.player.skills:
            for i, skill in enumerate(self.player.skills, 1):
                print(f"{i}. {skill.name} - {skill.description}")
        else:
            print("技能栏为空。")

    def display_inventory(self):
        """显示背包中的物品（但不能使用）"""
        print("\n====== 玩家背包 ======")
        if self.player.inventory:
            for i, item in enumerate(self.player.inventory, 1):
                print(f"{i}. {item.name} (ID: {item.number}, 数量: {item.quantity}) - {item.description}")
        else:
            print("背包为空。")

    def manage_equipment(self):
        """管理装备，玩家可以选择装备/卸下装备"""
        while True:
            print("\n====== 装备管理 ======")
            print("1. 装备物品")
            print("2. 卸下物品")
            print("3. 返回上一级")
            choice = input("请选择操作: ")

            if choice == '1':
                self.equip_item()
            elif choice == '2':
                self.unequip_item()
            elif choice == '3':
                break
            else:
                print("无效的选择，请重试。")

    def manage_skills(self):
        """管理技能，玩家可以选择装备/卸下技能"""
        while True:
            print("\n====== 技能管理 ======")
            print("1. 装备技能")
            print("2. 卸下技能")
            print("3. 返回上一级")
            choice = input("请选择操作: ")

            if choice == '1':
                self.equip_skill()
            elif choice == '2':
                self.unequip_skill()
            elif choice == '3':
                break
            else:
                print("无效的选择，请重试。")

    def equip_item(self):
        """从背包中选择装备物品"""
        equipment_items = [item for item in self.player.inventory if isinstance(item, Equipment)]
        if not equipment_items:
            print("背包中没有可装备的物品。")
            return

        print("\n选择要装备的物品:")
        for i, item in enumerate(equipment_items, 1):
            print(f"{i}. {item.name} - {item.description}")

        choice = input("请输入物品编号: ")
        if choice.isdigit() and 1 <= int(choice) <= len(equipment_items):
            item = equipment_items[int(choice) - 1]

            # 检查装备限制
            equipment_types = {"武器": 0, "防具": 0, "饰品": 0, "法宝": 0}
            for eq in self.player.equipment:
                if eq.category in equipment_types:
                    equipment_types[eq.category] += 1

            if item.category in ["武器", "防具", "饰品"]:
                if equipment_types[item.category] >= 1:
                    print(f"{item.category} 已经装备，无法再装备 {item.name}。")
                    return
            elif item.category == "法宝":
                if equipment_types["法宝"] >= 3:
                    print("法宝数量已达上限，无法再装备。")
                    return

            self.player.equipment.append(item)
            item.apply_attributes(self.player)
            self.player.inventory.remove(item)
            print(f"装备了 {item.name}。")
        else:
            print("无效的选择。")

    def unequip_item(self):
        """卸下装备并返回到背包"""
        if not self.player.equipment:
            print("你没有装备任何物品。")
            return

        print("\n选择要卸下的物品:")
        for i, item in enumerate(self.player.equipment, 1):
            print(f"{i}. {item.name} - {item.description}")

        choice = input("请输入物品编号: ")
        if choice.isdigit() and 1 <= int(choice) <= len(self.player.equipment):
            item = self.player.equipment[int(choice) - 1]
            item.remove_attributes(self.player)
            self.player.equipment.remove(item)
            self.player.inventory.append(item)
            print(f"卸下了 {item.name}。")
        else:
            print("无效的选择。")

    def equip_skill(self):
        """从背包中选择装备技能"""
        if len(self.player.skills) >= 9:
            print("技能栏已满，无法再装备新的技能。")
            return

        available_skills = [item for item in self.player.inventory if isinstance(item, Skill)]
        if not available_skills:
            print("背包中没有可装备的技能。")
            return

        print("\n选择要装备的技能:")
        for i, skill in enumerate(available_skills, 1):
            print(f"{i}. {skill.name} - {skill.description}")

        choice = input("请输入技能编号: ")
        if choice.isdigit() and 1 <= int(choice) <= len(available_skills):
            skill = available_skills[int(choice) - 1]
            self.player.skills.append(skill)
            self.player.inventory.remove(skill)
            print(f"装备了技能 {skill.name}。")
        else:
            print("无效的选择。")

    def unequip_skill(self):
        """卸下技能并返回到背包"""
        if not self.player.skills:
            print("你没有装备任何技能。")
            return

        print("\n选择要卸下的技能:")
        for i, skill in enumerate(self.player.skills, 1):
            print(f"{i}. {skill.name} - {skill.description}")

        choice = input("请输入技能编号: ")
        if choice.isdigit() and 1 <= int(choice) <= len(self.player.skills):
            skill = self.player.skills[int(choice) - 1]
            self.player.skills.remove(skill)
            self.player.inventory.append(skill)
            print(f"卸下了技能 {skill.name}。")
        else:
            print("无效的选择。")
