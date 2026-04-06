"""
Map — 地圖類別
所有 print 已替換為 EventBus.emit。
game_state 依賴完全移除：
  - player 透過參數傳入
  - 地圖跳轉 / 相鄰地圖 透過 EventBus emit 事件
"""

from __future__ import annotations

import copy
import random

from common.event import (
    EventBus,
    InfoEvent,
    WarningEvent,
)
from common.event.system.map import MapWarpRequestEvent, ShowAdjacentMapsEvent


class Map:
    def __init__(
        self,
        number,
        name,
        description,
        adjacent_maps,
        npcs,
        battles,
        collectible_items,
        dungeons=None,
        passport=None,
        unpasstext=None,
        passtext=None,
    ):
        self.number = number
        self.name = name
        self.description = description
        self.adjacent_maps = adjacent_maps
        self.npcs = npcs
        self.battles = battles
        self.collectible_items = collectible_items
        self.dungeons = dungeons or []
        self.passport = passport
        self.unpasstext = unpasstext
        self.passtext = passtext

    # ── 相鄰地圖 ────────────────────────────────────────────

    def add_adjacent_map(self, map_number, distance, direction="双向", map_factory=None):
        self.adjacent_maps[map_number] = {"distance": distance, "direction": direction}
        if direction == "双向" and map_factory:
            adjacent_map = map_factory(map_number)
            adjacent_map.adjacent_maps[self.number] = {"distance": distance, "direction": direction}

    # ── 通行證檢查 ──────────────────────────────────────────

    def can_enter(self, player) -> bool:
        if self.passport is None:
            if self.passtext:
                EventBus.emit(InfoEvent(message=self.passtext))
            return True

        if isinstance(self.passport, dict):
            if "AND" in self.passport:
                if not all(player.has_item(item) for item in self.passport["AND"]):
                    if self.unpasstext:
                        EventBus.emit(InfoEvent(message=self.unpasstext))
                    return False
            elif "OR" in self.passport:
                if not any(player.has_item(item) for item in self.passport["OR"]):
                    if self.unpasstext:
                        EventBus.emit(InfoEvent(message=self.unpasstext))
                    return False
        else:
            if not player.has_item(self.passport):
                if self.unpasstext:
                    EventBus.emit(InfoEvent(message=self.unpasstext))
                return False

        if self.passtext:
            EventBus.emit(InfoEvent(message=self.passtext))
        return True

    # ── 主探索迴圈 ──────────────────────────────────────────

    def explore(self, player):
        """
        player 由呼叫方傳入，不再依賴 game_state。
        """
        if not self.can_enter(player):
            return

        EventBus.emit(InfoEvent(message=f"你正在探索 {self.name}"))
        EventBus.emit(InfoEvent(message=self.description))
        self._show_npcs()
        self._show_battles()
        self._show_collectibles()

        MENU = (
            "\n請選擇你的行動：\n"
            "1. 談天說地\n"
            "2. 採集材料\n"
            "3. 清理野怪\n"
            "4. 探索秘境\n"
            "5. 離開此地\n"
            "6. 返回上一級"
        )

        while True:
            EventBus.emit(InfoEvent(message=MENU))
            choice = input("請輸入選項編號: ")

            if choice == "1":
                self.interact_with_npc(player)
            elif choice == "2":
                self.collect_materials(player)
            elif choice == "3":
                self.clean_monsters(player)
            elif choice == "4":
                self.explore_dungeon(player)
            elif choice == "5":
                # 請求顯示相鄰地圖，由 GameState handler 處理
                EventBus.emit(ShowAdjacentMapsEvent(
                    player_location=player.map_location,
                ))
            elif choice == "6":
                EventBus.emit(InfoEvent(message="若想回到主界面請多次嘗試"))
                return
            else:
                EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))

    # ── 顯示輔助 ────────────────────────────────────────────

    def _show_npcs(self):
        if self.npcs:
            lines = ["此地圖上的 NPC:"]
            for npc in self.npcs:
                lines.append(f"- {npc.name}: {npc.description}")
            EventBus.emit(InfoEvent(message="\n".join(lines)))
        else:
            EventBus.emit(InfoEvent(message="此地圖上沒有 NPC。"))

    def _show_battles(self):
        if self.battles:
            lines = ["此地圖上的戰鬥場景:"]
            for i, enemy_list in enumerate(self.battles):
                enemies = ", ".join(e.name for e in enemy_list)
                lines.append(f"{i + 1}. 敵人: {enemies}")
            EventBus.emit(InfoEvent(message="\n".join(lines)))
        else:
            EventBus.emit(InfoEvent(message="此地圖上沒有戰鬥場景。"))

    def _show_collectibles(self):
        if self.collectible_items:
            lines = ["此地圖上可採集的物品:"]
            for item in self.collectible_items:
                lines.append(f"- {item.name}")
            EventBus.emit(InfoEvent(message="\n".join(lines)))
        else:
            EventBus.emit(InfoEvent(message="此地圖上沒有可採集的物品。"))

    # ── NPC 互動 ────────────────────────────────────────────

    def interact_with_npc(self, player):
        if not self.npcs:
            EventBus.emit(InfoEvent(message="此地圖上沒有 NPC 供你互動。"))
            return

        lines = ["你可以與以下 NPC 互動:"]
        for i, npc in enumerate(self.npcs):
            lines.append(f"{i + 1}. {npc.name}")
        lines.append("0. 返回上一級")
        EventBus.emit(InfoEvent(message="\n".join(lines)))

        choice = input("請選擇 NPC 編號: ")
        if choice == "0":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.npcs):
                self.npcs[idx].interact(player)
            else:
                EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))
        except ValueError:
            EventBus.emit(WarningEvent(message="無效的輸入，請輸入數字。"))

    # ── 採集材料 ────────────────────────────────────────────

    def collect_materials(self, player):
        if not self.collectible_items:
            EventBus.emit(InfoEvent(message="此地圖上沒有可採集的物品。"))
            return

        while True:
            lines = ["\n你可以採集以下物品："]
            for i, item in enumerate(self.collectible_items.keys(), 1):
                lines.append(f"{i}. {item.name}")
            lines.append("0. 返回上一級")
            EventBus.emit(InfoEvent(message="\n".join(lines)))

            choice = input("請輸入你想採集的物品編號: ")
            if choice == "0":
                EventBus.emit(InfoEvent(message="你決定暫時不進行採集。"))
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.collectible_items):
                    selected_item = list(self.collectible_items.keys())[idx]
                    item_info = self.collectible_items[selected_item]
                    success_rate = item_info["success_rate"]
                    quantity_range = item_info["quantity_range"]

                    if random.uniform(0, 1) <= success_rate:
                        quantity = (
                            random.randint(quantity_range[0], quantity_range[1])
                            if isinstance(quantity_range, tuple)
                            else quantity_range
                        )
                        collect_item = copy.deepcopy(selected_item)
                        collect_item.quantity = quantity
                        player.add_to_inventory(collect_item)
                        EventBus.emit(InfoEvent(
                            message=f"成功採集到 {selected_item.name} x {quantity}！"
                        ))
                    else:
                        EventBus.emit(InfoEvent(message=f"採集 {selected_item.name} 失敗。"))
                else:
                    EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))
            except ValueError:
                EventBus.emit(WarningEvent(message="無效的輸入，請輸入數字。"))

    # ── 清理野怪 ────────────────────────────────────────────

    def clean_monsters(self, player):
        if not self.battles:
            EventBus.emit(InfoEvent(message="此地圖上沒有野怪。"))
            return

        lines = ["你可以挑戰以下戰鬥場景:"]
        for i, enemy_list in enumerate(self.battles):
            enemies = ", ".join(e.name for e in enemy_list)
            lines.append(f"{i + 1}. 敵人: {enemies}")
        lines.append("0. 返回上一級")
        EventBus.emit(InfoEvent(message="\n".join(lines)))

        choice = input("請選擇戰鬥場景編號: ")
        if choice == "0":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.battles):
                from common.battle.engine import BattleEngine
                engine = BattleEngine(player, [], self.battles[idx])
                result = engine.run()

                if result == "loss":
                    self.handle_monster_defeat(player)
                elif result == "win":
                    EventBus.emit(InfoEvent(message=f"{player.name} 戰勝了敵人！"))
                else:
                    EventBus.emit(WarningEvent(message="戰鬥結束，未定義的結果。"))
            else:
                EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))
        except ValueError:
            EventBus.emit(WarningEvent(message="無效的輸入，請輸入數字。"))

    def handle_monster_defeat(self, player):
        """
        戰敗：計算 exp_loss，emit MapWarpRequestEvent。
        hp 扣除 / exp 扣除 / 重新 explore 由 GameState handler 執行。
        """
        exp_loss_percentage = random.uniform(0.01, 0.1)
        exp_loss = int(player.exp * exp_loss_percentage)

        EventBus.emit(MapWarpRequestEvent(
            player_location=player.map_location,
            reason="monster_defeat",
            exp_loss=exp_loss,
        ))

    # ── 探索秘境 ────────────────────────────────────────────

    def explore_dungeon(self, player):
        if not self.dungeons:
            EventBus.emit(InfoEvent(message="此地圖上沒有秘境可以探索。"))
            return

        lines = ["你可以探索以下秘境:"]
        for i, dungeon in enumerate(self.dungeons):
            lines.append(f"{i + 1}. {dungeon.name}: {dungeon.description}")
        lines.append("0. 返回上一級")
        EventBus.emit(InfoEvent(message="\n".join(lines)))

        choice = input("請選擇秘境編號: ")
        if choice == "0":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.dungeons):
                self.dungeons[idx].enter_dungeon(player)
            else:
                EventBus.emit(WarningEvent(message="無效的選擇，請重試。"))
        except ValueError:
            EventBus.emit(WarningEvent(message="無效的輸入，請輸入數字。"))

    # ── NPC 移除 ────────────────────────────────────────────

    def remove_npc_from_map(self, npc_number):
        self.npcs = [npc for npc in self.npcs if npc.number != npc_number]