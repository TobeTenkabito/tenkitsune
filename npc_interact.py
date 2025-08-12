# common/interact/npc_interact.py
import random
from all.gamestate import game_state


class NPC:
    def __init__(self, number, name, description, race, affection, favorite_items,
                 daily_dialogue, task_dialogue, finish_task_dialogue,
                 tasks=None, exchange=None, affection_dialogues=None, fight=None, taunt_dialogue=None, lottery=None):
        self.number = number
        self.name = name
        self.description = description
        self.race = race
        self.affection = affection
        self.favorite_items = favorite_items
        self.daily_dialogue = daily_dialogue if isinstance(daily_dialogue, list) else [daily_dialogue]
        self.task_dialogue = task_dialogue
        self.finish_task_dialogue = finish_task_dialogue
        self.fight = fight
        self.tasks = tasks or []
        self.exchange = exchange or {}
        self.lottery = lottery
        self.affection_dialogues = affection_dialogues or {
            "low": [], "medium": [], "high": []
        }
        self.taunt_dialogue = taunt_dialogue or {
            "low": [], "medium": [], "high": []
        }

    def get_daily_dialogue(self) -> str:
        """获取随机日常对话或好感度对话"""
        all_dialogues = self.daily_dialogue + self.get_affection_based_dialogue()
        return random.choice(all_dialogues) if all_dialogues else "没有什么好说的。"

    def get_task_dialogue_based_on_affection(self) -> str:
        """根据好感度返回任务对话"""
        if self.affection < -25:
            return "我没有什么要和你说的，滚开！"
        elif -25 <= self.affection <= 25:
            return self.task_dialogue
        elif 26 <= self.affection <= 75:
            return "嘿，有些任务你可能感兴趣。"
        else:
            return "你来了！有些特别的任务需要你来完成。"

    def get_available_tasks(self) -> list:
        """根据好感度返回可接取任务"""
        if self.affection < 25:
            return [task for task in self.tasks if task.quality == "普通"]
        elif 25 <= self.affection <= 75:
            return [task for task in self.tasks if task.quality in ["普通", "稀有"]]
        else:
            return self.tasks

    def accept_task(self, task_index: int, player) -> tuple[bool, str]:
        """接受指定任务"""
        available_tasks = self.get_available_tasks()
        if 0 <= task_index < len(available_tasks):
            task = available_tasks[task_index]
            if task.can_accept(player):
                task.accept(player)
                return True, f"任务 '{task.name}' 已接受。"
            return False, f"你未满足任务 '{task.name}' 的接受条件。"
        return False, "无效的任务编号。"

    def complete_task_dialogue(self, player) -> tuple[bool, str]:
        """处理任务完成对话"""
        player.talk_to_npc(self.number)
        for task in player.accepted_tasks:
            for condition in task.completion_conditions:
                if "talk_to_npc" in condition and condition["talk_to_npc"] == self.number:
                    if task.check_completion(player):
                        dialogue = (self.finish_task_dialogue.get(task.number, "感谢你完成任务！")
                                   if isinstance(self.finish_task_dialogue, dict)
                                   else self.finish_task_dialogue)
                        task.complete(player)
                        return True, f"{self.name}: {dialogue}"
                    return False, f"{self.name}: 你还没有完成任务 '{task.name}'。"
        return False, f"{self.name}: 你没有可以在这里完成的任务。"

    def deliver_task(self, player) -> tuple[bool, str]:
        """交付任务并发放奖励"""
        for task in player.ready_to_complete_tasks:
            if task.source_npc == self.number:
                task.give_rewards(player)
                player.completed_tasks.append(task.number)
                player.ready_to_complete_tasks.remove(task)
                return True, f"{self.name}: 你完成了任务 '{task.name}'！"
        return False, f"{self.name}: 你没有可以交付的任务。"

    def receive_gift(self, item, quantity: int) -> tuple[int, str]:
        """接受礼物并更新好感度"""
        affection_change = 5 * quantity if item in self.favorite_items else 1 * quantity
        self.affection += affection_change
        message = (f"{self.name} 非常喜欢 {item.name}，好感度增加了 {affection_change} 点！"
                  if item in self.favorite_items
                  else f"{self.name} 接受了 {item.name}，好感度增加了 {affection_change} 点。")
        return affection_change, message

    def exchange_item(self, exchange_index: int, player) -> tuple[bool, str]:
        """处理物品交易"""
        if not self.exchange:
            return False, f"{self.name} 当前没有可交易的物品。"
        if 0 <= exchange_index < len(self.exchange):
            offered_item, details = list(self.exchange.items())[exchange_index]
            required_item, required_quantity = details['item'], details['quantity']
            if player.remove_from_inventory(required_item.number, required_quantity):
                player.add_to_inventory(offered_item)
                return True, f"你成功交易了 {required_quantity} 个 {required_item.name}，获得了 {offered_item.name}。"
            return False, f"你没有足够的 {required_item.name} 进行交易。"
        return False, "无效的交易物品编号。"

    def go_battle(self, player) -> str:
        """执行战斗"""
        from common.module.battle import Battle
        enemies = self.fight
        if not enemies:
            return "no_battle"
        battle = Battle(player, [], enemies)
        return battle.run_battle()

    def get_random_taunt(self) -> str:
        """获取随机嘲讽对话"""
        dialogue_list = (self.taunt_dialogue["low"] if self.affection <= -25 else
                        self.taunt_dialogue["medium"] if self.affection <= 25 else
                        self.taunt_dialogue["high"])
        return random.choice(dialogue_list) if dialogue_list else "看来你还需要多加努力。"

    def get_affection_based_dialogue(self) -> list:
        """根据好感度返回对话列表"""
        if self.affection < -25:
            return self.affection_dialogues.get("low", ["你这个家伙，别再来烦我了！"])
        elif -25 <= self.affection <= 25:
            return self.affection_dialogues.get("medium", ["哦，你来了，最近过得好吗？"])
        else:
            return self.affection_dialogues.get("high", ["嘿，老朋友！我一直在等你呢，有什么需要我帮忙的？"])

    def remove_npc(self) -> str:
        """从游戏中移除 NPC"""
        game_state.player.mark_remove_npc(self.number)
        game_state.remove_npc(self.number)
        return f"{self.name} 已被杀死，凄惨地倒在地上。"

    def __str__(self):
        return f"NPC({self.number}, {self.name}, {self.description}, 种族: {self.race}, 好感度: {self.affection})"
