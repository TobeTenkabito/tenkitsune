"""
修為系統（五行修為 + 心法）
─────────────────────────────────────────────
與舊版的差異：
  - skill_library 參數移除，改用 registry.get("skill", id)
  - 所有 print 改為 EventBus.emit
  - 修為屬性加成 / 扣除改為 emit StatChangeRequestEvent（scope="permanent"）
  - player.update_stats() 保留（非戰鬥屬性同步）
  - player.add_to_inventory / remove_from_inventory / remove_skill 保留
"""

from __future__ import annotations

from core.registry import registry
from common.event import (
    EventBus,
    WarningEvent,
    InfoEvent,
    StatChangeRequestEvent,
    CultivationUpgradeEvent,
    CultivationResetEvent,
    XinfaUnlockEvent,
    XinfaResetEvent,
)


# ── 常數 ──────────────────────────────────────────────────────

_XINFA_LINES: dict[int, tuple[str, list[int]]] = {
    1: ("重陽功",   [251001, 251002, 251003, 251004, 251005]),
    2: ("九尾迷心", [252001, 252002, 252003, 252004, 252005]),
    3: ("天劍玄典", [253001, 253002, 253003, 253004, 253005]),
    4: ("萬魔真經", [254001, 254002, 254003, 254004, 254005]),
    5: ("太阿神訣", [254001, 254002, 254003, 254004, 254005]),  # 與 line4 共用 ID（原始邏輯保留）
}

_CULTIVATION_DATA: dict[str, dict] = {
    "金": {
        "level": 0,
        "attributes_per_level": {
            1: {"cultivation_attack": 28,  "cultivation_crit": 1},
            2: {"cultivation_attack": 84,  "cultivation_crit": 2},
            3: {"cultivation_attack": 168, "cultivation_crit": 3},
            4: {"cultivation_attack": 280, "cultivation_crit": 4},
            5: {"cultivation_attack": 420, "cultivation_crit": 5},
        },
    },
    "木": {
        "level": 0,
        "attributes_per_level": {
            1: {"cultivation_speed": 8,   "cultivation_penetration": 1},
            2: {"cultivation_speed": 24,  "cultivation_penetration": 2},
            3: {"cultivation_speed": 48,  "cultivation_penetration": 3},
            4: {"cultivation_speed": 80,  "cultivation_penetration": 4},
            5: {"cultivation_speed": 120, "cultivation_penetration": 5},
        },
    },
    "水": {
        "level": 0,
        "attributes_per_level": {
            1: {"cultivation_mp": 32,  "cultivation_crit_damage": 1},
            2: {"cultivation_mp": 96,  "cultivation_crit_damage": 2},
            3: {"cultivation_mp": 192, "cultivation_crit_damage": 3},
            4: {"cultivation_mp": 320, "cultivation_crit_damage": 4},
            5: {"cultivation_mp": 480, "cultivation_crit_damage": 5},
        },
    },
    "火": {
        "level": 0,
        "attributes_per_level": {
            1: {"cultivation_hp": 64,  "cultivation_crit_damage": 1},
            2: {"cultivation_hp": 192, "cultivation_crit_damage": 2},
            3: {"cultivation_hp": 384, "cultivation_crit_damage": 3},
            4: {"cultivation_hp": 640, "cultivation_crit_damage": 4},
            5: {"cultivation_hp": 960, "cultivation_crit_damage": 5},
        },
    },
    "土": {
        "level": 0,
        "attributes_per_level": {
            1: {"cultivation_defense": 20,  "cultivation_resistance": 1},
            2: {"cultivation_defense": 60,  "cultivation_resistance": 2},
            3: {"cultivation_defense": 120, "cultivation_resistance": 3},
            4: {"cultivation_defense": 200, "cultivation_resistance": 4},
            5: {"cultivation_defense": 300, "cultivation_resistance": 5},
        },
    },
}

_XINFA_THRESHOLDS = [0, 20, 40, 60, 80]   # 各等級解鎖所需已用修為點


# ══════════════════════════════════════════════════════════════
#  CultivationSystem
# ══════════════════════════════════════════════════════════════

class CultivationSystem:

    MAX_LEVEL = 5

    def __init__(self, player):
        self.player = player

        # 五行修為數據（深拷貝常數，避免跨實例污染）
        import copy
        self.cultivation_data: dict[str, dict] = copy.deepcopy(_CULTIVATION_DATA)

        # 心法狀態
        self.current_xinfa_line_id: int | None = None   # 1~5
        self.current_xinfa_level:   int        = 0

        # 修為點計數
        self.used_points:   int = 0
        self.unused_points: int = player.cultivation_point

        # 從背包 / 技能欄初始化心法狀態
        self._update_xinfa_from_inventory()

    # ── 屬性：當前心法線技能 ID 列表 ─────────────────────────

    @property
    def _current_xinfa_skill_ids(self) -> list[int] | None:
        if self.current_xinfa_line_id is None:
            return None
        return _XINFA_LINES[self.current_xinfa_line_id][1]

    @property
    def _current_xinfa_name(self) -> str:
        if self.current_xinfa_line_id is None:
            return "（未選擇）"
        return _XINFA_LINES[self.current_xinfa_line_id][0]

    # ── 存檔還原 ──────────────────────────────────────────────

    def restore_from_save(self, save_data: dict) -> None:
        if "cultivation_data" not in save_data:
            EventBus.emit(WarningEvent(
                message="存檔中找不到 'cultivation_data'，跳過還原。"
            ))
            return

        for element, data in save_data["cultivation_data"].items():
            if element not in self.cultivation_data:
                continue
            self.cultivation_data[element]["level"] = data.get("level", 0)
            self.cultivation_data[element]["attributes_per_level"] = {
                int(lv): attrs
                for lv, attrs in data.get("attributes_per_level", {}).items()
            }

        self.used_points   = save_data.get("used_points",   0)
        self.unused_points = save_data.get("unused_points", self.player.cultivation_point)

    # ── 五行修為：升級 ────────────────────────────────────────

    def upgrade(self, element: str) -> bool:
        """
        升級指定五行修為。
        成功回傳 True，失敗回傳 False。
        屬性加成透過 StatChangeRequestEvent（scope="permanent"）通知。
        """
        if element not in self.cultivation_data:
            EventBus.emit(WarningEvent(
                message=f"無效的修為元素：{element}。"
            ))
            return False

        current_level = self.cultivation_data[element]["level"]

        if current_level >= self.MAX_LEVEL:
            EventBus.emit(WarningEvent(
                message=f"【{element}】修為已達最高等級（{self.MAX_LEVEL}）。"
            ))
            return False

        cost = current_level + 2
        if self.unused_points < cost:
            EventBus.emit(WarningEvent(
                message=(
                    f"培養點不足，無法提升【{element}】修為。"
                    f"需要 {cost} 點，剩餘 {self.unused_points} 點。"
                )
            ))
            return False

        new_level = current_level + 1
        attr_increases = (
            self.cultivation_data[element]
            .get("attributes_per_level", {})
            .get(new_level)
        )
        if not attr_increases:
            EventBus.emit(WarningEvent(
                message=f"【{element}】第 {new_level} 級沒有定義屬性加成。"
            ))
            return False

        # 更新內部狀態
        self.cultivation_data[element]["level"] = new_level
        self.used_points   += cost
        self.unused_points -= cost
        self.player.cultivation_point = self.unused_points

        # 屬性加成 → StatChangeRequestEvent
        for attr, increase in attr_increases.items():
            EventBus.emit(StatChangeRequestEvent(
                source="cultivation",
                target=self.player.name,
                attr=attr,
                change=increase,
                scope="permanent",
            ))

        self.player.update_stats()

        EventBus.emit(CultivationUpgradeEvent(
            player=self.player.name,
            element=element,
            new_level=new_level,
            cost=cost,
            remaining_points=self.unused_points,
        ))
        return True

    # ── 五行修為：重置 ────────────────────────────────────────

    def reset(self) -> None:
        """
        重置所有五行修為，返還培養點。
        屬性扣除透過 StatChangeRequestEvent（scope="permanent", change 為負值）。
        """
        for element, data in self.cultivation_data.items():
            level = data["level"]
            if level <= 0:
                continue

            attr_decreases = data["attributes_per_level"].get(level, {})
            for attr, decrease in attr_decreases.items():
                EventBus.emit(StatChangeRequestEvent(
                    source="cultivation_reset",
                    target=self.player.name,
                    attr=attr,
                    change=-decrease,
                    scope="permanent",
                ))

            data["level"] = 0

        self.unused_points += self.used_points
        self.used_points    = 0
        self.player.cultivation_point = self.unused_points

        self.player.update_stats()
        self._reset_xinfa()

        EventBus.emit(CultivationResetEvent(
            player=self.player.name,
            returned_points=self.unused_points,
        ))

    # ── 心法：選擇線路 ────────────────────────────────────────

    def select_xinfa_line(self, line: int) -> None:
        if line not in _XINFA_LINES:
            EventBus.emit(WarningEvent(
                message=f"無效的心法線選擇：{line}。"
            ))
            return

        self.current_xinfa_line_id = line
        EventBus.emit(InfoEvent(
            message=f"已選擇心法線：【{self._current_xinfa_name}】"
        ))

    # ── 心法：檢查並解鎖 ─────────────────────────────────────

    def check_xinfa_unlock(self) -> None:
        if self.current_xinfa_line_id is None:
            EventBus.emit(WarningEvent(message="請先選擇心法線。"))
            return

        if not self._has_xinfa_level1_skill():
            EventBus.emit(WarningEvent(
                message="尚未擁有該心法線的一級技能，無法解鎖下一等級。"
            ))
            return

        if self.current_xinfa_level == 0:
            self.current_xinfa_level = 1

        for i in range(self.current_xinfa_level + 1, len(_XINFA_THRESHOLDS)):
            if self.used_points < _XINFA_THRESHOLDS[i]:
                break
            if i >= 1 and self._is_level_unlocked_in_other_lines(i):
                EventBus.emit(WarningEvent(
                    message=f"已在其他心法線激活了 Level {i + 1}，無法在此線激活。"
                ))
                break
            self._unlock_xinfa(i + 1)

    # ── 心法：內部輔助 ────────────────────────────────────────

    def _update_xinfa_from_inventory(self) -> None:
        """啟動時掃描背包 / 技能欄，還原心法狀態。"""
        for line_id, (_, skill_ids) in _XINFA_LINES.items():
            for level, skill_id in enumerate(skill_ids, start=1):
                if self.player.has_skill(skill_id):
                    self.current_xinfa_line_id = line_id
                    self.current_xinfa_level   = max(self.current_xinfa_level, level)

        EventBus.emit(InfoEvent(
            message=f"心法初始化完成，當前等級：{self.current_xinfa_level}"
        ))

    def _has_xinfa_level1_skill(self) -> bool:
        skill_ids = self._current_xinfa_skill_ids
        if not skill_ids:
            return False
        skill_id = skill_ids[0]   # Level 1 = index 0
        skill    = registry.get("skill", skill_id)
        if skill and self.player.has_skill(skill.number):
            return True
        return False

    def _is_level_unlocked_in_other_lines(self, level_index: int) -> bool:
        """
        檢查其他心法線的第 level_index 級（0-based）是否已解鎖。
        """
        for line_id, (_, skill_ids) in _XINFA_LINES.items():
            if line_id == self.current_xinfa_line_id:
                continue
            if level_index >= len(skill_ids):
                continue
            skill_id = skill_ids[level_index]
            if self.player.has_skill(skill_id):
                return True
        return False

    def _unlock_xinfa(self, level: int) -> None:
        """解鎖指定等級的心法技能（1-based）。"""
        skill_ids = self._current_xinfa_skill_ids
        if not skill_ids or level > len(skill_ids):
            EventBus.emit(WarningEvent(
                message=f"心法等級 {level} 對應技能不存在。"
            ))
            return

        skill_id = skill_ids[level - 1]
        skill    = registry.get("skill", skill_id)
        if not skill:
            EventBus.emit(WarningEvent(
                message=f"Registry 找不到技能 ID={skill_id}。"
            ))
            return

        self.player.add_to_inventory(skill)
        self.current_xinfa_level = level

        EventBus.emit(XinfaUnlockEvent(
            player=self.player.name,
            xinfa_name=self._current_xinfa_name,
            level=level,
            skill_name=skill.name,
        ))

    def _reset_xinfa(self) -> None:
        """重置心法（保留第一級）。"""
        skill_ids = self._current_xinfa_skill_ids
        if not skill_ids:
            return

        for level in range(2, self.current_xinfa_level + 1):
            skill_id = skill_ids[level - 1]
            skill    = registry.get("skill", skill_id)
            if not skill:
                continue

            removed = self.player.remove_from_inventory(skill.number, 1)
            self.player.remove_skill(skill.number)

            EventBus.emit(XinfaResetEvent(
                player=self.player.name,
                xinfa_name=self._current_xinfa_name,
                level=level,
                skill_name=skill.name,
                removed=removed,
            ))

        self.current_xinfa_level = 1
