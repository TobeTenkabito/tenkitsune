"""
Task — 任務類別
所有 print 已替換為 EventBus.emit。
npc_library 查詢改為 on_npc_name_resolve hook。
"""

from __future__ import annotations

import random
import copy
from typing import Callable

from common.event import (
    EventBus,
    InfoEvent,
    WarningEvent,
    TaskAcceptedEvent,
    TaskAcceptFailedEvent,
    TaskReadyEvent,
    TaskReturnNpcEvent,
    TaskCompletedEvent,
    TaskRewardEvent,
    KillRegisteredEvent,
)


class Task:
    # ── 全域 hook：由外部注入，避免 lazy import ──────────────
    # 簽名：(npc_id: int | str) -> str
    on_npc_name_resolve: Callable[[int | str], str] | None = None

    def __init__(
        self,
        number,
        name,
        description,
        quality,
        repeatable,
        acceptance_conditions,
        completion_conditions,
        rewards,
        prerequisite_tasks=None,
        acceptance_logic=None,
        completion_logic=None,
        source_npc=None,
    ):
        self.number = number
        self.name = name
        self.description = description
        self.quality = quality
        self.repeatable = repeatable
        self.acceptance_conditions = acceptance_conditions
        self.completion_conditions = completion_conditions
        self.rewards = rewards
        self.prerequisite_tasks = prerequisite_tasks or []
        self.acceptance_logic = acceptance_logic
        self.completion_logic = completion_logic
        self.kill_counts: dict[str, int] = {}
        self.is_completed = False
        self.source_npc = source_npc

    # ── 邏輯解析 ────────────────────────────────────────────

    def evaluate_logic(self, logic, player) -> bool:
        """遞迴解析布林邏輯。"""
        if isinstance(logic, dict):
            if "AND" in logic:
                return all(self.evaluate_logic(sub, player) for sub in logic["AND"])
            if "OR" in logic:
                return any(self.evaluate_logic(sub, player) for sub in logic["OR"])
            if "NOT" in logic:
                return not self.evaluate_logic(logic["NOT"], player)
            if "task_completed" in logic:
                return logic["task_completed"] in player.completed_tasks
            if "task_not_completed" in logic:
                return logic["task_not_completed"] not in player.completed_tasks
        return bool(logic)

    def evaluate_conditions(self, conditions, player) -> bool:
        """處理條件列表與布林代數邏輯。"""
        if isinstance(conditions, dict):
            if "AND" in conditions:
                return all(self.evaluate_conditions(sub, player) for sub in conditions["AND"])
            if "OR" in conditions:
                return any(self.evaluate_conditions(sub, player) for sub in conditions["OR"])
            if "NOT" in conditions:
                return not self.evaluate_conditions(conditions["NOT"], player)
        else:
            return all(self.evaluate_single_condition(cond, player) for cond in conditions)
        return False

    def evaluate_single_condition(self, condition, player) -> bool:
        """檢查單個條件是否滿足。"""
        if "level" in condition:
            required_level = condition["level"]
            operator = condition.get("operator", "=")
            if operator == "=":
                return player.level == required_level
            if operator == ">":
                return player.level > required_level
            if operator == "<":
                return player.level < required_level
            raise ValueError(f"未知的比較運算符 '{operator}'")

        if "kill" in condition:
            kill_condition = condition["kill"]
            current_count = self.kill_counts.get(kill_condition["enemy_id"], 0)
            return current_count >= kill_condition["count"]

        if "talk_to_npc" in condition:
            return player.has_talked_to_npc(condition["talk_to_npc"])

        if "item" in condition:
            return player.get_inventory_count(condition["item"]) >= condition.get("quantity", 1)

        if "give_item_to_npc" in condition:
            d = condition["give_item_to_npc"]
            return player.get_item_given_to_npc(d["npc_id"], d["item_number"]) >= d["quantity"]

        return False

    # ── 接取 ────────────────────────────────────────────────

    def can_accept(self, player) -> bool:
        player_name = getattr(player, "name", "")

        if not self.repeatable:
            already = (
                self.number in [t.number for t in player.accepted_tasks]
                or self.number in player.completed_tasks
            )
            if already:
                EventBus.emit(TaskAcceptFailedEvent(
                    player=player_name,
                    task_number=self.number,
                    task_name=self.name,
                    reason="not_repeatable",
                ))
                return False

        for task_number in self.prerequisite_tasks:
            if task_number not in player.completed_tasks:
                EventBus.emit(TaskAcceptFailedEvent(
                    player=player_name,
                    task_number=self.number,
                    task_name=self.name,
                    reason=f"prerequisite:{task_number}",
                ))
                return False

        if self.acceptance_logic:
            result = self.evaluate_logic(self.acceptance_logic, player)
            if not result:
                EventBus.emit(TaskAcceptFailedEvent(
                    player=player_name,
                    task_number=self.number,
                    task_name=self.name,
                    reason="condition",
                ))
            return result

        result = self.evaluate_conditions(self.acceptance_conditions, player)
        if not result:
            EventBus.emit(TaskAcceptFailedEvent(
                player=player_name,
                task_number=self.number,
                task_name=self.name,
                reason="condition",
            ))
        return result

    def accept(self, player):
        player_name = getattr(player, "name", "")
        if self.can_accept(player):
            player.accepted_tasks.append(self)
            EventBus.emit(TaskAcceptedEvent(
                player=player_name,
                task_number=self.number,
                task_name=self.name,
            ))
        else:
            EventBus.emit(WarningEvent(
                message=f"任務 '{self.name}' 無法接受。",
            ))

    # ── 完成 ────────────────────────────────────────────────

    def check_completion(self, player) -> bool:
        if self.completion_logic:
            return self.evaluate_logic(self.completion_logic, player)
        return self.evaluate_conditions(self.completion_conditions, player)

    def complete(self, player):
        player_name = getattr(player, "name", "")
        if self.check_completion(player):
            self.is_completed = True
            player.accepted_tasks.remove(self)
            player.ready_to_complete_tasks.append(self)

            EventBus.emit(TaskReadyEvent(
                player=player_name,
                task_number=self.number,
                task_name=self.name,
            ))

            if self.source_npc is None:
                self.give_rewards(player)
                EventBus.emit(TaskCompletedEvent(
                    player=player_name,
                    task_number=self.number,
                    task_name=self.name,
                ))
            else:
                npc_name = self._resolve_npc_name(self.source_npc)
                EventBus.emit(TaskReturnNpcEvent(
                    player=player_name,
                    task_number=self.number,
                    task_name=self.name,
                    npc_id=self.source_npc,
                    npc_name=npc_name,
                ))
        else:
            EventBus.emit(WarningEvent(
                message=f"任務 '{self.name}' 尚未完成。",
            ))

    # ── 獎勵 ────────────────────────────────────────────────

    def give_rewards(self, player):
        player_name = getattr(player, "name", "")
        for reward in self.rewards:
            if random.random() > reward.get("chance", 1.0):
                continue

            rtype = reward["type"]

            if rtype == "item":
                reward_item = copy.deepcopy(reward["item"])
                reward_item.quantity = reward["quantity"]
                player.add_to_inventory(reward_item)
                detail = f"{reward_item.name} x {reward_item.quantity}"
                EventBus.emit(TaskRewardEvent(
                    player=player_name,
                    task_number=self.number,
                    reward_type="item",
                    detail=detail,
                ))

            elif rtype == "exp":
                player.gain_exp(reward["amount"])
                detail = f"{reward['amount']} 點經驗值"
                EventBus.emit(TaskRewardEvent(
                    player=player_name,
                    task_number=self.number,
                    reward_type="exp",
                    detail=detail,
                ))

            elif rtype == "attribute":
                attr = reward["attribute"]
                value = reward["value"]
                player.gain_task_attribute(attr, value)
                detail = f"{attr} +{value}"
                EventBus.emit(TaskRewardEvent(
                    player=player_name,
                    task_number=self.number,
                    reward_type="attribute",
                    detail=detail,
                ))

    # ── 擊殺計數 ────────────────────────────────────────────

    def register_kill(self, enemy_id: str):
        self.kill_counts.setdefault(enemy_id, 0)
        self.kill_counts[enemy_id] += 1
        EventBus.emit(KillRegisteredEvent(
            task_name=self.name,
            enemy_id=enemy_id,
            current_count=self.kill_counts[enemy_id],
        ))

    # ── 內部工具 ────────────────────────────────────────────

    def _resolve_npc_name(self, npc_id: int | str) -> str:
        """透過 hook 取得 NPC 名稱，避免直接 import npc_library。"""
        if callable(Task.on_npc_name_resolve):
            return Task.on_npc_name_resolve(npc_id)
        return f"NPC 編號 {npc_id}"