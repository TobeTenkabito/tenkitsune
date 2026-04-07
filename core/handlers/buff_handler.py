"""
BuffHandler
─────────────────────────────────────────────
处理 Buff 相关的 Request 事件：
  - BuffRequestEvent       → 挂载 Buff 到 battle_state
  - BuffRemoveRequestEvent → 从 battle_state 移除 Buff

生命周期：随 BattleEngine 创建/销毁
"""
from __future__ import annotations

import random
import copy

from common.event.handlers import BattleHandler
from common.event.battle import (
    BuffRequestEvent,
    BuffRemoveRequestEvent,
)
from common.event import EventBus, WarningEvent
from common.module.buff import Buff


class BuffHandler(BattleHandler):

    def __init__(self, engine) -> None:
        self._engine = engine

    def _resolve(self, name: str):
        for p in self._engine._all_participants():
            if p.name == name:
                return p
        return None

    # ── Apply ─────────────────────────────────

    def on_buff_request_event(self, e: BuffRequestEvent) -> None:
        # 概率检查
        if random.random() > e.chance:
            return

        target = self._resolve(e.target)
        if target is None:
            EventBus.emit(WarningEvent(
                message=f"BuffRequest: 找不到目标 '{e.target}'"
            ))
            return

        buff = Buff(
            name=e.buff_name,
            buff_type=e.buff_type,
            duration=e.duration,
            effect=copy.deepcopy(e.effect),
            target=e.target,
        )
        target.battle_state.apply_buff(buff)

    # ── Remove ────────────────────────────────

    def on_buff_remove_request_event(self, e: BuffRemoveRequestEvent) -> None:
        target = self._resolve(e.target)
        if target is None:
            EventBus.emit(WarningEvent(
                message=f"BuffRemoveRequest: 找不到目标 '{e.target}'"
            ))
            return

        bs = target.battle_state

        if e.scope == "name":
            if not e.buff_name:
                EventBus.emit(WarningEvent(
                    message="BuffRemoveRequest: scope='name' 但 buff_name 为空"
                ))
                return
            bs.remove_buff(e.buff_name)

        elif e.scope == "type":
            if not e.buff_type:
                EventBus.emit(WarningEvent(
                    message="BuffRemoveRequest: scope='type' 但 buff_type 为空"
                ))
                return
            bs.remove_buffs_by_type(e.buff_type)

        elif e.scope == "all":
            bs.remove_all_buffs()

        else:
            EventBus.emit(WarningEvent(
                message=f"BuffRemoveRequest: 未知 scope '{e.scope}'"
            ))
