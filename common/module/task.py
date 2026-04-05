import random
import copy


class Task:
    def __init__(self, number, name, description, quality, repeatable, acceptance_conditions, completion_conditions,
                 rewards, prerequisite_tasks=None, acceptance_logic=None, completion_logic=None, source_npc=None):
        self.number = number
        self.name = name
        self.description = description
        self.quality = quality
        self.repeatable = repeatable  # 标识任务是否可重复接取
        self.acceptance_conditions = acceptance_conditions
        self.completion_conditions = completion_conditions  # 任务完成条件，支持布尔逻辑
        self.rewards = rewards
        self.prerequisite_tasks = prerequisite_tasks or []
        self.acceptance_logic = acceptance_logic
        self.completion_logic = completion_logic
        self.kill_counts = {}  # 用于追踪特定敌人的击杀数目
        self.is_completed = False  # 标记任务是否已完成
        self.source_npc = source_npc  # 任务来源的 NPC

    def evaluate_logic(self, logic, player):
        """递归解析布尔逻辑"""
        if isinstance(logic, dict):
            if "AND" in logic:
                return all(self.evaluate_logic(sub, player) for sub in logic["AND"])
            elif "OR" in logic:
                return any(self.evaluate_logic(sub, player) for sub in logic["OR"])
            elif "NOT" in logic:
                return not self.evaluate_logic(logic["NOT"], player)
            elif "task_completed" in logic:
                return logic["task_completed"] in player.completed_tasks
            elif "task_not_completed" in logic:
                return logic["task_not_completed"] not in player.completed_tasks
        else:
            return bool(logic)

    def check_completion(self, player):
        """递归检查任务完成条件，包括布尔逻辑"""
        if self.completion_logic:
            return self.evaluate_logic(self.completion_logic, player)

        return self.evaluate_conditions(self.completion_conditions, player)

    def evaluate_conditions(self, conditions, player):
        """处理条件列表和布尔代数逻辑"""
        if isinstance(conditions, dict):
            if "AND" in conditions:
                return all(self.evaluate_conditions(sub, player) for sub in conditions["AND"])
            elif "OR" in conditions:
                return any(self.evaluate_conditions(sub, player) for sub in conditions["OR"])
            elif "NOT" in conditions:
                return not self.evaluate_conditions(conditions["NOT"], player)
        else:
            return all(self.evaluate_single_condition(cond, player) for cond in conditions)

    def evaluate_single_condition(self, condition, player):
        """检查单个条件是否满足"""
        # 检查玩家等级
        if "level" in condition:
            required_level = condition["level"]
            operator = condition.get("operator", "=")  # 默认为等于判断

            if operator == "=":
                return player.level == required_level
            elif operator == ">":
                return player.level > required_level
            elif operator == "<":
                return player.level < required_level
            else:
                raise ValueError(f"未知的比较运算符 '{operator}'")

        # 检查其他条件
        if "kill" in condition:
            kill_condition = condition["kill"]
            current_count = self.kill_counts.get(kill_condition["enemy_id"], 0)
            required_count = kill_condition["count"]
            return current_count >= required_count

        if "talk_to_npc" in condition:
            npc_id = condition["talk_to_npc"]
            return player.has_talked_to_npc(npc_id)

        if "item" in condition:
            item_number = condition["item"]
            quantity = condition.get("quantity", 1)
            return player.get_inventory_count(item_number) >= quantity

        if "give_item_to_npc" in condition:
            npc_id = condition["give_item_to_npc"]["npc_id"]
            item_number = condition["give_item_to_npc"]["item_number"]
            quantity = condition["give_item_to_npc"]["quantity"]
            return player.get_item_given_to_npc(npc_id, item_number) >= quantity

        return False

    def can_accept(self, player):
        # 检查任务是否已接取过
        if not self.repeatable:
            if self.number in [task.number for task in player.accepted_tasks] or \
               self.number in player.completed_tasks:
                print(f"任务 '{self.name}' 已接取过且不可重复接取。")
                return False

        # 检查前置任务条件
        for task_number in self.prerequisite_tasks:
            if task_number not in player.completed_tasks:
                print(f"任务 '{self.name}' 的前置任务 {task_number} 尚未完成。")
                return False

        # 检查接取逻辑表达式
        if self.acceptance_logic:
            return self.evaluate_logic(self.acceptance_logic, player)

        # 检查接取条件（支持布尔逻辑）
        return self.evaluate_conditions(self.acceptance_conditions, player)

    def accept(self, player):
        if self.can_accept(player):
            player.accepted_tasks.append(self)
            print(f"任务 '{self.name}' 已接受。")
        else:
            print(f"任务 '{self.name}' 无法接受。")

    def complete(self, player):
        from library.npc_library import npc_library
        if self.check_completion(player):
            self.is_completed = True
            player.accepted_tasks.remove(self)  # 从已接受任务中移除
            player.ready_to_complete_tasks.append(self)  # 将任务放入可交付列表
            print(f"任务 '{self.name}' 已完成！")

            if self.source_npc is None:
                self.give_rewards(player)
            else:
                npc_name = npc_library[self.source_npc].name \
                    if self.source_npc in npc_library else f"NPC 编号 {self.source_npc}"
                print(f"请返回到任务的来源 NPC ({npc_name}) 处领取奖励。")
        else:
            print(f"任务 '{self.name}' 尚未完成。")

    def give_rewards(self, player):
        for reward in self.rewards:
            if reward["type"] == "item":
                if random.random() <= reward.get("chance", 1.0):
                    # 创建一个新的物品实例，避免传递相同的物品实例
                    reward_item = copy.deepcopy(reward["item"])
                    reward_item.quantity = reward["quantity"]
                    player.add_to_inventory(reward_item)
                    print(f"玩家获得了 {reward_item.name} x {reward_item.quantity}")
                    return f"玩家获得了 {reward_item.name} x {reward_item.quantity}"
            elif reward["type"] == "exp":
                if random.random() <= reward.get("chance", 1.0):
                    player.gain_exp(reward["amount"])
                    print(f"玩家获得了 {reward['amount']} 点经验值。")
                    return f"玩家获得了 {reward['amount']} 点经验值。"
            elif reward["type"] == "attribute":
                if random.random() <= reward.get("chance", 1.0):
                    attr = reward["attribute"]
                    value = reward["value"]
                    player.gain_task_attribute(attr, value)

    def register_kill(self, enemy_id):
        if enemy_id not in self.kill_counts:
            self.kill_counts[enemy_id] = 0
        self.kill_counts[enemy_id] += 1
        print(f"任务 '{self.name}' 更新: 已击败 {enemy_id} 数量: {self.kill_counts[enemy_id]}")