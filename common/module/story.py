from library.material_library import material_library
from library.enemy_library import enemy_library
from library.storybuff_library import storybuff_library
from library.storyfight_library import storyfight_library
from library.ally_library import ally_library
from .battle import Battle
import time
import json
import copy


class Action:
    def execute(self):
        pass

    def execute_with_battle(self, dynamic_battle):
        # 默认行为只是调用 execute 方法
        self.execute()


class Choice:
    def __init__(self, description, next_node, next_node_id):
        self.description = description
        self.next_node = next_node
        self.next_node_id = next_node_id

    def execute(self):
        return self.next_node and self.next_node_id


class AddItemAction(Action):
    def __init__(self, player, item, quantity):
        self.player = player
        self.item = item
        self.quantity = quantity
        self.type = 'add'

    def execute(self):
        # 深拷贝以避免影响原始 item 模板
        new_item = copy.deepcopy(self.item)
        new_item.quantity = self.quantity
        self.player.add_to_inventory(new_item)
        print(f"{self.player.name} 获得了 {new_item.name} x{new_item.quantity}")


class AddBuffAction(Action):
    def __init__(self, player, buff_name):
        self.player = player
        self.buff_name = buff_name
        self.type = 'add'

    def execute(self):
        # 如果没有传入 battle 参数，默认行为
        pass

    def execute_with_battle(self, dynamic_battle):
        if self.buff_name in storybuff_library:
            buff = storybuff_library[self.buff_name]
            buff.user = self.player
            buff.target = self.player
            self.player.add_buff(buff)
            print(f"{self.player.name} 获得了 {buff.name} buff")


class ModifyBattleEnemiesAction(Action):
    def __init__(self, add_enemies=None, remove_enemies=None):
        self.add_enemies = add_enemies or []
        self.remove_enemies = remove_enemies or []
        self.type = 'modify'

    def execute(self):
        pass

    def execute_with_battle(self, dynamic_battle):
        for enemy in self.add_enemies:
            dynamic_battle.enemies.append(enemy)
            print(f"敌人 {enemy.name} 被加入战斗。")

        for enemy in self.remove_enemies:
            if enemy in dynamic_battle.enemies:
                dynamic_battle.enemies.remove(enemy)
                print(f"敌人 {enemy.name} 被移出战斗。")


class ModifyBattleAlliesAction(Action):
    def __init__(self, add_allies=None, remove_allies=None):
        self.add_allies = add_allies or []
        self.remove_allies = remove_allies or []
        self.type = 'modify'

    def execute(self):
        pass

    def execute_with_battle(self, dynamic_battle):
        for ally in self.add_allies:
            dynamic_battle.allies.append(ally)
            print(f"队友 {ally.name} 被加入战斗。")

        for ally in self.remove_allies:
            if ally in dynamic_battle.allies:
                dynamic_battle.allies.remove(ally)
                print(f"队友 {ally.name} 被移出战斗。")


class ChapterEndAction:
    def __init__(self, chapter, player):
        self.chapter = chapter
        self.player = player
        self.type = "end"

    def execute(self):
        """执行章节结束操作，标记章节为完成，并更新玩家的故事进度"""
        print(f"章节 {self.chapter.number} 已完成")

        # 标记章节为已完成
        self.chapter.is_completed = True

        # 更新 player.story_progress 中的 chapters_completed
        if "chapters_completed" not in self.player.story_progress:
            self.player.story_progress["chapters_completed"] = {}

        self.player.story_progress["chapters_completed"][str(self.chapter.number)] = True

        print(f"玩家进度已更新: {self.player.story_progress['chapters_completed']}")


class StartBattleAction(Action):
    def __init__(self, player, battle_id):
        self.player = player
        self.battle_id = battle_id
        self.type = "start_battle"

    def execute_with_battle(self, dynamic_battle, story_instance=None):
        from library.storyfight_library import storyfight_library
        if self.battle_id in storyfight_library:
            new_battle = storyfight_library[self.battle_id]
            if story_instance:
                story_instance.dynamic_battle = new_battle  # 替换为指定的战斗
            print(f"触发战斗：{self.battle_id}")
            new_battle.player = self.player
            new_battle.run_battle()
        else:
            print(f"[错误] 无法找到战斗 ID: {self.battle_id}")


class Chapter:
    def __init__(self, number, title, start_node, end_node):
        self.number = number
        self.title = title
        self.start_node = start_node
        self.end_node = end_node
        self.is_completed = False
        self.nodes = {}

    def mark_completed(self):
        self.is_completed = True
        print(f"章节 {self.number} 已完成。")

    def add_node(self, node_id, node):
        self.nodes[node_id] = node
        print(f"节点 {node_id} 已添加到章节 {self.number}")

    def get_node(self, node_id):
        node = self.nodes.get(node_id, None)
        if node:
            print(f"成功获取节点 {node_id} 在章节 {self.number}")
        else:
            print(f"节点 {node_id} 在章节 {self.number} 中未找到")
        return node


class StoryNode:
    def __init__(self, description, choices=None, actions=None, chapter_number=None, node_id=None):
        self.description = description
        self.choices = choices or []
        self.actions = actions or []
        self.battle = None  # 初始化为空的战斗属性
        self.is_completed = False
        self.chapter_number = chapter_number  # 章节编号
        self.node_id = node_id  # 节点编号
        self.next_node = None
        self.next_node_id = None

    def add_choice(self, choice):
        self.choices.append(choice)

    def set_battle(self, battle_id, dynamic_battle):
        if battle_id in storyfight_library:
            predefined_battle = storyfight_library[battle_id]

            # 合并全局动态战斗与静态战斗
            self.battle = Battle(
                player=predefined_battle.player,
                allies=dynamic_battle.allies + predefined_battle.allies,
                enemies=dynamic_battle.enemies + predefined_battle.enemies
            )

    def add_action(self, action):
        self.actions.append(action)

    def execute_actions(self, dynamic_battle):
        for action in self.actions:
            action.execute_with_battle(dynamic_battle)

    def trigger_battle(self, player):
        if self.battle:
            self.battle.player = player  # 从 Story 类传递的 player
            self.battle.player.battle = self.battle
            battle_status = self.battle.run_battle()
            if battle_status == "win":
                print("战斗胜利！继续剧情...")
                return False  # 返回 False 表示继续故事
            elif battle_status == "loss":
                print("战斗失败！")
                return True  # 返回 True 表示结束故事
        return False

    def mark_completed(self):
        """标记节点已完成"""
        self.is_completed = True
        print(f"节点 {self.node_id} 已完成")


class Story:
    def __init__(self, start_node, player, save_callback, story_manager, dynamic_battle=None):
        self.current_node = start_node
        self.player = player
        self.dynamic_battle = dynamic_battle or Battle(player=None, allies=[], enemies=[])  # 全局动态战斗
        self.is_auto_play = False  # 自动播放
        self.completed = False
        self.save_callback = save_callback  # 回调函数
        self.story_manager = story_manager

    def toggle_auto_play(self):
        self.is_auto_play = not self.is_auto_play

    def run(self):
        while self.current_node:
            print(f"当前节点: {self.current_node.node_id}, 章节编号: {self.current_node.chapter_number}")
            print(
                f"当前节点 {self.current_node.node_id} 的 next_node_id 是: {getattr(self.current_node, 'next_node_id', '未设置')}")
            # 处理描述（兼容列表或字符串）
            description = self.current_node.description
            if isinstance(description, list):
                text_slices = description
            else:
                text_slices = split_text(description)

            # 显示文本
            for text_slice in text_slices:
                print(text_slice)

                if self.is_auto_play:
                    time.sleep(3)
                else:
                    next_action = input("按 Enter 显示下一句，输入 'auto' 进行自动播放: ").strip().lower()
                    if next_action == 'auto':
                        self.toggle_auto_play()
                        time.sleep(3)

            # 保存当前节点
            save_option = input("是否保存当前节点? (y/n): ").strip().lower()
            if save_option == 'y':
                self.save_progress()

            # 执行动作
            if self.current_node.actions:
                for action in self.current_node.actions:
                    if hasattr(action, "execute_with_battle"):
                        action.execute_with_battle(dynamic_battle=self.dynamic_battle)
                    else:
                        action.execute()

            if self.current_node.choices:
                for i, choice in enumerate(self.current_node.choices):
                    print(f"{i + 1}. {choice.description}")
                choice_number = int(input("请输入选择编号: "))
                selected_choice = self.current_node.choices[choice_number - 1]

                next_node = self.find_node_by_id(selected_choice.next_node_id)
                if next_node:
                    # 如果章节切换了
                    if next_node.chapter_number != self.current_node.chapter_number:
                        print(
                            f"[章节切换] 从第 {self.current_node.chapter_number} 章切换到第 {next_node.chapter_number} 章")
                        self.story_manager.mark_chapter_completed(self.current_node.chapter_number)
                        self.story_manager.set_current_chapter(next_node.chapter_number)

                    self.current_node = next_node
                    print(
                        f"切换到下一个节点: {self.current_node.node_id}, 章节编号: {self.current_node.chapter_number}")
                else:
                    print("错误：找不到对应的下一个节点。")
                    break
            else:
                # 没有 choices，尝试按 next_node_id 跳转
                next_node_id = getattr(self.current_node, "next_node_id", None)
                if next_node_id is not None:
                    next_node = self.find_node_by_id(next_node_id)
                    if next_node:
                        self.current_node = next_node
                        print(f"自动跳转到节点: {self.current_node.node_id}, 章节编号: {self.current_node.chapter_number}")
                    else:
                        print("错误：找不到对应的下一个节点。")
                        break
                else:
                    print("故事结束")
                    self.completed = True
                    self.story_manager.mark_chapter_completed(self.current_node.chapter_number)
                    self.save_progress()
                    break

    def get_node_by_id(self, node_id):
        for chapter in self.story_manager.chapters:
            for node in chapter.nodes.values():
                if node.node_id == node_id:
                    return node
        return None

    def find_node_by_id(self, node_id):
        # 优先从当前章节查找
        current_chapter = self.story_manager.current_chapter
        node = current_chapter.get_node(node_id)
        if node:
            return node

        # 否则全局查找
        for chapter in self.story_manager.chapters:
            if chapter == current_chapter:
                continue
            node = chapter.get_node(node_id)
            if node:
                print(f"[章节切换] 从第 {current_chapter.number} 章切换到第 {chapter.number} 章")
                self.story_manager.mark_chapter_completed(current_chapter.number)
                self.story_manager.set_current_chapter(chapter.number)
                return node
        return None

    def is_completed(self):
        """检查故事是否完成"""
        return self.completed

    def save_progress(self):
        # 存储玩家当前章节和节点
        if self.current_node and self.current_node.chapter_number is not None and self.current_node.node_id is not None:
            print(f"保存当前章节: {self.current_node.chapter_number}, 当前节点: {self.current_node.node_id}")
            self.player.story_progress["current_chapter"] = self.current_node.chapter_number
            self.player.story_progress["current_node"] = self.current_node.node_id

            # 保存章节完成状态
            completed_status = []
            for chapter in self.story_manager.chapters:
                completed_status.append(chapter.is_completed)
                self.player.story_progress["chapters_completed"][str(chapter.number)] = chapter.is_completed

            print(f"保存章节完成状态: {completed_status}")
            self.save_callback()
            print("故事进度已保存。")
        else:
            print("错误: 无法保存进度，节点信息不完整。")


class StoryManager:
    def __init__(self, player, chapters):
        self.player = player
        self.chapters = chapters  # 所有章节的列表
        self.current_chapter = None  # 当前章节
        self.story = None

    # 故事读档
    def continue_from_saved_node(self, save_callback=None):
        chapter_number = self.player.story_progress["current_chapter"]
        node_id = self.player.story_progress["current_node"]
        # 获取已保存的章节和节点
        self.current_chapter = self.chapters[chapter_number - 1]
        saved_node = self.current_chapter.get_node(node_id)

        # 传递 StoryManager 实例
        story = Story(saved_node, self.player, save_callback=save_callback, story_manager=self,
                      dynamic_battle=Battle(player=self.player, allies=[], enemies=[]))
        story.run()

        # 检查故事是否完成，标记章节完成
        if story.is_completed():
            self.current_chapter.mark_completed()

        # 保存故事进度
        if save_callback:
            save_callback()

    # 故事存档
    def start_chapter_from_beginning(self, save_callback=None):
        """从章节的起始节点开始"""
        if self.current_chapter is None:
            print("尚未选择章节，请先选择章节。")
            self.select_chapter()

        if self.current_chapter:
            # 传入章节的起始节点并传递 StoryManager 实例
            story = Story(self.current_chapter.start_node, self.player, save_callback=save_callback, story_manager=self,
                          dynamic_battle=Battle(player=self.player, allies=[], enemies=[]))
            story.run()

            # 检查故事是否完成
            if story.is_completed():
                print(f"章节 {self.current_chapter.title} 已完成！")
                self.current_chapter.mark_completed()

            # 保存故事进度
            if save_callback:
                save_callback()

    # 选择章节
    def select_chapter(self):
        """玩家选择章节"""
        print("请选择章节:")
        for chapter in self.chapters:
            status = "已完成" if chapter.is_completed else "未完成"
            print(f"章节 {chapter.number}: {chapter.title} ({status}) - 状态: {chapter.is_completed}")

        chapter_number = int(input("请选择章节编号: "))
        selected_chapter = next((c for c in self.chapters if c.number == chapter_number), None)

        if selected_chapter:
            # 第一章默认解锁，后续章节依赖于完成状态解锁
            if selected_chapter.number == 1 or self.chapters[selected_chapter.number - 2].is_completed:
                self.current_chapter = selected_chapter
                return selected_chapter
            else:
                print("该章节尚未解锁。")
        else:
            print("尚未选择章节，请先选择章节。")
        return None

    def get_current_chapter(self):
        """根据玩家 story_progress 获取当前章节"""
        current_chapter_number = self.player.story_progress["current_chapter"]
        # 从 StoryManager 中的 chapters 列表获取对应的章节
        for chapter in self.chapters:
            if chapter.number == current_chapter_number:
                return chapter
        return None

    def mark_chapter_completed(self, chapter_number):
        """标记章节完成并更新玩家的进度"""
        self.player.story_progress["chapters_completed"][str(chapter_number)] = True
        print(f"章节 {chapter_number} 已完成并更新到玩家进度: {self.player.story_progress['chapters_completed']}")

    def mark_node_completed(self, chapter_number, node_id):
        """记录节点已完成"""
        # 确保 completed_nodes 键存在
        if "completed_nodes" not in self.player.story_progress:
            self.player.story_progress["completed_nodes"] = []  # 初始化为空列表

        # 生成章节号和节点号的元组
        completed_key = (chapter_number, node_id)

        # 记录节点完成状态
        if completed_key not in self.player.story_progress["completed_nodes"]:
            self.player.story_progress["completed_nodes"].append(completed_key)
            print(f"章节 {chapter_number} 的节点 {node_id} 已记录为完成")

    def save_progress(self):
        """保存玩家的故事进度"""
        if self.current_chapter:
            # 调用当前 Story 实例的 save_progress 来保存当前节点状态
            if hasattr(self, 'story'):  # 检查是否有 story 实例
                self.story.save_progress()  # 调用 story 的保存函数
            else:
                print("当前没有 Story 实例，无法保存节点进度。")
        else:
            print("当前没有章节正在进行，无法保存进度。")

    def set_current_chapter(self, chapter_number):
        """根据章节编号切换当前章节"""
        for chapter in self.chapters:
            if chapter.number == chapter_number:
                self.current_chapter = chapter
                print(f"已切换到章节 {chapter.number}: {chapter.title}")
                return
        print(f"[错误] 未找到章节编号 {chapter_number}，无法切换。")


# 新版解码器
def load_story_from_json(filename, player, dynamic_battle, chapter=None, story_manager=None):
    nodes = {}  # 存储所有节点
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)  # 读取JSON文件

    chapter_number = data.get('chapter_number')
    start_node = None
    last_node = None

    # 1. 首先加载所有节点
    for node_data in data['nodes']:
        node_id = node_data['node_id']
        description = node_data['description']

        # 创建节点时，传递 chapter_number 和 node_id
        node = StoryNode(description, chapter_number=chapter_number, node_id=node_id)

        # 添加节点到章节
        if chapter:
            chapter.add_node(node_id, node)

        # 把节点放入 nodes 字典
        nodes[node_id] = node

        # 记录第一个节点作为起始节点
        if start_node is None:
            start_node = node

        last_node = node  # 记录最后一个节点

    # 打印加载的所有节点
    print(f"所有加载的节点: {list(nodes.keys())}")

    # 2. 处理选择和动作
    for node_data in data['nodes']:
        node_id = node_data['node_id']

        # 处理选择
        if 'choices' in node_data:
            for choice_data in node_data['choices']:
                choice_description = choice_data['description']
                next_node_id = choice_data['next_node_id']

                # 确保 next_node_id 已经在 nodes 中
                if next_node_id not in nodes:
                    raise KeyError(f"节点 {next_node_id} 在选择中被引用，但没有找到对应的节点定义。")

                # 为当前节点添加选择
                nodes[node_id].add_choice(Choice(choice_description, nodes[next_node_id], next_node_id))

        # 处理动作
        if 'actions' in node_data:
            for action_data in node_data['actions']:
                action_type = action_data['type']

                # 添加物品
                if action_type == 'add_item':
                    item = material_library[action_data['item_id']]
                    nodes[node_id].add_action(AddItemAction(player, item, action_data['quantity']))

                # 增加敌人
                elif action_type == 'add_enemy':
                    enemy = enemy_library[action_data['enemy_id']]
                    nodes[node_id].add_action(ModifyBattleEnemiesAction(add_enemies=[enemy]))

                # 移除敌人
                elif action_type == 'remove_enemy':
                    enemy = enemy_library[action_data['enemy_id']]
                    nodes[node_id].add_action(ModifyBattleEnemiesAction(remove_enemies=[enemy]))

                # 增加队友
                elif action_type == 'add_ally':
                    ally = ally_library[action_data['ally_id']]
                    nodes[node_id].add_action(ModifyBattleAlliesAction(add_allies=[ally]))

                # 移除队友
                elif action_type == 'remove_ally':
                    ally = ally_library[action_data['ally_id']]
                    nodes[node_id].add_action(ModifyBattleAlliesAction(remove_allies=[ally]))

                # 添加 Buff
                elif action_type == 'add_buff':
                    buff_name = action_data['buff_name']
                    nodes[node_id].add_action(AddBuffAction(player, buff_name))

                # 进入战斗
                elif action_type == 'start_battle':
                    battle_id = action_data['battle_id']
                    nodes[node_id].set_battle(battle_id, dynamic_battle=dynamic_battle)
                    nodes[node_id].add_action(StartBattleAction(player, battle_id))

                # 章节结束
                elif action_type == 'end':
                    # 在节点动作执行时标记章节结束
                    nodes[node_id].add_action(ChapterEndAction(chapter, player))

        # 处理 next_node_id（为每个节点设置 next_node）
        next_node_id = node_data.get('next_node_id')  # 获取 next_node_id，如果没有则为 None
        if next_node_id:
            # 如果 next_node_id 存在并且在 nodes 中
            if next_node_id in nodes:
                nodes[node_id].next_node = nodes[next_node_id]
                nodes[node_id].next_node_id = next_node_id

        # else:
            # 如果没有定义 next_node_id，则尝试使用当前 node_id + 1 作为默认的下一个节点
            # default_next_node_id = node_id + 1
            # if default_next_node_id in nodes:
                # nodes[node_id].next_node = nodes[default_next_node_id]
                # nodes[node_id].next_node_id = default_next_node_id

    # 确保章节设置了开始节点和结束节点
    if chapter:
        chapter.start_node = start_node
        chapter.end_node = last_node

    # 返回 Story 实例，并传入 story_manager
    return Story(start_node, player, dynamic_battle=dynamic_battle, save_callback=None, story_manager=story_manager)


def split_text(description):
    if isinstance(description, list):
        print("description 是列表，逐行处理")
        text_slices = []
        for line in description:
            text_slices.extend(line.split('|'))
        return text_slices
    elif isinstance(description, str):
        print("description 是字符串，直接分割")
        return description.split('|')
    else:
        raise ValueError("description 既不是字符串也不是列表")
