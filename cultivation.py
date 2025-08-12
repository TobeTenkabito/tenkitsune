class CultivationSystem:
    def __init__(self, player, skill_library):
        self.player = player
        self.skill_library = skill_library
        self.skill_ids_line1 = {
            1: skill_library[251001],
            2: skill_library[251002],
            3: skill_library[251003],
            4: skill_library[251004],
            5: skill_library[251005]
        }
        self.skill_ids_line2 = {
            1: skill_library[252001],
            2: skill_library[252002],
            3: skill_library[252003],
            4: skill_library[252004],
            5: skill_library[252005]
        }
        self.skill_ids_line3 = {
            1: skill_library[253001],
            2: skill_library[253002],
            3: skill_library[253003],
            4: skill_library[253004],
            5: skill_library[253005]
        }
        self.skill_ids_line4 = {
            1: skill_library[254001],
            2: skill_library[254002],
            3: skill_library[254003],
            4: skill_library[254004],
            5: skill_library[254005]
        }
        # 当前玩家选择的心法线（初始为空）
        self.current_xinfa_line = None
        self.current_xinfa_level = 0  # 当前心法等级
        self.xinfa_thresholds = [0, 20, 40, 60, 80]  # 心法等级解锁的阈值
        self.update_xinfa_from_inventory()  # 检查背包和技能栏
        # 每个修为类型的最大等级
        self.max_level = 5
        self.cultivation_data = {
            "金": {
                "level": 0,
                "attributes_per_level": {
                    1: {"cultivation_attack": 28, "cultivation_crit": 1},
                    2: {"cultivation_attack": 84, "cultivation_crit": 2},
                    3: {"cultivation_attack": 168, "cultivation_crit": 3},
                    4: {"cultivation_attack": 280, "cultivation_crit": 4},
                    5: {"cultivation_attack": 420, "cultivation_crit": 5}
                }
            },
            "木": {
                "level": 0,
                "attributes_per_level": {
                    1: {"cultivation_speed": 8, "cultivation_penetration": 1},
                    2: {"cultivation_speed": 24, "cultivation_penetration": 2},
                    3: {"cultivation_speed": 48, "cultivation_penetration": 3},
                    4: {"cultivation_speed": 80, "cultivation_penetration": 4},
                    5: {"cultivation_speed": 120, "cultivation_penetration": 5}
                }
            },
            "水": {
                "level": 0,
                "attributes_per_level": {
                    1: {"cultivation_mp": 32, "cultivation_crit_damage": 1},
                    2: {"cultivation_mp": 96, "cultivation_crit_damage": 2},
                    3: {"cultivation_mp": 192, "cultivation_crit_damage": 3},
                    4: {"cultivation_mp": 320, "cultivation_crit_damage": 4},
                    5: {"cultivation_mp": 480, "cultivation_crit_damage": 5}
                }
            },
            "火": {
                "level": 0,
                "attributes_per_level": {
                    1: {"cultivation_hp": 64, "cultivation_crit_damage": 1},
                    2: {"cultivation_hp": 192, "cultivation_crit_damage": 2},
                    3: {"cultivation_hp": 384, "cultivation_crit_damage": 3},
                    4: {"cultivation_hp": 640, "cultivation_crit_damage": 4},
                    5: {"cultivation_hp": 960, "cultivation_crit_damage": 5}
                }
            },
            "土": {
                "level": 0,
                "attributes_per_level": {
                    1: {"cultivation_defense": 20, "cultivation_resistance": 1},
                    2: {"cultivation_defense": 60, "cultivation_resistance": 2},
                    3: {"cultivation_defense": 120, "cultivation_resistance": 3},
                    4: {"cultivation_defense": 200, "cultivation_resistance": 4},
                    5: {"cultivation_defense": 300, "cultivation_resistance": 5}
                }
            }
        }
        # 计数器：记录已使用和未使用的培养点
        self.used_points = 0
        self.unused_points = player.cultivation_point

    def restore_from_save(self, cultivation_data):
        # 检查传入数据是否包含预期的键
        if "cultivation_data" not in cultivation_data:
            print("警告：没有找到 'cultivation_data' 键。")
            return

        # 打印当前的修为数据
        print("当前修为数据:", self.cultivation_data)

        # 遍历并恢复五行修为数据
        for element, data in cultivation_data["cultivation_data"].items():
            print(f"正在处理元素: {element}")  # 添加打印语句
            if element in self.cultivation_data:
                self.cultivation_data[element]['level'] = data.get('level', 0)

                # 确保 attributes_per_level 的键是整数
                self.cultivation_data[element]['attributes_per_level'] = {
                    int(level): attributes
                    for level, attributes in data.get('attributes_per_level', {}).items()
                }

        # 恢复使用点和未使用点
        self.used_points = cultivation_data.get('used_points', 0)
        self.unused_points = cultivation_data.get('unused_points', self.player.cultivation_point)

    def upgrade(self, element):
        print(f"升级请求的元素: {element}")
        print(f"当前修为数据: {self.cultivation_data}")
        if element not in self.cultivation_data:
            print("无效的修为元素选择。")
            return

        current_level = self.cultivation_data[element]["level"]
        if current_level >= self.max_level:
            print(f"{element} 修为已达到最高等级。")
            return

        cost = current_level + 2  # 提升到下一级所需的点数
        if self.unused_points < cost:
            print(f"培养点不足，无法提升 {element} 修为。需要 {cost} 点，当前剩余 {self.unused_points} 点。")
            return

        # 提升等级
        new_level = current_level + 1

        # 打印当前修为系统的所有等级加成效果
        print(f"{element} 修为当前等级及加成:")
        for level in range(1, self.max_level + 1):
            attribute_increases = self.cultivation_data[element].get("attributes_per_level", {}).get(level, {})
            print(f"等级 {level}: {attribute_increases}")

        attribute_increases = self.cultivation_data[element].get("attributes_per_level", {}).get(new_level)
        if not attribute_increases:
            print(f"{element} 修为的第 {new_level} 级没有定义属性加成。")
            return

        # 提升修为等级
        self.cultivation_data[element]["level"] = new_level
        self.used_points += cost
        self.unused_points -= cost

        # 同步修为点到 Player
        self.player.cultivation_point = self.unused_points
        print(f"玩家修为点同步为: {self.player.cultivation_point}")

        # 应用属性加成
        for attribute, increase in attribute_increases.items():
            setattr(self.player, attribute, getattr(self.player, attribute) + increase)

        self.player.update_stats()
        print(f"{element} 修为提升至 {new_level} 级，消耗了 {cost} 个培养点。")
        return f"{element} 修为提升至 {new_level} 级，消耗了 {cost} 个培养点。"

    def reset(self):
        print(f"重置修为数据，当前修为数据: {self.cultivation_data}")
        # 重置每个元素的修为
        for element, data in self.cultivation_data.items():
            level = data["level"]
            if level > 0:
                attribute_decreases = data["attributes_per_level"][level]
                for attribute, decrease in attribute_decreases.items():
                    setattr(self.player, attribute, getattr(self.player, attribute) - decrease)

                # 重置修为等级
                self.cultivation_data[element]["level"] = 0

        # 重置计数器
        self.unused_points += self.used_points
        self.used_points = 0
        # 更新玩家属性
        self.player.update_stats()

        # 重置心法
        self.reset_xinfa()
        print("修为已重置，所有培养点已返还，并重置心法。")

    # 心法类
    def update_xinfa_from_inventory(self):
        # 遍历所有心法线
        for xinfa_line in [self.skill_ids_line1, self.skill_ids_line2, self.skill_ids_line3, self.skill_ids_line4]:
            for level, skill in xinfa_line.items():
                if self.player.has_skill(skill.number):
                    self.current_xinfa_line = xinfa_line
                    self.current_xinfa_level = max(self.current_xinfa_level, level)

        print(f"初始化时检测到的心法等级: {self.current_xinfa_level}")

    def select_xinfa_line(self, line):
        if line == 1:
            self.current_xinfa_line = self.skill_ids_line1
            print("已选择第一条心法线")
        elif line == 2:
            self.current_xinfa_line = self.skill_ids_line2
            print("已选择第二条心法线")
        elif line == 3:
            self.current_xinfa_line = self.skill_ids_line3
            print("已选择第三条心法线")
        elif line == 4:
            self.current_xinfa_line = self.skill_ids_line4
            print("已选择第四条心法线")
        else:
            print("无效的心法线选择。")

    def check_xinfa_unlock(self):
        if not self.current_xinfa_line:
            print("请先选择心法线。")
            return

        # 检查是否已经拥有该线的 Level1 技能
        if not self.has_xinfa_level1_skill():
            print("你尚未拥有该心法线的一级技能，无法解锁下一等级。")
            return
        else:
            # 更新心法等级到 1（如果第一级已经解锁）
            if self.current_xinfa_level == 0:
                self.current_xinfa_level = 1
                print("已成功更新心法等级至 1")

        # 遍历当前心法线，逐级检查能否解锁
        for i in range(self.current_xinfa_level + 1, len(self.xinfa_thresholds)):
            if self.used_points >= self.xinfa_thresholds[i]:
                # 仅从 Level 2 开始检查互斥条件，Level 1 不受限制
                if i >= 1 and self.is_level_unlocked_in_other_lines(i):
                    print(f"已在其他心法线激活了 Level {i + 1}，无法在此线激活。")
                    break
                # 解锁该心法线的技能
                self.unlock_xinfa(i + 1)
            else:
                break

    def has_xinfa_level1_skill(self):
        if self.current_xinfa_line:
            level1_skill = self.current_xinfa_line.get(1)
            if self.player.has_skill(level1_skill.number):
                print(f"已拥有第一级技能: {level1_skill.name}")
                return True
            else:
                print(f"未找到第一级技能: {level1_skill.name}")
        return False

    def is_level_unlocked_in_other_lines(self, level):
        # 把所有心法线存入一个列表
        all_xinfa_lines = [self.skill_ids_line1, self.skill_ids_line2, self.skill_ids_line3]

        # 遍历所有心法线，检查除了当前选定的心法线之外，是否有其他心法线解锁了指定等级
        for xinfa_line in all_xinfa_lines:
            if xinfa_line != self.current_xinfa_line:  # 忽略当前心法线
                skill_in_other_line = xinfa_line.get(level)
                if skill_in_other_line and self.player.has_skill(skill_in_other_line.number):
                    return True  # 如果其他心法线已经解锁了该等级的技能，返回True

        return False  # 如果没有其他心法线解锁该等级的技能，返回False

    def unlock_xinfa(self, level):
        skill = self.current_xinfa_line.get(level)
        if skill:
            print(f"正在解锁心法等级 {level}，技能: {skill.name}")
            self.player.add_to_inventory(skill)
            print(f"已添加技能 {skill.name} 到背包")
            self.current_xinfa_level = level  # 更新心法等级
            print(f"心法等级已更新到 {level}")
        else:
            print(f"心法等级 {level} 对应的技能不存在。")

    def reset_xinfa(self):
        for level in range(2, self.current_xinfa_level + 1):  # 从第二级开始
            skill = self.current_xinfa_line.get(level)
            if skill:
                print(f"移除心法等级 {level} 对应的技能 {skill.name}。")
                # 移除背包中的技能，指定数量为 1
                removed = self.player.remove_from_inventory(skill.number, 1)
                if removed:
                    print(f"已成功移除技能 {skill.name}。")
                else:
                    print(f"未能移除技能 {skill.name}，可能不在背包中。")
                # 检查并移除技能栏中的技能
                self.player.remove_skill(skill.number)

        # 重置心法等级，保留第一级心法
        self.current_xinfa_level = 1  # 保留第一级
