"""
技能組件
─────────────────────────────────────────────
管理已學技能與裝備欄位
"""

from __future__ import annotations
from dataclasses import dataclass, field
from common.event import EventBus, WarningEvent, SkillEquippedEvent, SkillRemovedEvent


# ══════════════════════════════════════════════
#  技能欄
# ══════════════════════════════════════════════

class SkillSet:
    def __init__(self, max_equipped: int = 6, owner: str = "unknown"):
        self.owner        = owner
        self.max_equipped = max_equipped
        self._learned:  dict[str, object] = {}   # 所有已學技能
        self._equipped: list[str]         = []   # 當前裝備的技能名稱（有序）

    # ══════════════════════════════════════════
    #  學習
    # ══════════════════════════════════════════

    def learn(self, skill) -> None:
        """學習技能，不自動裝備。"""
        name = skill.name
        if name in self._learned:
            EventBus.emit(WarningEvent(message=f"{self.owner} 已學過【{name}】"))
            return
        self._learned[name] = skill

    # ══════════════════════════════════════════
    #  裝備 / 移除
    # ══════════════════════════════════════════

    def equip(self, skill_name: str) -> bool:
        """裝備技能到快捷欄，回傳是否成功。"""
        if skill_name not in self._learned:
            EventBus.emit(WarningEvent(message=f"{self.owner} 尚未學習【{skill_name}】"))
            return False
        if skill_name in self._equipped:
            EventBus.emit(WarningEvent(message=f"{self.owner}【{skill_name}】已在裝備欄中"))
            return False
        if len(self._equipped) >= self.max_equipped:
            EventBus.emit(WarningEvent(
                message=f"{self.owner} 技能欄已滿（上限 {self.max_equipped}）"
            ))
            return False

        self._equipped.append(skill_name)
        EventBus.emit(SkillEquippedEvent(player=self.owner, skill_name=skill_name))
        return True

    def unequip(self, skill_name: str) -> bool:
        """從快捷欄移除技能，回傳是否成功。"""
        if skill_name not in self._equipped:
            EventBus.emit(WarningEvent(message=f"{self.owner}【{skill_name}】不在裝備欄中"))
            return False
        self._equipped.remove(skill_name)
        EventBus.emit(SkillRemovedEvent(player=self.owner, skill_name=skill_name))
        return True

    # ══════════════════════════════════════════
    #  查詢
    # ══════════════════════════════════════════

    def get(self, skill_name: str) -> object | None:
        """取得技能物件（已學即可，不限裝備）。"""
        return self._learned.get(skill_name)

    def get_equipped(self) -> list[object]:
        """回傳所有已裝備的技能物件（按順序）。"""
        return [self._learned[n] for n in self._equipped if n in self._learned]

    def has_learned(self, skill_name: str) -> bool:
        return skill_name in self._learned

    def has_equipped(self, skill_name: str) -> bool:
        return skill_name in self._equipped

    @property
    def learned_names(self) -> list[str]:
        return list(self._learned.keys())

    @property
    def equipped_names(self) -> list[str]:
        return list(self._equipped)

    # ══════════════════════════════════════════
    #  顯示
    # ══════════════════════════════════════════

    def summary(self) -> str:
        equipped_str = "、".join(self._equipped) if self._equipped else "（空）"
        learned_str  = "、".join(self._learned.keys()) if self._learned else "（無）"
        return (
            f"裝備技能（{len(self._equipped)}/{self.max_equipped}）：{equipped_str}\n"
            f"已學技能：{learned_str}"
        )
