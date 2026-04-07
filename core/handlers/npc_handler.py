"""
NpcHandler
─────────────────────────────────────────────
处理 NPC 被移除后的跨层联动：
  - NpcRemovedEvent → 从 Map 和 Dungeon 中移除 NPC

常驻，游戏启动时注册。
"""
from __future__ import annotations

from common.event.handlers import BattleHandler
from common.event.system.npc import NpcRemovedEvent
from common.event import EventBus, WarningEvent


class NpcHandler(BattleHandler):

    def __init__(
        self,
        map_registry: dict,       # map_number → Map
        dungeon_registry: dict,   # dungeon_number → Dungeon
    ) -> None:
        self._maps     = map_registry
        self._dungeons = dungeon_registry

    def on_npc_removed_event(self, e: NpcRemovedEvent) -> None:
        removed_any = False

        # 从所有地图移除
        for m in self._maps.values():
            before = len(m.npcs)
            m.remove_npc_from_map(e.npc_id)
            if len(m.npcs) < before:
                removed_any = True

        # 从所有秘境移除
        for d in self._dungeons.values():
            if d.remove_npc_from_dungeon(e.npc_id):
                removed_any = True

        if not removed_any:
            EventBus.emit(WarningEvent(
                message=f"NpcHandler: NPC {e.npc_id}({e.npc_name}) "
                        f"不存在于任何地图或秘境中"
            ))
