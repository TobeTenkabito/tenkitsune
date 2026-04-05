"""
Player
─────────────────────────────────────────────
繼承 Combatant，組合 Stats / Inventory / SkillSet / BattleState
"""

from __future__ import annotations
from common.event import EventBus, WarningEvent, EquipmentEquippedEvent
from components.stats import Stats
from components.inventory import Inventory
from components.skills import SkillSet
from components.battle_state import BattleState


class Player:
    def __init__(self, name: str):
        self.name         = name
        self.stats        = Stats(owner=name)
        self.inventory    = Inventory(owner=name)
        self.skill_set    = SkillSet(owner=name)
        self.battle_state = BattleState(owner=name)

        # 裝備欄：每個部位只能裝一件
        self._equipment: dict[str, object] = {}   # category → item

    # ══════════════════════════════════════════
    #  裝備
    # ══════════════════════════════════════════

    def equip(self, item) -> bool:
        """
        裝備物品。
        物品需有 .category 與 .name 屬性。
        """
        category = getattr(item, "category", None)
        if category is None:
            EventBus.emit(WarningEvent(message=f"【{item.name}】沒有 category，無法裝備"))
            return False

        # 先卸下同部位舊裝備
        if category in self._equipment:
            old = self._equipment[category]
            self.inventory.add(old, quantity=1)

        self._equipment[category] = item
        EventBus.emit(EquipmentEquippedEvent(
            player=self.name,
            equipment_name=item.name,
            category=category,
        ))
        return True

    def unequip(self, category: str) -> bool:
        """卸下指定部位的裝備，放回背包。"""
        if category not in self._equipment:
            EventBus.emit(WarningEvent(message=f"{self.name} 沒有裝備【{category}】部位"))
            return False
        item = self._equipment.pop(category)
        self.inventory.add(item, quantity=1)
        return True

    def get_equipment(self, category: str) -> object | None:
        return self._equipment.get(category)

    def use_item(self, item_name: str, target=None) -> bool:
        """從背包取出並使用物品。"""
        slot = self.inventory.get(item_name)
        if slot is None:
            EventBus.emit(WarningEvent(message=f"{self.name} 背包中沒有【{item_name}】"))
            return False
        slot.item.use(self, target)
        self.inventory.remove(item_name, quantity=1)
        return True

    def use_equipment(self, equipment, target=None) -> bool:
        """使用法寶類裝備。"""
        if getattr(equipment, "category", None) != "法寶":
            EventBus.emit(WarningEvent(message=f"【{equipment.name}】不是法寶，不能使用"))
            return False
        equipment.use(self, target)
        return True

    # ══════════════════════════════════════════
    #  便捷代理
    # ══════════════════════════════════════════

    @property
    def hp(self) -> float:
        return self.stats.hp

    @property
    def is_alive(self) -> bool:
        return self.stats.is_alive

    def take_damage(self, amount: float) -> float:
        amount = self.battle_state.absorb(amount)
        return self.stats.take_damage(amount)

    def heal(self, amount: float) -> float:
        return self.stats.heal(amount)

    # ══════════════════════════════════════════
    #  顯示
    # ══════════════════════════════════════════

    def summary(self) -> str:
        lines = [
            f"{'─'*40}",
            f"  {self.name}",
            f"{'─'*40}",
            self.stats.summary(),
            self.skill_set.summary(),
            self.inventory.summary(),
            self.battle_state.summary(),
            f"{'─'*40}",
        ]
        return "\n".join(lines)
