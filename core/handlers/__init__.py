"""
全局 Handler 注册入口
─────────────────────────────────────────────
使用方式：

  from core.handlers import register_global_handlers, BattleHandlerContext

  # 游戏启动时（一次）
  register_global_handlers(player, map_registry, dungeon_registry)

  # 进入战斗时
  ctx = BattleHandlerContext(engine)
  result = engine.run()
  ctx.teardown()
"""
from __future__ import annotations

from common.event import EventBus

from core.handlers.npc_handler   import NpcHandler
from core.handlers.quest_handler  import QuestHandler
from core.handlers.map_handler    import MapHandler
from core.handlers.combat_handler import CombatHandler
from core.handlers.buff_handler   import BuffHandler
from core.handlers.status_handler import StatusHandler


def register_global_handlers(
    player,
    map_registry: dict,
    dungeon_registry: dict,
) -> None:
    """
    注册全局常驻 Handler（游戏启动时调用一次）。
    """
    EventBus.register(NpcHandler(map_registry, dungeon_registry))
    EventBus.register(QuestHandler(player))
    EventBus.register(MapHandler(player, map_registry))


class BattleHandlerContext:
    """
    战斗期间的 Handler 上下文。
    进入战斗时创建，战斗结束后调用 teardown() 注销。

    用法：
        ctx = BattleHandlerContext(engine)
        result = engine.run()
        ctx.teardown()
    """

    def __init__(self, engine) -> None:
        self._handlers = [
            CombatHandler(engine),
            BuffHandler(engine),
            StatusHandler(engine),
        ]
        for h in self._handlers:
            EventBus.register(h)

    def teardown(self) -> None:
        for h in self._handlers:
            EventBus.unregister(h)
        self._handlers.clear()
