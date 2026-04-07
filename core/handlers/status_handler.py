"""
StatusHandler
─────────────────────────────────────────────
处理状态异常的施加请求：
  - StatusAppliedEvent → 将状态异常作为 Buff 写入 battle_state

状态异常在 BattleState 中以特殊 Buff 形式存储：
  effect = {"attribute": "stunned", "value": 0, "tick": False}

生命周期：随 BattleEngine 创建/销毁
"""
from __future__ import annotations

from common.event.handlers import BattleHandler
from common.event.battle import StatusAppliedEvent
from common.event import EventBus, WarningEvent
from common.module.buff import Buff


# 状态异常 → buff_type 映射
_STATUS_BUFF_TYPE = {
    "stunned":   "debuff",
    "paralyzed": "debuff",
    "silenced":  "debuff",
    "blinded":   "debuff",
}


class StatusHandler(BattleHandler):

    def __init__(self, engine) -> None:
        self._engine = engine

    def _resolve(self, name: str):
        for p in self._engine._all_participants():
            if p.name == name:
                return p
        return None

    def on_status_applied_event(self, e: StatusAppliedEvent) -> None:
        target = self._resolve(e.target)
        if target is None:
            EventBus.emit(WarningEvent(
                message=f"StatusApplied: 找不到目标 '{e.target}'"
            ))
            return

        buff_type = _STATUS_BUFF_TYPE.get(e.status, "debuff")

        buff = Buff(
            name=e.status,
            buff_type=buff_type,
            duration=e.rounds,
            effect={
                "attribute": e.status,
                "value": 0,
                "tick": False,
            },
            target=e.target,
        )
        target.battle_state.apply_buff(buff)
