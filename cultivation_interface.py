class CultivationInterface:
    def __init__(self, cultivation_system):
        self.cultivation_system = cultivation_system

    def show_cultivation_interface(self):
        while True:
            print("\n=== 修为系统菜单 ===")
            print("1. 分配修为点数")
            print("2. 选择心法线")
            print("3. 检查心法解锁")
            print("4. 展示当前心法技能信息")
            print("5. 重置修为和心法")
            print("6. 退出菜单")

            choice = input("请选择操作: ")

            if choice == "1":
                self.allocate_points_menu()
            elif choice == "2":
                self.choose_xinfa_line_menu()
            elif choice == "3":
                self.cultivation_system.check_xinfa_unlock()
            elif choice == "4":
                self.display_xinfa_skills()
            elif choice == "5":
                self.cultivation_system.reset()
            elif choice == "6":
                print("退出修为系统。")
                break
            else:
                print("无效的选择，请重新输入。")

    def allocate_points_menu(self):
        elements = ["金", "木", "水", "火", "土"]  # 元素列表
        while True:
            print("\n=== 分配修为点数 ===")
            print(f"当前剩余培养点: {self.cultivation_system.unused_points}")
            print(f"玩家修为点: {self.cultivation_system.player.cultivation_point}")
            print("1. 金")
            print("2. 木")
            print("3. 水")
            print("4. 火")
            print("5. 土")
            print("6. 返回主菜单")

            choice = input("请选择要提升修为的元素(输入数字): ")

            if choice in ["1", "2", "3", "4", "5"]:
                element = elements[int(choice) - 1]  # 根据选择数字获取对应的元素
                self.display_element_attributes(element)
                self.cultivation_system.upgrade(element)
            elif choice == "6":
                break
            else:
                print("无效的选择，请重新输入。")

    def choose_xinfa_line_menu(self):
        while True:
            print("\n=== 选择心法路线 ===")
            print("1. 第一条心法线")
            print("2. 第二条心法线")
            print("3. 第三条心法线")
            print("0. 返回主菜单")

            choice = input("请选择心法路线: ")

            if choice == "1":
                self.cultivation_system.select_xinfa_line(1)
                self.display_xinfa_skills()
                break
            elif choice == "2":
                self.cultivation_system.select_xinfa_line(2)
                self.display_xinfa_skills()
                break
            elif choice == "3":
                self.cultivation_system.select_xinfa_line(3)
                self.display_xinfa_skills()
            elif choice == "0":
                break
            else:
                print("无效的选择，请重新输入。")

    def display_element_attributes(self, element):
        data = self.cultivation_system.cultivation_data[element]
        current_level = data["level"]

        print(f"\n=== {element} 修为属性 ===")
        print(f"当前等级: {current_level}")

        # 检查当前等级是否为 0
        if current_level == 0:
            print("当前没有任何属性加成，请提升修为等级以获得加成。")
        else:
            print("当前属性加成:")
            current_attributes = data.get('attributes_per_level', {}).get(current_level, {})
            for attribute, value in current_attributes.items():
                translated_attribute = ATTRIBUTE_TRANSLATION.get(attribute, attribute)
                print(f"{translated_attribute}: {value}")

        # 提示下一等级的属性加成
        if current_level < self.cultivation_system.max_level:
            next_level = current_level + 1
            print(f"下一等级: {next_level}")
            print("下一等级属性加成:")
            next_attributes = data.get('attributes_per_level', {}).get(next_level, {})
            for attribute, value in next_attributes.items():
                translated_attribute = ATTRIBUTE_TRANSLATION.get(attribute, attribute)
                print(f"{translated_attribute}: {value}")
        else:
            print(f"{element} 修为已达到最高等级。")

    def display_xinfa_skills(self):
        if not self.cultivation_system.current_xinfa_line:
            print("尚未选择心法线。")
            return

        print("\n=== 当前心法线技能 ===")
        for level, skill in self.cultivation_system.current_xinfa_line.items():
            skill_status = "已解锁" if level <= self.cultivation_system.current_xinfa_level else "未解锁"
            print(f"心法等级 {level}: {skill.name} ({skill_status})")
            print(f"描述: {skill.description}")
            print("-" * 40)


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