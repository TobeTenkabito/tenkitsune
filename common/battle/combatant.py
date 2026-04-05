"""
所有參戰者的共同基類。
Player / Enemy / Boss / Ally 都繼承此類。
純數據 + 通用戰鬥方法，不含任何 IO 或 AI 邏輯。
所有訊息一律透過 EventBus 發送。

與舊版的差異：
  - dizzy_rounds / paralysis_rounds / silence_rounds / blind_rounds 移除
    → 狀態異常統一由 BattleState 管理
  - buffs: list 移除
    → 改用 self.battle_state: BattleState
  - take_damage() / heal() 不直接修改 hp
    → emit DamageRequestEvent / HealRequestEvent，由監聽器執行
  - perform_attack() 不直接扣血
    → emit DamageRequestEvent
  - add_buff() / remove_buff() 系列移除
    → 改用 self.battle_state.apply_buff() / remove_buff()
    → 外部請求透過 BuffRequestEvent / BuffRemoveRequestEvent
"""

from __future__ import annotations
import copy
import uuid
import random

from common.event import (
    EventBus,
    AttackEvent,
    MissEvent,
    DamageRequestEvent,
    HealRequestEvent,
    BuffRequestEvent,
    BuffRemoveRequestEvent,
    WarningEvent,
)
from components.battle_state import BattleState


class Combatant:

    # ── 初始化 ──────────────────────────────────────────────

    def __init__(
        self,
        number, name, description, level,
        hp, mp, max_hp, max_mp,
        attack, defense, speed,
        crit, crit_damage,
        resistance, penetration,
        skills=None, equipment=None,
    ):
        self.number      = number
        self.name        = name
        self.description = description
        self.level       = level

        self.hp      = hp
        self.mp      = mp
        self.max_hp  = max_hp
        self.max_mp  = max_mp

        self.attack      = attack
        self.defense     = defense
        self.speed       = speed
        self.crit        = crit          # 百分比，如 15 代表 15%
        self.crit_damage = crit_damage   # 百分比，如 150 代表 150%
        self.resistance  = resistance
        self.penetration = penetration

        self.skills    = skills    if skills    is not None else []
        self.equipment = equipment if equipment is not None else []

        # 戰鬥中的技能副本（由 BattleEngine 初始化）
        self.battle_skills: list = []

        # 戰鬥狀態（Buff / 狀態異常 / 護盾）
        self.battle_state = BattleState(owner=name)

        # 持續效果（舊版相容，逐步遷移中）
        self.sustained_effects: list = []

        # 由 BattleEngine 注入，構造函數不傳遞
        self.battle = None

        # 唯一 ID（區分同名實例）
        self.unique_id = uuid.uuid4()

    # ── 狀態判斷 ────────────────────────────────────────────

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def can_act(self) -> bool:
        """
        檢查是否能行動（眩暈 / 麻痹）。
        同時發送 StatusBlockedActionEvent 通知。
        """
        return not self.battle_state.check_and_emit_blocked()

    def can_use_skill(self) -> bool:
        """檢查是否能使用技能（沉默）。"""
        if self.battle_state.has_status("silenced"):
            return not self.battle_state.check_and_emit_blocked()
        return True

    def can_attack(self) -> bool:
        """檢查是否能普通攻擊（致盲）。"""
        if self.battle_state.has_status("blinded"):
            return not self.battle_state.check_and_emit_blocked()
        return True

    # ── 傷害計算 ────────────────────────────────────────────

    def calculate_damage(
        self, target: "Combatant", base_value: float,
        skill_multiplier: float = 1.0, is_skill: bool = False,
    ) -> tuple[float, bool]:
        """
        計算最終傷害值，不修改任何狀態。
        回傳 (final_damage, is_critical)。
        """
        is_critical     = random.random() < self.crit / 100.0
        crit_multiplier = self.crit_damage / 100.0 if is_critical else 1.0

        theoretical_damage = base_value * skill_multiplier * crit_multiplier

        level_difference  = self.level - target.level
        level_suppression = self._calc_level_suppression(level_difference)

        final_damage = (
            (theoretical_damage - target.defense)
            * (1 + (self.penetration - target.resistance) / 100.0)
            * level_suppression
            * random.randint(900, 1100) / 1000
        )

        # 保底傷害
        final_damage = max(0.05 * self.attack, final_damage)

        return final_damage, is_critical

    @staticmethod
    def _calc_level_suppression(diff: int) -> float:
        thresholds = [
            (50,  1.5), (40,  1.4), (30,  1.3), (20,  1.2), (10,  1.1),
            (-9,  1.0),
            (-19, 0.9), (-29, 0.8), (-39, 0.7), (-49, 0.6),
        ]
        for threshold, multiplier in thresholds:
            if diff >= threshold:
                return multiplier
        return 0.5

    # ── 核心戰鬥方法 ────────────────────────────────────────

    def perform_attack(self, target: "Combatant") -> float | None:
        """
        執行普通攻擊。
        不直接扣血，emit DamageRequestEvent 由監聽器處理。
        致盲時 emit MissEvent 並回傳 None。
        """
        if not self.is_alive:
            EventBus.emit(WarningEvent(
                message=f"{self.name} 無法行動，HP 為 0。"
            ))
            return None

        if not self.can_attack():
            EventBus.emit(MissEvent(
                attacker=self.name,
                target=target.name,
            ))
            return None

        damage, is_critical = self.calculate_damage(target, self.attack)

        EventBus.emit(AttackEvent(
            attacker=self.name,
            target=target.name,
            damage=round(damage, 2),
            is_critical=is_critical,
        ))
        EventBus.emit(DamageRequestEvent(
            source=self.name,
            target=target.name,
            amount=round(damage, 2),
            damage_type="physical",
        ))

        return damage

    def take_damage(self, amount: float, damage_type: str = "physical") -> None:
        """
        請求承受傷害。
        不直接修改 hp，emit DamageRequestEvent 由監聽器執行。
        """
        EventBus.emit(DamageRequestEvent(
            source="direct",
            target=self.name,
            amount=amount,
            damage_type=damage_type,
        ))

    def heal(self, amount: float, attr: str = "hp") -> None:
        """
        請求治療。
        不直接修改 hp/mp，emit HealRequestEvent 由監聽器執行。
        """
        EventBus.emit(HealRequestEvent(
            source="direct",
            target=self.name,
            amount=amount,
            attr=attr,
        ))

    def use_skill(self, skill, target) -> None:
        if not self.can_act():
            return
        if not self.can_use_skill():
            return

        if skill.target_scope == "all":
            targets = (
                self.battle.enemies
                if skill.target_type == "enemy"
                else [self] + self.battle.allies
            )
        else:
            targets = target

        skill.use(self, targets)

    def use_equipment(self, equipment, target) -> None:
        if equipment.category == "法寶":
            equipment.use(self, target)
        else:
            EventBus.emit(WarningEvent(
                message=f"{equipment.name} 不是法寶，不能使用。"
            ))

    def use_medicine(self, medicine, target) -> None:
        if medicine.quantity > 0:
            medicine.use(self, target)
            if medicine.quantity == 0 and hasattr(self, "inventory"):
                self.inventory.remove(medicine)
        else:
            EventBus.emit(WarningEvent(
                message=f"{medicine.name} 數量不足，無法使用。"
            ))

    # ── Buff 代理 ────────────────────────────────────────────
    #
    #  直接操作（Engine / 技能內部）：
    #    self.battle_state.apply_buff(buff_obj)
    #    self.battle_state.remove_buff("buff_name")
    #
    #  外部請求（物品 / 技能 emit）：
    #    EventBus.emit(BuffRequestEvent(...))
    #    EventBus.emit(BuffRemoveRequestEvent(...))
    #
    #  以下兩個方法保留給需要從 Combatant 層直接 emit 的情境。

    def request_buff(
        self,
        buff_name: str,
        buff_type: str,
        duration: int,
        effect: dict,
        source: str = "",
        chance: float = 1.0,
    ) -> None:
        """透過 Event 請求施加 Buff（由監聽器路由到 battle_state）。"""
        EventBus.emit(BuffRequestEvent(
            source=source or self.name,
            target=self.name,
            buff_name=buff_name,
            buff_type=buff_type,
            duration=duration,
            effect=effect,
            chance=chance,
        ))

    def request_remove_buff(
        self,
        scope: str = "name",
        buff_name: str = "",
        buff_type: str = "",
    ) -> None:
        """透過 Event 請求移除 Buff（由監聽器路由到 battle_state）。"""
        EventBus.emit(BuffRemoveRequestEvent(
            source=self.name,
            target=self.name,
            scope=scope,
            buff_name=buff_name,
            buff_type=buff_type,
        ))

    # ── 多態接口（子類必須實現）────────────────────────────

    def choose_action(self, engine) -> None:
        raise NotImplementedError(
            f"{self.__class__.__name__} 未實現 choose_action()"
        )

    # ── deepcopy ────────────────────────────────────────────

    def _copy_base_fields(self, new_obj: "Combatant", memo: dict) -> None:
        """
        子類 __deepcopy__ 呼叫，複製 Combatant 層的所有欄位。
        battle_state 深拷貝，battle 淺引用（Engine 重新注入）。
        """
        new_obj.battle_state      = copy.deepcopy(self.battle_state, memo)
        new_obj.sustained_effects = copy.deepcopy(self.sustained_effects, memo)
        new_obj.battle_skills     = copy.deepcopy(self.battle_skills, memo)
        new_obj.battle            = self.battle   # 淺引用，Engine 重新注入
        new_obj.unique_id         = uuid.uuid4()  # 新實例給新 ID

    # ── 顯示 ────────────────────────────────────────────────

    def __str__(self) -> str:
        return (
            f"{self.name} (Lv.{self.level}) "
            f"HP:{self.hp:.0f}/{self.max_hp} "
            f"MP:{self.mp:.0f}/{self.max_mp}"
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} #{str(self.unique_id)[:8]}>"
