"""
QuestHandler
─────────────────────────────────────────────
处理战斗事件对任务系统的影响：
  - DeathEvent      → 注册击杀，检查任务进度
  - BattleResultEvent → 检查战斗类任务完成条件

常驻，游戏启动时注册。
"""
from __future__ import annotations

from common.event.handlers import BattleHandler
from common.event.battle import DeathEvent, BattleResultEvent
from common.event import EventBus, InfoEvent


class QuestHandler(BattleHandler):

    def __init__(self, player) -> None:
        self._player = player

    # ── 击杀注册 ──────────────────────────────

    def on_death_event(self, e: DeathEvent) -> None:
        if not e.is_enemy:
            return

        player = self._player
        for task in player.accepted_tasks:
            # 检查任务中是否有击杀该敌人的条件
            for condition in _flatten_conditions(task.completion_conditions):
                if "kill" not in condition:
                    continue
                kill_cond = condition["kill"]
                if kill_cond.get("enemy_id") == e.name:
                    task.register_kill(e.name)
                    # 检查是否达成完成条件
                    if task.check_completion(player):
                        task.complete(player)
                    break

    # ── 战斗结果 ──────────────────────────────

    def on_battle_result_event(self, e: BattleResultEvent) -> None:
        if e.result != "win":
            return

        player = self._player
        for task in list(player.accepted_tasks):
            if task.check_completion(player):
                task.complete(player)


# ── 工具函数 ──────────────────────────────────

def _flatten_conditions(conditions) -> list[dict]:
    """
    将嵌套的条件结构展开为扁平列表。
    支持 AND/OR/NOT 嵌套。
    """
    result = []
    if isinstance(conditions, dict):
        for key in ("AND", "OR"):
            if key in conditions:
                for sub in conditions[key]:
                    result.extend(_flatten_conditions(sub))
        if "NOT" in conditions:
            result.extend(_flatten_conditions(conditions["NOT"]))
        # 叶节点：直接是条件 dict
        if not any(k in conditions for k in ("AND", "OR", "NOT")):
            result.append(conditions)
    elif isinstance(conditions, list):
        for item in conditions:
            result.extend(_flatten_conditions(item))
    return result
