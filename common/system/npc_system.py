"""
NPC — NPC 類別
所有 print 已替換為 EventBus.emit。
Battle → BattleEngine。
"""

from __future__ import annotations

import random
from common.battle.engine import BattleEngine
from common.event import (
    EventBus,
    InfoEvent,
    WarningEvent,
    NpcInteractEvent,
    NpcDialogueEvent,
    NpcGiftEvent,
    NpcAffectionChangedEvent,
    NpcRemovedEvent,
    NpcExchangeEvent,
    NpcInteractionEvent,
    TaskCompletedEvent,
)


class NPC:
    def __init__(
        self,
        number,
        name,
        description,
        race,
        affection,
        favorite_items,
        daily_dialogue,
        task_dialogue,
        finish_task_dialogue,
        tasks=None,
        exchange=None,
        affection_dialogues=None,
        fight=None,
        taunt_dialogue=None,
        lottery=None,
    ):
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
        self.affection_dialogues = affection_dialogues or {"low": [], "medium": [], "high": []}
        self.taunt_dialogue = taunt_dialogue or {"low": [], "medium": [], "high": []}

    # ── 主互動迴圈 ──────────────────────────────────────────

    def interact(self, player):
        EventBus.emit(NpcInteractEvent(npc_id=self.number, npc_name=self.name))
        EventBus.emit(InfoEvent(message=f"\n你正在與 {self.name} 互動。"))

        MENU = (
            "1. 日常對話\n"
            "2. 接取任務\n"
            "3. 任務對話\n"
            "4. 交付任務\n"
            "5. 贈送物品\n"
            "6. 交易、學習、打造\n"
            "7. 退出對話"
        )

        while True:
            EventBus.emit(InfoEvent(message=MENU))
            choice = input("請輸入選項編號: ")

            if choice == "1":
                self.handle_daily_dialogue(player)
            elif choice == "2":
                self.handle_task_dialogue(player)
            elif choice == "3":
                self.handle_finish_task_dialogue(player)
            elif choice == "4":
                self.handle_npc_task(player)
            elif choice == "5":
                self.give_gift(player)
            elif choice == "6":
                self.handle_exchange(player)
            elif choice == "7":
                EventBus.emit(InfoEvent(message=f"你結束了與 {self.name} 的對話。"))
                break
            else:
                EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))

    # ── 交易 ────────────────────────────────────────────────

    def handle_exchange(self, player):
        if not self.exchange:
            EventBus.emit(InfoEvent(message=f"{self.name} 當前沒有可交易的物品。"))
            return

        lines = [f"{self.name} 提供以下物品進行交易："]
        items = list(self.exchange.items())
        for i, (offered_item, details) in enumerate(items, 1):
            required_item = details["item"]
            required_quantity = details["quantity"]
            lines.append(f"{i}. {offered_item.name} - 需要 {required_item.name} x{required_quantity}")
        EventBus.emit(InfoEvent(message="\n".join(lines)))

        choice = input("請輸入你想交易的物品編號: ")
        if not choice.isdigit():
            EventBus.emit(WarningEvent(message="無效的輸入，請重試。"))
            return

        idx = int(choice) - 1
        if not (0 <= idx < len(items)):
            EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))
            return

        offered_item, details = items[idx]
        required_item = details["item"]
        required_quantity = details["quantity"]

        if player.remove_from_inventory(required_item.number, required_quantity):
            player.add_to_inventory(offered_item)
            EventBus.emit(NpcExchangeEvent(
                npc_id=self.number,
                npc_name=self.name,
                offered_item=offered_item.name,
                required_item=required_item.name,
                quantity=required_quantity,
            ))
        else:
            EventBus.emit(WarningEvent(message=f"你沒有足夠的 {required_item.name} 進行交易。"))

    # ── 日常對話 ────────────────────────────────────────────

    def handle_daily_dialogue(self, player):
        all_dialogues = self.daily_dialogue + self.get_affection_based_dialogue()
        dialogue = random.choice(all_dialogues)
        EventBus.emit(NpcDialogueEvent(npc_id=self.number, npc_name=self.name, dialogue=dialogue))

        if self.affection >= -25:
            EventBus.emit(InfoEvent(message="1. 繼續對話\n2. 其它事情\n3. 結束對話"))
            choice = input("請輸入選項編號: ")
            if choice == "1":
                EventBus.emit(NpcDialogueEvent(
                    npc_id=self.number,
                    npc_name=self.name,
                    dialogue=random.choice(all_dialogues),
                ))
            elif choice == "2":
                self.invoke_function_module(player)
            elif choice == "3":
                EventBus.emit(InfoEvent(message=f"你結束了與 {self.name} 的日常對話。"))
            else:
                EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))

    def invoke_function_module(self, player):
        if self.affection < -25:
            EventBus.emit(WarningEvent(
                message=f"{self.name} 對你已經失去了信任，無法調用任何功能模組。"
            ))
            return

        lines = ["選擇要調用的功能模組:"]
        if self.affection >= 0:
            lines += ["1. 市場", "2. 戰鬥", "3. 合成"]
        lines.append("4. 返回")
        EventBus.emit(InfoEvent(message="\n".join(lines)))

        choice = input("請輸入選項編號: ")
        if choice == "1" and self.affection >= 0:
            self.call_market(player)
        elif choice == "2" and self.affection >= 0:
            self.call_battle(player)
        elif choice == "3" and self.affection >= 0:
            self.call_synthesis(player)
        elif choice == "4":
            EventBus.emit(InfoEvent(message="返回上一級菜單。"))
        else:
            EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))

    # ── 任務對話 ────────────────────────────────────────────

    def handle_task_dialogue(self, player):
        if self.affection < -25:
            EventBus.emit(WarningEvent(
                message=f"{self.name} 對你已經失去了信任，不願意給你任何任務。"
            ))
            return

        EventBus.emit(NpcDialogueEvent(
            npc_id=self.number,
            npc_name=self.name,
            dialogue=self.get_task_dialogue_based_on_affection(),
        ))

        available_tasks = self.get_available_tasks_based_on_affection()
        if not available_tasks:
            EventBus.emit(InfoEvent(message="此 NPC 沒有可接取的任務。"))
            return

        lines = ["可接取任務:"]
        for i, task in enumerate(available_tasks):
            lines.append(f"{i + 1}. {task.name}")
        EventBus.emit(InfoEvent(message="\n".join(lines)))

        choice = int(input("請輸入任務編號以接受任務: ")) - 1
        if 0 <= choice < len(available_tasks):
            available_tasks[choice].accept(player)
        else:
            EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))

    # ── 完成任務對話 ─────────────────────────────────────────

    def handle_finish_task_dialogue(self, player):
        player.talk_to_npc(self.number)
        EventBus.emit(NpcInteractionEvent(
            npc_id=self.number,
            action="talk",
            detail="finish_task_dialogue",
        ))

        completed_any = False
        for task in player.accepted_tasks:
            for condition in task.completion_conditions:
                if "talk_to_npc" in condition and condition["talk_to_npc"] == self.number:
                    if task.check_completion(player):
                        if isinstance(self.finish_task_dialogue, dict):
                            dialogue = self.finish_task_dialogue.get(task.number, "感謝你完成任務！")
                        else:
                            dialogue = self.finish_task_dialogue
                        EventBus.emit(NpcDialogueEvent(
                            npc_id=self.number,
                            npc_name=self.name,
                            dialogue=dialogue,
                        ))
                        task.complete(player)
                        completed_any = True
                    else:
                        EventBus.emit(InfoEvent(
                            message=f"{self.name}: 你還沒有完成任務 '{task.name}'。"
                        ))
                    return

        if not completed_any:
            EventBus.emit(InfoEvent(
                message=f"{self.name}: 你沒有可以在這裡完成的任務。"
            ))

    # ── 交付任務 ────────────────────────────────────────────

    def handle_npc_task(self, player):
        for task in player.ready_to_complete_tasks:
            if task.source_npc == self.number:
                EventBus.emit(InfoEvent(
                    message=f"{self.name}: 你完成了任務 '{task.name}'！"
                ))
                task.give_rewards(player)
                player.completed_tasks.append(task.number)
                player.ready_to_complete_tasks.remove(task)
                EventBus.emit(TaskCompletedEvent(
                    player=getattr(player, "name", ""),
                    task_number=task.number,
                    task_name=task.name,
                ))
                return

        EventBus.emit(InfoEvent(message=f"{self.name}: 你沒有可以交付的任務。"))

    # ── 贈送物品 ────────────────────────────────────────────

    def give_gift(self, player):
        EventBus.emit(NpcDialogueEvent(
            npc_id=self.number,
            npc_name=self.name,
            dialogue="你想贈送什麼給我？",
        ))

        inventory_items = player.get_inventory()
        if not inventory_items:
            EventBus.emit(InfoEvent(message="你沒有可以贈送的物品。"))
            return

        item_mapping: dict[int, object] = {}
        lines = []
        for idx, item in enumerate(inventory_items, 1):
            lines.append(f"{idx}. {item.name} (數量: {item.quantity})")
            item_mapping[idx] = item
        EventBus.emit(InfoEvent(message="\n".join(lines)))

        choice = input("請輸入物品編號: ")
        if not choice.isdigit() or int(choice) not in item_mapping:
            EventBus.emit(WarningEvent(message="無效的物品編號，請重試。"))
            return

        item = item_mapping[int(choice)]
        quantity_str = input(f"你有 {item.quantity} 個 {item.name}，請輸入你想贈送的數量: ")
        if not quantity_str.isdigit():
            EventBus.emit(WarningEvent(message="無效的數量輸入，請重試。"))
            return

        quantity = int(quantity_str)
        if quantity > item.quantity:
            EventBus.emit(WarningEvent(
                message=f"你沒有足夠的 {item.name}，無法贈送 {quantity} 個。"
            ))
            return

        for _ in range(quantity):
            self.receive_gift(item)
            player.remove_from_inventory(item.number, 1)

        player.give_item_to_npc(self.number, item.number, quantity)
        EventBus.emit(NpcInteractionEvent(
            npc_id=self.number,
            action="give_item",
            detail=f"{item.name} x{quantity}",
        ))

        for task in player.accepted_tasks:
            if task.check_completion(player):
                EventBus.emit(InfoEvent(message=f"任務 '{task.name}' 已完成！"))
            else:
                EventBus.emit(InfoEvent(message=f"任務 '{task.name}' 尚未完成。"))

    def receive_gift(self, item):
        delta = 5 if item in self.favorite_items else 1
        self.affection += delta
        EventBus.emit(NpcAffectionChangedEvent(
            npc_id=self.number,
            npc_name=self.name,
            delta=delta,
            total=self.affection,
            reason="gift",
        ))

    # ── 好感度工具 ──────────────────────────────────────────

    def get_affection_based_dialogue(self) -> list[str]:
        if self.affection < -25:
            return self.affection_dialogues.get("low", ["你這個傢伙，別再來煩我了！"])
        if self.affection <= 25:
            return self.affection_dialogues.get("medium", ["哦，你來了，最近過得好嗎？"])
        return self.affection_dialogues.get("high", ["嘿，老朋友！我一直在等你呢，有什麼需要我幫忙的？"])

    def get_task_dialogue_based_on_affection(self) -> str:
        if self.affection < -25:
            return "我沒有什麼要和你說的，滾開！"
        if self.affection <= 25:
            return self.task_dialogue
        if self.affection <= 75:
            return "嘿，有些任務你可能感興趣。"
        return "你來了！有些特別的任務需要你來完成。"

    def get_available_tasks_based_on_affection(self) -> list:
        if self.affection < 25:
            return [t for t in self.tasks if t.quality == "普通"]
        if self.affection <= 75:
            return [t for t in self.tasks if t.quality in ["普通", "稀有"]]
        return list(self.tasks)

    # ── 戰鬥 ────────────────────────────────────────────────

    def call_market(self, player):
        EventBus.emit(InfoEvent(message=f"你與 {self.name} 進入了市場。"))

    def call_battle(self, player):
        if not self.fight:
            EventBus.emit(WarningEvent(message=f"{self.name} 沒有準備戰鬥信息。"))
            return
        EventBus.emit(InfoEvent(message=f"你與 {self.name} 進入了戰鬥。"))
        result = self.go_battle(player)
        if result == "win":
            self.handle_victory(player)
        elif result == "loss":
            self.handle_defeat(player)

    def go_battle(self, player) -> str:
        engine = BattleEngine(player, [], self.fight)
        return engine.run()

    def handle_victory(self, player):
        EventBus.emit(InfoEvent(message=f"你戰勝了 {self.name}！"))
        choice = input("你想殺掉此 NPC 嗎？有些 NPC 會影響劇情和探索，請慎重！(y/n): ").strip().lower()
        if choice == "y":
            self.remove_npc_from_game()
        else:
            EventBus.emit(InfoEvent(message=f"{self.name} 感謝你放他一條生路。"))

    def handle_defeat(self, player):
        EventBus.emit(InfoEvent(message=f"你被 {self.name} 打敗了！"))
        EventBus.emit(NpcDialogueEvent(
            npc_id=self.number,
            npc_name=self.name,
            dialogue=self.get_random_taunt(),
        ))

    def get_random_taunt(self) -> str:
        if self.affection <= -25:
            lst = self.taunt_dialogue["low"]
        elif self.affection <= 25:
            lst = self.taunt_dialogue["medium"]
        else:
            lst = self.taunt_dialogue["high"]
        return random.choice(lst) if lst else "看來你還需要多加努力。"

    def remove_npc_from_game(self):
        EventBus.emit(NpcRemovedEvent(npc_id=self.number, npc_name=self.name))
        EventBus.emit(InfoEvent(message=f"{self.name} 被你殺死了，本周目他將不再出現！"))
        EventBus.emit(NpcInteractionEvent(
            npc_id=self.number,
            action="remove",
            detail=f"{self.name} 已被殺死",
        ))

    def call_synthesis(self, player):
        EventBus.emit(InfoEvent(message=f"你與 {self.name} 進入了合成模組。"))

    def __str__(self):
        return (
            f"NPC({self.number}, {self.name}, {self.description}, "
            f"種族: {self.race}, 好感度: {self.affection})"
        )