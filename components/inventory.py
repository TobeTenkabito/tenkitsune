"""
背包組件
─────────────────────────────────────────────
管理物品的增刪查，支援堆疊與上限控制
"""

from __future__ import annotations
from dataclasses import dataclass, field
from common.event import EventBus, WarningEvent, ItemAddedEvent, ItemRemovedEvent


# ══════════════════════════════════════════════
#  背包槽
# ══════════════════════════════════════════════

@dataclass
class InventorySlot:
    item: object          # 任意 item 物件
    quantity: int = 1


# ══════════════════════════════════════════════
#  背包
# ══════════════════════════════════════════════

class Inventory:
    def __init__(self, capacity: int = 50, owner: str = "unknown"):
        self.capacity = capacity
        self.owner    = owner
        self._slots: dict[str, InventorySlot] = {}   # key = item.name

    # ══════════════════════════════════════════
    #  新增
    # ══════════════════════════════════════════

    def add(self, item, quantity: int = 1) -> bool:
        """
        新增物品。
        回傳 True 表示成功，False 表示背包已滿。
        """
        name = item.name
        if name in self._slots:
            self._slots[name].quantity += quantity
            EventBus.emit(ItemAddedEvent(item_name=name, quantity=quantity, is_new=False))
            return True

        if len(self._slots) >= self.capacity:
            EventBus.emit(WarningEvent(message=f"{self.owner} 背包已滿，無法放入【{name}】"))
            return False

        self._slots[name] = InventorySlot(item=item, quantity=quantity)
        EventBus.emit(ItemAddedEvent(item_name=name, quantity=quantity, is_new=True))
        return True

    # ══════════════════════════════════════════
    #  移除
    # ══════════════════════════════════════════

    def remove(self, item_name: str, quantity: int = 1) -> bool:
        """
        移除物品。
        回傳 True 表示成功，False 表示數量不足。
        """
        if item_name not in self._slots:
            EventBus.emit(WarningEvent(message=f"{self.owner} 背包中沒有【{item_name}】"))
            return False

        slot = self._slots[item_name]
        if slot.quantity < quantity:
            EventBus.emit(WarningEvent(
                message=f"{self.owner}【{item_name}】數量不足（需要 {quantity}，剩餘 {slot.quantity}）"
            ))
            return False

        slot.quantity -= quantity
        if slot.quantity == 0:
            del self._slots[item_name]

        EventBus.emit(ItemRemovedEvent(item_name=item_name, quantity=quantity))
        return True

    # ══════════════════════════════════════════
    #  查詢
    # ══════════════════════════════════════════

    def get(self, item_name: str) -> InventorySlot | None:
        return self._slots.get(item_name)

    def has(self, item_name: str, quantity: int = 1) -> bool:
        slot = self._slots.get(item_name)
        return slot is not None and slot.quantity >= quantity

    def count(self, item_name: str) -> int:
        slot = self._slots.get(item_name)
        return slot.quantity if slot else 0

    @property
    def is_full(self) -> bool:
        return len(self._slots) >= self.capacity

    @property
    def all_items(self) -> list[tuple[str, int]]:
        """回傳 [(item_name, quantity), ...]"""
        return [(name, slot.quantity) for name, slot in self._slots.items()]

    # ══════════════════════════════════════════
    #  顯示
    # ══════════════════════════════════════════

    def summary(self) -> str:
        if not self._slots:
            return "背包是空的。"
        lines = [f"背包（{len(self._slots)}/{self.capacity}）："]
        for name, slot in self._slots.items():
            lines.append(f"  {name} × {slot.quantity}")
        return "\n".join(lines)
