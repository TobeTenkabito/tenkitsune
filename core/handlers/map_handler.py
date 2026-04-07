"""
MapHandler
─────────────────────────────────────────────
处理地图跳转请求：
  - MapWarpRequestEvent → 执行传送 + 惩罚结算
  - WarpRequestEvent    → 通用传送

常驻，游戏启动时注册。
"""
from __future__ import annotations

from common.event.handlers import BattleHandler
from common.event.system.map import MapWarpRequestEvent
from common.event import EventBus, WarpRequestEvent, InfoEvent, WarningEvent


class MapHandler(BattleHandler):

    def __init__(self, player, map_registry: dict) -> None:
        self._player = player
        self._maps   = map_registry

    # ── 战败/秘境失败传送 ─────────────────────

    def on_map_warp_request_event(self, e: MapWarpRequestEvent) -> None:
        player = self._player

        # 扣除经验惩罚
        exp_loss = getattr(e, "exp_loss", 0)
        if exp_loss > 0:
            player.exp = max(0, player.exp - exp_loss)
            EventBus.emit(InfoEvent(
                message=f"你损失了 {exp_loss} 点经验值。"
            ))

        # HP 重置为 1（战败保底）
        player.hp = 1

        # 传送回出生点或指定地图
        target_map_number = getattr(e, "target_map", None) or player.birth_location
        self._warp_to(target_map_number)

    # ── 通用传送 ──────────────────────────────

    def on_warp_request_event(self, e: WarpRequestEvent) -> None:
        self._warp_to(e.target_map)

    # ── 内部工具 ──────────────────────────────

    def _warp_to(self, map_number) -> None:
        player = self._player
        target = self._maps.get(map_number)

        if target is None:
            EventBus.emit(WarningEvent(
                message=f"MapHandler: 地图 {map_number} 不存在"
            ))
            return

        if not target.can_enter(player):
            return

        player.map_location = map_number
        EventBus.emit(InfoEvent(
            message=f"你传送到了 {target.name}。"
        ))
        target.explore(player)
