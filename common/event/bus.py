"""
EventBus 核心
─────────────────────────────────────────────
只包含：
  - BattleEvent 基類
  - _BattleEventBus 實作
  - EventBus 全域單例
  - _to_snake 工具函數
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
import json
import re


# ══════════════════════════════════════════════
#  事件基類
# ══════════════════════════════════════════════

@dataclass
class BattleEvent:
    """所有事件的基類。"""

    def to_dict(self) -> dict:
        return {"type": self.__class__.__name__, **asdict(self)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ══════════════════════════════════════════════
#  EventBus
# ══════════════════════════════════════════════

class _EventBus:
    """
    全域事件總線。
      register(handler)   : 添加 Handler
      unregister(handler) : 移除 Handler
      emit(event)         : 發送事件給所有 Handler
      clear()             : 清空所有 Handler（測試用）
    """

    def __init__(self):
        self._handlers: list = []

    def register(self, handler) -> None:
        self._handlers.append(handler)

    def unregister(self, handler) -> None:
        self._handlers.remove(handler)

    def emit(self, event: BattleEvent) -> None:
        for handler in self._handlers:
            handler.handle(event)

    def clear(self) -> None:
        self._handlers.clear()


# 全域單例
EventBus = _EventBus()


# ══════════════════════════════════════════════
#  工具函數
# ══════════════════════════════════════════════

def _to_snake(name: str) -> str:
    """CamelCase → snake_case。例：DamageEvent → damage_event"""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
