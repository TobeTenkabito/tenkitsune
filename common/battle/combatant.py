"""
所有參戰者的共同基類。
Player / Enemy / Boss / Ally 都繼承此類。
純數據 + 通用戰鬥方法，不含任何 IO 或 AI 邏輯。
所有訊息一律透過 BattleEventBus 發送。
"""

import copy
import uuid
import random

from common.battle.event import (
    BattleEventBus,
    AttackEvent,
    MissEvent,
    BuffAppliedEvent,
    BuffExpiredEvent,
    StatusBlockedActionEvent,
    WarningEvent,
)


class Combatant:

    # ── 初始化 ────────────────────────────────────────────────

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

        # 狀態效果
        self.dizzy_rounds     = 0
        self.paralysis_rounds = 0
        self.silence_rounds   = 0
        self.blind_rounds     = 0
        self.sustained_effects: list = []
        self.buffs: list = []

        # 由 BattleEngine 注入，構造函數不傳遞
        self.battle = None

        # 唯一 ID（區分同名實例）
        self.unique_id = uuid.uuid4()

    # ── 狀態判斷 ──────────────────────────────────────────────

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def can_use_skill(self) -> bool:
        if self.silence_rounds > 0:
            BattleEventBus.emit(StatusBlockedActionEvent(
                target=self.name,
                status="silenced",
                rounds_remaining=self.silence_rounds,
            ))
            return False
        return True

    # ── 傷害計算 ──────────────────────────────────────────────

    def calculate_damage(
        self, target, base_value,
        skill_multiplier=1.0, is_skill=False
    ) -> float:
        # 暴擊判定
        is_critical     = random.random() < self.crit / 100.0
        crit_multiplier = self.crit_damage / 100.0 if is_critical else 1.0

        # 理論傷害
        theoretical_damage = base_value * skill_multiplier * crit_multiplier

        # 等級壓制
        level_difference  = self.level - target.level
        level_suppression = self._calc_level_suppression(level_difference)

        # 最終傷害
        final_damage = (
            (theoretical_damage - target.defense)
            * (1 + (self.penetration - target.resistance) / 100.0)
            * level_suppression
            * random.randint(900, 1100) / 1000
        )

        # 保底傷害
        final_damage = max(0.05 * self.attack, final_damage)

        # 暴擊事件由 perform_attack / use_skill 層發送，
        # 這裡只返回數值 + 暴擊標記，避免重複發送。
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

    # ── 核心戰鬥方法 ──────────────────────────────────────────

    def perform_attack(self, target) -> float | None:
        if not self.is_alive:
            BattleEventBus.emit(WarningEvent(
                message=f"{self.name} 無法行動，HP 為 0。"
            ))
            return None

        if self.blind_rounds > 0:
            BattleEventBus.emit(StatusBlockedActionEvent(
                target=self.name,
                status="blinded",
                rounds_remaining=self.blind_rounds,
            ))
            return None

        damage, is_critical = self.calculate_damage(target, self.attack)
        target.hp -= damage

        BattleEventBus.emit(AttackEvent(
            attacker=self.name,
            target=target.name,
            damage=round(damage, 2),
            is_critical=is_critical,
        ))
        return damage

    def use_skill(self, skill, target):
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

    def use_equipment(self, equipment, target):
        if equipment.category == "法宝":
            equipment.use(self, target)
        else:
            BattleEventBus.emit(WarningEvent(
                message=f"{equipment.name} 不是法寶，不能使用。"
            ))

    def use_medicine(self, medicine, target):
        if medicine.quantity > 0:
            medicine.use(self, target)
            if medicine.quantity == 0 and hasattr(self, "inventory"):
                self.inventory.remove(medicine)
        else:
            BattleEventBus.emit(WarningEvent(
                message=f"{medicine.name} 數量不足，無法使用。"
            ))

    # ── Buff 系統 ─────────────────────────────────────────────

    def add_buff(self, new_buff):
        existing = next((b for b in self.buffs if b.name == new_buff.name), None)
        if existing:
            existing.duration = new_buff.original_duration
            BattleEventBus.emit(BuffAppliedEvent(
                target=self.name,
                buff_name=existing.name,
                duration=existing.duration,
            ))
        else:
            new_buff.target = self
            self.buffs.append(new_buff)
            BattleEventBus.emit(BuffAppliedEvent(
                target=self.name,
                buff_name=new_buff.name,
                duration=new_buff.duration,
            ))
            new_buff.apply_effect()

    def remove_buff(self, buff_name=None, buff_type=None):
        if buff_name:
            removed = [b for b in self.buffs if b.name == buff_name]
            self.buffs = [b for b in self.buffs if b.name != buff_name]
            for b in removed:
                b.remove_effect()
                BattleEventBus.emit(BuffExpiredEvent(
                    target=self.name,
                    buff_name=b.name,
                ))
        elif buff_type:
            removed = [b for b in self.buffs if b.buff_type == buff_type]
            self.buffs = [b for b in self.buffs if b.buff_type != buff_type]
            for b in removed:
                b.remove_effect()
                BattleEventBus.emit(BuffExpiredEvent(
                    target=self.name,
                    buff_name=b.name,
                ))
        else:
            BattleEventBus.emit(WarningEvent(
                message="未指定 buff 名字或類型，無法移除。"
            ))

    def remove_buffs_by_type(self, buff_type):
        to_remove = [b for b in self.buffs if b.buff_type == buff_type]
        for buff in to_remove:
            buff.remove_effect()
            self.buffs.remove(buff)
            BattleEventBus.emit(BuffExpiredEvent(
                target=self.name,
                buff_name=buff.name,
            ))

    def remove_all_buffs(self):
        for buff in self.buffs:
            buff.remove_effect()
        self.buffs.clear()

    # ── 多態接口（子類必須實現）──────────────────────────────

    def choose_action(self, engine) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} 未實現 choose_action()")

    # ── deepcopy 公共部分 ─────────────────────────────────────

    def _copy_base_fields(self, new_obj, memo):
        new_obj.dizzy_rounds      = self.dizzy_rounds
        new_obj.paralysis_rounds  = self.paralysis_rounds
        new_obj.silence_rounds    = self.silence_rounds
        new_obj.blind_rounds      = self.blind_rounds
        new_obj.sustained_effects = copy.deepcopy(self.sustained_effects, memo)
        new_obj.buffs             = copy.deepcopy(self.buffs, memo)
        new_obj.battle            = self.battle   # 淺引用，Engine 重新注入
        new_obj.unique_id         = uuid.uuid4()  # 新實例給新 ID

    # ── 顯示 ──────────────────────────────────────────────────

    def __str__(self):
        return (
            f"{self.name} (Lv.{self.level}) "
            f"HP:{self.hp:.0f}/{self.max_hp} "
            f"MP:{self.mp:.0f}/{self.max_mp}"
        )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} #{str(self.unique_id)[:8]}>"
