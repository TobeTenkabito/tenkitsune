"""
DungeonFloor / Dungeon — 秘境類別
所有 print 已替換為 EventBus.emit。
Battle → BattleEngine。
game_state 呼叫 → emit 事件佔位。
"""

from __future__ import annotations

import random
from copy import deepcopy
from typing import Callable

from common.battle.engine import BattleEngine
from common.event.system.map import MapWarpRequestEvent
from common.event import (
    EventBus,
    InfoEvent,
    WarningEvent,
    DungeonEnteredEvent,
    DungeonFloorEnteredEvent,
    DungeonFloorClearedEvent,
    DungeonRewardEvent,
    DungeonClearedEvent,
    DungeonLostEvent,
    DungeonNpcRemovedEvent,
    DungeonProgressEvent,
    NpcAffectionChangedEvent,
)


class DungeonFloor:
    def __init__(
        self,
        number,
        description,
        enemies=None,
        npc=None,
        entry_buff=None,
        rewards=None,
        first_time_rewards=None,
        random_rewards=None,
        restrictions=None,
    ):
        self.number = number
        self.description = description
        self.enemies = enemies or []
        self.npc = npc
        self.entry_buff = entry_buff
        self.rewards = rewards or []
        self.first_time_rewards = first_time_rewards or []
        self.random_rewards = random_rewards or []
        self.restrictions = restrictions or {}
        self.completed = False

    def enter(self, player, dungeon_id=None, is_first_time: bool = False) -> bool:
        EventBus.emit(DungeonFloorEnteredEvent(
            player=getattr(player, "name", ""),
            dungeon_id=dungeon_id or 0,
            floor_number=self.number,
            description=self.description,
        ))

        # 移除已標記刪除的 NPC
        if self.npc is not None and self.npc.number in player.npcs_removed:
            self.npc = None

        if self.npc:
            self.npc.interact(player)

        # 入場 Buff
        if self.entry_buff:
            buffs = self.entry_buff if isinstance(self.entry_buff, list) else [self.entry_buff]
            for buff in buffs:
                EventBus.emit(InfoEvent(message=f"玩家獲得了 {buff.name} buff."))
                player.add_buff(deepcopy(buff))

        # 戰鬥
        if self.enemies:
            EventBus.emit(InfoEvent(
                message=f"開始戰鬥，敵人: {[e.name for e in self.enemies]}"
            ))
            engine = BattleEngine(player, [], self.enemies)
            result = engine.run()
            EventBus.emit(InfoEvent(message=f"戰鬥結果: {result}"))

            if result == "win":
                self.completed = True
                self.give_rewards(player, dungeon_id=dungeon_id, is_first_time=is_first_time)
                EventBus.emit(DungeonFloorClearedEvent(
                    player=getattr(player, "name", ""),
                    dungeon_id=dungeon_id or 0,
                    floor_number=self.number,
                ))
                return True
            else:
                EventBus.emit(WarningEvent(message="玩家未能通過這一層。"))
                return False
        else:
            self.completed = True
            self.give_rewards(player, dungeon_id=dungeon_id, is_first_time=is_first_time)
            EventBus.emit(DungeonFloorClearedEvent(
                player=getattr(player, "name", ""),
                dungeon_id=dungeon_id or 0,
                floor_number=self.number,
            ))
            return True

    def give_rewards(self, player, dungeon_id=None, is_first_time: bool = False):
        EventBus.emit(InfoEvent(message=f"開始發放獎勵: 首通狀態: {is_first_time}"))

        if is_first_time and self.first_time_rewards:
            for reward in self.first_time_rewards:
                self._apply_reward(player, reward, dungeon_id=dungeon_id,
                                   is_first_time=True, reward_kind="first_time")

        for reward in self.rewards:
            self._apply_reward(player, reward, dungeon_id=dungeon_id,
                               is_first_time=is_first_time, reward_kind="fixed")

        for reward in self.random_rewards:
            if random.random() <= reward.get("chance", 1.0):
                self._apply_reward(player, reward, dungeon_id=dungeon_id,
                                   is_first_time=is_first_time, reward_kind="random")
            else:
                EventBus.emit(InfoEvent(message=f"未能獲得隨機獎勵: {reward['item'].name}"))

    def _apply_reward(self, player, reward: dict, dungeon_id=None,
                      is_first_time: bool = False, reward_kind: str = "fixed"):
        player_name = getattr(player, "name", "")
        rtype = reward["type"]

        if rtype == "item":
            reward_item = deepcopy(reward["item"])
            reward_item.quantity = reward["quantity"]
            player.add_to_inventory(reward_item)
            EventBus.emit(DungeonRewardEvent(
                player=player_name, dungeon_id=dungeon_id or 0,
                floor_number=self.number, reward_type="item",
                detail=f"{reward_item.name} x {reward_item.quantity}",
                is_first_time=is_first_time, reward_kind=reward_kind,
            ))

        elif rtype == "exp":
            player.gain_exp(reward["amount"])
            EventBus.emit(DungeonRewardEvent(
                player=player_name, dungeon_id=dungeon_id or 0,
                floor_number=self.number, reward_type="exp",
                detail=f"{reward['amount']} 點經驗值",
                is_first_time=is_first_time, reward_kind=reward_kind,
            ))

        elif rtype == "attribute":
            player.gain_dungeon_attribute(reward["attribute"], reward["value"])
            EventBus.emit(DungeonRewardEvent(
                player=player_name, dungeon_id=dungeon_id or 0,
                floor_number=self.number, reward_type="attribute",
                detail=f"{reward['attribute']} +{reward['value']}",
                is_first_time=is_first_time, reward_kind=reward_kind,
            ))

    def remove_npc_dungeon_floor(self):
        if self.npc:
            EventBus.emit(InfoEvent(
                message=f"NPC {self.npc.name} 已從秘境的第 {self.number} 層移除。"
            ))
            self.npc = None
        else:
            EventBus.emit(WarningEvent(
                message=f"該樓層 {self.number} 沒有 NPC 需要移除。"
            ))


# ════════════════════════════════════════════════════════════


class Dungeon:
    # hook：(npc_id) -> NPC | None，由外部注入避免 lazy import
    on_npc_resolve: Callable[[int | str], object | None] | None = None

    def __init__(
        self,
        name,
        number,
        description,
        floors,
        can_replay_after_completion: bool = True,
        npc_affection_impact=None,
    ):
        self.name = name
        self.number = number
        self.description = description
        self.floors: list[DungeonFloor] = floors
        self.highest_floor = 0
        self.completed = False
        self.player_restrictions: dict = {}
        self.can_replay_after_completion = can_replay_after_completion
        self.npc_affection_impact = npc_affection_impact or {}

    # ── 進入秘境 ────────────────────────────────────────────

    def enter_dungeon(self, player):
        player_name = getattr(player, "name", "")

        if (self.completed or self.number in player.dungeons_cleared) \
                and not self.can_replay_after_completion:
            EventBus.emit(WarningEvent(
                message=f"你已經通關了秘境 '{self.name}'，不能再次進入。"
            ))
            return

        self.apply_npc_affection_impact(player)

        EventBus.emit(DungeonEnteredEvent(
            player=player_name,
            dungeon_id=self.number,
            dungeon_name=self.name,
        ))

        for floor in self.floors:
            EventBus.emit(InfoEvent(message=f"進入 {floor.description}"))

            if floor.npc is not None and floor.npc.number in player.npcs_removed:
                EventBus.emit(InfoEvent(
                    message=f"NPC {floor.npc.name} 已被你殺死，不再出現在本秘境樓層 {floor.number}。"
                ))
                floor.npc = None

            is_first_time = player.highest_floor.get(self.number, 0) < floor.number

            floor_success = floor.enter(
                player,
                dungeon_id=self.number,
                is_first_time=is_first_time,
            )

            if not floor_success:
                self.handle_loss_explore(player)
                break

            self.highest_floor = max(self.highest_floor, floor.number)
            player.update_highest_floor(self.number, floor.number)
            EventBus.emit(DungeonProgressEvent(
                dungeon_id=self.number,
                floor=floor.number,
                player=player_name,
                dungeon_name=self.name,
            ))

        if self.highest_floor == len(self.floors):
            self.completed = True
            player.mark_dungeon_cleared(self.number)
            EventBus.emit(DungeonClearedEvent(
                player=player_name,
                dungeon_id=self.number,
                dungeon_name=self.name,
            ))
        else:
            EventBus.emit(InfoEvent(
                message=f"你未能通關秘境 '{self.name}'，當前最高層: {self.highest_floor}，請再接再厲！"
            ))

        player.display_inventory()

    # ── 失敗處理 ────────────────────────────────────────────

    def handle_loss_explore(self, player):
        exp_loss_percentage = random.uniform(0.01, 0.1)
        exp_loss = int(player.exp * exp_loss_percentage)

        EventBus.emit(DungeonLostEvent(
            player=getattr(player, "name", ""),
            dungeon_id=self.number,
            exp_loss=exp_loss,
        ))

        # 地圖跳轉佔位，等 GameState 狀態機接管
        EventBus.emit(MapWarpRequestEvent(
            player_location=player.map_location,
            reason="dungeon_loss",
        ))

    # ── NPC 好感度影響 ───────────────────────────────────────

    def apply_npc_affection_impact(self, player):
        if not Dungeon.on_npc_resolve:
            return
        for npc_id, affection_change in self.npc_affection_impact.items():
            npc = Dungeon.on_npc_resolve(npc_id)
            if npc:
                npc.affection += affection_change
                EventBus.emit(NpcAffectionChangedEvent(
                    npc_id=npc_id,
                    npc_name=npc.name,
                    delta=affection_change,
                    total=npc.affection,
                    reason=f"enter_dungeon_{self.number}",
                ))

    # ── 其他工具方法 ─────────────────────────────────────────

    def check_completion(self) -> bool:
        return self.completed

    def finish(self, player):
        self.completed = True
        player.dungeon_clears[self.number] = self.completed
        player.mark_dungeon_cleared(self.number)
        player.display_inventory()
        player.update_stats()
        if self.number not in player.dungeons_cleared:
            player.dungeons_cleared.add(self.number)

    def remove_npc_from_dungeon(self, npc_number) -> bool:
        for floor in self.floors:
            if floor.npc and floor.npc.number == npc_number:
                floor.remove_npc_dungeon_floor()
                EventBus.emit(DungeonNpcRemovedEvent(
                    dungeon_id=self.number,
                    dungeon_name=self.name,
                    npc_id=npc_number,
                    floor_number=floor.number,
                ))
                return True
        EventBus.emit(WarningEvent(
            message=f"未找到編號為 {npc_number} 的 NPC 在秘境 {self.name} 中。"
        ))
        return False

    def add_restrictions(self, restrictions: dict):
        self.player_restrictions = restrictions

    def reset_progress(self):
        self.highest_floor = 0
        self.completed = False
        for floor in self.floors:
            floor.completed = False