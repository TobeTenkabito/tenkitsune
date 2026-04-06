"""
物品系統
─────────────────────────────────────────────
Item 基類 + 子類：
  Equipment  - 裝備 / 法寶
  Medicine   - 藥品
  Material   - 材料
  Skill      - 技能書（戰鬥技能載體）
  Product    - 道具（戰鬥消耗品）
  Warp       - 折躍令（傳送）

與舊版的差異：
  - Buff 類移除，改用 common.module.buff.Buff
  - 所有 print 改為 EventBus.emit
  - 所有直接修改 target.hp/mp 改為 emit DamageRequestEvent / HealRequestEvent
  - 所有 target.add_buff() 改為 emit BuffRequestEvent
  - 所有 target.remove_xxx_buff() 改為 emit BuffRemoveRequestEvent
  - Warp.use() 改為 emit WarpRequestEvent
  - Medicine 的 medicine_xxx 欄位改為 emit StatChangeRequestEvent
  - Equipment.apply_attributes / remove_attributes 保留（裝備時直接改 base 值）
"""

from __future__ import annotations
import random

from common.event import (
    EventBus,
    DamageRequestEvent,
    HealRequestEvent,
    StatChangeRequestEvent,
    BuffRequestEvent,
    BuffRemoveRequestEvent,
    WarpRequestEvent,
    WarningEvent,
    SummonEvent,
)


# ══════════════════════════════════════════════
#  Item 基類
# ══════════════════════════════════════════════

class Item:
    def __init__(self, number, name, description, quality, price, quantity):
        self.number      = number
        self.name        = name
        self.description = description
        self.quality     = quality
        self.price       = price
        self.quantity    = quantity

    def use(self, user, target=None):
        """子類覆寫。"""
        pass

    def __str__(self):
        return f"{self.name} (ID: {self.number}, 數量: {self.quantity})"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"


# ══════════════════════════════════════════════
#  Equipment
# ══════════════════════════════════════════════

class Equipment(Item):
    def __init__(
        self, number, name, description, quality, category,
        price, quantity,
        hp, mp, attack, defense, speed,
        crit, crit_damage, resistance, penetration,
        # 法寶專屬
        target_type=None, target_scope=None,
        effect_duration=None, effect_changes=None, cost=None,
    ):
        super().__init__(number, name, description, quality, price, quantity)
        self.category    = category
        self.hp          = hp
        self.mp          = mp
        self.attack      = attack
        self.defense     = defense
        self.speed       = speed
        self.crit        = crit
        self.crit_damage = crit_damage
        self.resistance  = resistance
        self.penetration = penetration

        if category == "法寶":
            self.target_type     = target_type
            self.target_scope    = target_scope
            self.effect_duration = effect_duration
            self.effect_changes  = effect_changes or {}
            self.cost            = cost or {}

    # ── 裝備屬性（直接修改 base 值，非戰鬥臨時）──────────

    def apply_attributes(self, player) -> None:
        for attr in ("max_hp", "max_mp", "attack", "defense", "speed",
                     "crit", "crit_damage", "resistance", "penetration"):
            item_attr = attr.replace("max_", "")   # max_hp → hp
            delta = getattr(self, item_attr, 0)
            setattr(player, attr, getattr(player, attr) + delta)

    def remove_attributes(self, player) -> None:
        for attr in ("max_hp", "max_mp", "attack", "defense", "speed",
                     "crit", "crit_damage", "resistance", "penetration"):
            item_attr = attr.replace("max_", "")
            delta = getattr(self, item_attr, 0)
            setattr(player, attr, getattr(player, attr) - delta)

    # ── 法寶使用 ──────────────────────────────────────────

    def use(self, user, target=None) -> None:
        if not user.is_alive:
            EventBus.emit(WarningEvent(
                message=f"{user.name} 無法行動，HP 為 0。"
            ))
            return

        if self.category != "法寶":
            EventBus.emit(WarningEvent(
                message=f"【{self.name}】不是法寶，無法使用。"
            ))
            return

        targets = target if isinstance(target, list) else [target]
        for t in targets:
            self._apply_effect(user, t)

    def _apply_effect(self, user, target) -> None:
        # 扣除消耗
        for attr, value in self.cost.items():
            current = getattr(user, attr, 0)
            if current < value:
                EventBus.emit(WarningEvent(
                    message=f"{user.name} 的 {attr} 不足，無法使用法寶【{self.name}】"
                ))
                return
            setattr(user, attr, current - value)

        if not hasattr(target, "name"):
            EventBus.emit(WarningEvent(
                message=f"法寶【{self.name}】目標無效。"
            ))
            return

        for attr, effect_change in self.effect_changes.items():
            if attr == "hp":
                _apply_hp_change(self.name, user, target, effect_change)
            elif attr == "buff":
                _apply_buff_change(self.name, user, target, effect_change)
            else:
                _apply_general_change(self.name, user, target, attr, effect_change)


# ══════════════════════════════════════════════
#  Medicine
# ══════════════════════════════════════════════

class Medicine(Item):
    def __init__(self, number, name, description, quality, price, quantity, effect_changes):
        super().__init__(number, name, description, quality, price, quantity)
        self.effect_changes = effect_changes

    def use(self, user, target=None) -> None:
        if self.quantity <= 0:
            EventBus.emit(WarningEvent(
                message=f"【{self.name}】數量不足，無法使用。"
            ))
            return

        self._apply_effect(user)
        self.quantity -= 1

    def _apply_effect(self, user) -> None:
        for attr, effect in self.effect_changes.items():
            value = _resolve_value(effect, user, user)

            if attr in ("hp", "mp"):
                if value >= 0:
                    EventBus.emit(HealRequestEvent(
                        source=self.name,
                        target=user.name,
                        amount=value,
                        attr=attr,
                    ))
                else:
                    EventBus.emit(DamageRequestEvent(
                        source=self.name,
                        target=user.name,
                        amount=-value,
                        damage_type="true",
                    ))
            else:
                # 非 hp/mp 屬性 → StatChangeRequest（battle scope）
                EventBus.emit(StatChangeRequestEvent(
                    source=self.name,
                    target=user.name,
                    attr=attr,
                    change=value,
                    scope="battle",
                ))


# ══════════════════════════════════════════════
#  Material
# ══════════════════════════════════════════════

class Material(Item):
    pass


# ══════════════════════════════════════════════
#  Skill（技能書）
# ══════════════════════════════════════════════

class Skill(Item):
    def __init__(
        self, number, name, description, quality, price, quantity,
        target_type, target_scope, frequency,
        effect_changes, cost,
    ):
        super().__init__(number, name, description, quality, price, quantity)
        self.target_type   = target_type
        self.target_scope  = target_scope
        self.frequency     = frequency
        self.effect_changes = effect_changes
        self.cost          = cost

    def use(self, user, target=None) -> None:
        if not user.is_alive:
            EventBus.emit(WarningEvent(
                message=f"{user.name} 無法行動，HP 為 0。"
            ))
            return

        # 次數檢查
        if self.frequency is not None:
            if self.frequency <= 0:
                EventBus.emit(WarningEvent(
                    message=f"靈力枯竭，{user.name} 無法使用技能【{self.name}】"
                ))
                return

        # 消耗計算
        for attr, cost_change in self.cost.items():
            cost_val = _resolve_value(cost_change, user, user)
            current  = getattr(user, attr, 0)
            if current < cost_val:
                EventBus.emit(WarningEvent(
                    message=f"{user.name} 的 {attr} 不足，無法使用技能【{self.name}】"
                ))
                return
            setattr(user, attr, current - cost_val)

        # 確定目標
        if self.target_type == "ally" and self.target_scope == "user":
            targets = [user]
        elif self.target_scope == "all":
            targets = self._get_all_targets(user)
        else:
            targets = [target] if not isinstance(target, list) else target

        for t in targets:
            self._apply_effect(user, t)

        if self.frequency is not None:
            self.frequency -= 1

    def _get_all_targets(self, user) -> list:
        if user.battle is None:
            EventBus.emit(WarningEvent(
                message=f"{user.name} 未綁定戰鬥實例，無法取得目標。"
            ))
            return []

        user_type = type(user).__name__
        if self.target_type == "enemy":
            return (
                [user.battle.player] + user.battle.allies
                if user_type in ("Enemy", "Boss")
                else user.battle.enemies
            )
        else:  # ally
            if user_type in ("Enemy", "Boss"):
                return [user] + [
                    e for e in user.battle.enemies
                    if type(e).__name__ in ("Enemy", "Boss")
                ]
            else:
                return [user, user.battle.player] + user.battle.allies

    def _apply_effect(self, user, target) -> None:
        for attr, effect_change in self.effect_changes.items():
            changes = effect_change if isinstance(effect_change, list) else [effect_change]
            for change in changes:
                if attr == "hp":
                    _apply_hp_change(self.name, user, target, change)
                elif attr == "buff":
                    _apply_buff_change(self.name, user, target, [change])
                else:
                    _apply_general_change(self.name, user, target, attr, change)


# ══════════════════════════════════════════════
#  Product（道具）
# ══════════════════════════════════════════════

class Product(Item):
    def __init__(
        self, number, name, description, quality, price, quantity,
        target_type, target_scope, effect_changes,
    ):
        super().__init__(number, name, description, quality, price, quantity)
        self.target_type   = target_type
        self.target_scope  = target_scope
        self.effect_changes = effect_changes

    def use(self, user, target=None, summon_func=None) -> None:
        if self.quantity <= 0:
            EventBus.emit(WarningEvent(
                message=f"【{self.name}】數量不足，無法使用。"
            ))
            return

        self._apply_effect(user, target, summon_func)
        self.quantity -= 1

    def _apply_effect(self, user, target, summon_func=None) -> None:
        for attr, effect_change in self.effect_changes.items():
            if attr == "hp":
                _apply_hp_change(self.name, user, target, effect_change)
            elif attr == "buff":
                _apply_buff_change(self.name, user, target, effect_change)
            elif attr == "summon":
                if summon_func:
                    summon_func(user, effect_change)
                    self.quantity += 1   # 召喚令非一次性
                    EventBus.emit(SummonEvent(
                        summoner=user.name,
                        ally_name=str(effect_change),
                    ))
                else:
                    EventBus.emit(WarningEvent(
                        message=f"【{self.name}】召喚功能未定義。"
                    ))
            else:
                _apply_general_change(self.name, user, target, attr, effect_change)


# ══════════════════════════════════════════════
#  Warp（折躍令）
# ══════════════════════════════════════════════

class Warp(Item):
    def __init__(self, number, name, description, quality, price, quantity, target_map_number):
        super().__init__(number, name, description, quality, price, quantity)
        self.target_map_number = target_map_number

    def use(self, user, target=None) -> None:
        if self.quantity <= 0:
            EventBus.emit(WarningEvent(
                message=f"【{self.name}】數量不足，無法使用。"
            ))
            return

        EventBus.emit(WarpRequestEvent(
            target_map_number=self.target_map_number,
        ))
        # 折躍令可重複使用，數量保持不變


# ══════════════════════════════════════════════
#  共用輔助函數（模組私有）
# ══════════════════════════════════════════════

def _resolve_value(effect_change, user, target) -> float:
    """
    從 effect_change 解析最終數值。
    effect_change 可以是：
      int / float          → 直接使用
      dict with multiplier → base_value * multiplier
      dict with value      → 直接取 value
    """
    if isinstance(effect_change, (int, float)):
        return float(effect_change)

    source    = effect_change.get("source", "user")
    attribute = effect_change.get("attribute", "attack")
    ref       = target if source == "target" else user
    base      = getattr(ref, attribute, 0)

    if "value" in effect_change:
        return float(effect_change["value"])
    return base * effect_change.get("multiplier", 1.0)


def _apply_hp_change(
    item_name: str, user, target, effect_change
) -> None:
    """
    處理 hp 類效果。
    attack/defense 屬性 → calculate_damage → DamageRequestEvent
    其他              → 正值 HealRequestEvent，負值 DamageRequestEvent
    """
    if isinstance(effect_change, dict):
        attribute = effect_change.get("attribute", "")
        if attribute in ("attack", "defense"):
            base_value       = _resolve_value(effect_change, user, target)
            multiplier       = effect_change.get("multiplier", 1.0)
            damage, is_crit  = user.calculate_damage(
                target, base_value,
                skill_multiplier=multiplier, is_skill=True,
            )
            EventBus.emit(DamageRequestEvent(
                source=item_name,
                target=target.name,
                amount=round(damage, 2),
                damage_type="skill",
                skill_multiplier=multiplier,
                is_skill=True,
            ))
            return

    change = _resolve_value(effect_change, user, target)
    if change >= 0:
        EventBus.emit(HealRequestEvent(
            source=item_name,
            target=target.name,
            amount=change,
            attr="hp",
        ))
    else:
        EventBus.emit(DamageRequestEvent(
            source=item_name,
            target=target.name,
            amount=-change,
            damage_type="true",
        ))


def _apply_buff_change(
    item_name: str, user, target, effect_list: list
) -> None:
    """
    處理 buff 類效果列表。
    add  → BuffRequestEvent
    remove → BuffRemoveRequestEvent
    """
    for buff_change in effect_list:
        action = buff_change.get("action")

        if action == "add":
            chance = buff_change.get("chance", 1.0)
            if random.random() > chance:
                return
            EventBus.emit(BuffRequestEvent(
                source=user.name,
                target=target.name,
                buff_name=buff_change["name"],
                buff_type=buff_change["type"],
                duration=buff_change["duration"],
                effect=buff_change.get("effect", {}),
                chance=chance,
            ))

        elif action == "remove":
            remove_type = buff_change.get("type", "")
            remove_name = buff_change.get("name", "")

            if remove_type == "all":
                scope = "all"
            elif remove_name:
                scope = "name"
            else:
                scope = "type"

            EventBus.emit(BuffRemoveRequestEvent(
                source=user.name,
                target=target.name,
                scope=scope,
                buff_name=remove_name,
                buff_type=remove_type,
            ))


def _apply_general_change(
    item_name: str, user, target, attr: str, effect_change
) -> None:
    """
    處理非 hp/buff 的屬性效果。
    emit StatChangeRequestEvent，scope 依目標類型決定。
    """
    change     = _resolve_value(effect_change, user, target)
    target_type = type(target).__name__

    scope = "battle" if target_type in ("Enemy", "Boss") else "battle"

    EventBus.emit(StatChangeRequestEvent(
        source=item_name,
        target=target.name,
        attr=attr,
        change=change,
        scope=scope,
    ))
