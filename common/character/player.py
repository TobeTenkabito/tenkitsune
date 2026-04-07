"""
Player
─────────────────────────────────────────────
继承 Combatant，组合 Stats / Inventory / SkillSet / BattleState

修复记录：
  - 补全所有 Stats 代理属性（hp / mp / speed 等）
  - 补全战斗接口（battle_skills / can_act / perform_attack / use_skill）
  - 补全任务接口（check_tasks_for_kill / update_tasks_after_battle）
  - 补全结算接口（reset_medicine_effects / reset_skill_bonuses）
  - 补全背包显示接口（display_inventory）
"""

from __future__ import annotations
import copy

from common.event import (
    EventBus,
    WarningEvent,
    EquipmentEquippedEvent,
    DamageRequestEvent,
    HealRequestEvent,
    BuffRequestEvent,
)
from components.stats       import Stats
from components.inventory   import Inventory
from components.skills      import SkillSet
from components.battle_state import BattleState


class Player:
    def __init__(self, name: str):
        self.name         = name
        self.stats        = Stats(owner=name)
        self.inventory    = Inventory(owner=name)
        self.skill_set    = SkillSet(owner=name)
        self.battle_state = BattleState(owner=name)

        # 装备栏：每个部位只能装一件
        self._equipment: dict[str, object] = {}   # category → item

        # 战斗期间由 BattleEngine 注入
        self.battle       = None
        self.battle_skills: list = []   # BattleEngine._copy_battle_skills 写入

        # 任务列表（由外部系统写入）
        self.accepted_tasks: list = []

        # 战斗期间的临时加成（由药品 / 技能写入，结算时清除）
        self._medicine_effects: dict = {}
        self._skill_bonuses:    dict = {}

    # ══════════════════════════════════════════
    #  Stats 代理属性（BattleEngine 直接访问）
    # ══════════════════════════════════════════

    @property
    def hp(self) -> float:
        return self.stats.hp

    @hp.setter
    def hp(self, value: float) -> None:
        self.stats.hp = value

    @property
    def max_hp(self) -> float:
        return self.stats.max_hp

    @max_hp.setter
    def max_hp(self, value: float) -> None:
        self.stats.max_hp = value

    @property
    def mp(self) -> float:
        return self.stats.mp

    @mp.setter
    def mp(self, value: float) -> None:
        self.stats.mp = value

    @property
    def max_mp(self) -> float:
        return self.stats.max_mp

    @max_mp.setter
    def max_mp(self, value: float) -> None:
        self.stats.max_mp = value

    @property
    def attack(self) -> float:
        base = self.stats.attack
        mod  = self.battle_state.total_buff_modifier("attack") if self.battle else 0.0
        return base + mod

    @property
    def defense(self) -> float:
        base = self.stats.defense
        mod  = self.battle_state.total_buff_modifier("defense") if self.battle else 0.0
        return base + mod

    @property
    def speed(self) -> float:
        return self.stats.speed

    @property
    def crit(self) -> float:
        return self.stats.crit_rate

    @property
    def crit_damage(self) -> float:
        return self.stats.crit_multi

    @property
    def resistance(self) -> float:
        return getattr(self.stats, "resistance", 0.0)

    @property
    def penetration(self) -> float:
        return getattr(self.stats, "penetration", 0.0)

    @property
    def level(self) -> int:
        return self.stats.level

    @property
    def exp(self) -> int:
        return self.stats.exp

    @exp.setter
    def exp(self, value: int) -> None:
        self.stats.exp = value

    @property
    def is_alive(self) -> bool:
        return self.stats.is_alive

    # skills 属性：供 BattleEngine._copy_battle_skills 读取
    @property
    def skills(self) -> list:
        return self.skill_set.get_equipped()

    # ══════════════════════════════════════════
    #  战斗接口（与 Combatant 对齐）
    # ══════════════════════════════════════════

    def can_act(self) -> bool:
        """检查是否能行动（眩晕 / 麻痹）。"""
        return not self.battle_state.is_blocked()

    def take_damage(self, amount: float) -> float:
        """护盾优先吸收，再扣 HP。"""
        remaining = self.battle_state.absorb(amount)
        return self.stats.take_damage(remaining)

    def heal(self, amount: float) -> float:
        return self.stats.heal(amount)

    def gain_exp(self, amount: int) -> None:
        self.stats.gain_exp(amount)

    def perform_attack(self, target) -> None:
        """
        普通攻击：计算伤害后 emit DamageRequestEvent。
        由 CombatHandler 执行实际扣血。
        """
        import random
        damage = self.attack
        is_crit = random.random() < self.crit
        if is_crit:
            damage *= self.crit_damage

        # 防御减伤
        target_def = getattr(target, "defense", 0)
        pen        = self.penetration / 100.0
        effective_def = target_def * (1 - pen)
        final_damage  = max(1.0, damage - effective_def)

        EventBus.emit(DamageRequestEvent(
            source=self.name,
            target=target.name,
            amount=final_damage,
            is_crit=is_crit,
        ))

    def use_skill(self, skill, target) -> None:
        """使用技能，消耗 MP 后委托给 skill.execute()。"""
        cost_mp = skill.cost.get("mp", 0)
        if not self.stats.consume_mp(cost_mp):
            return
        skill.execute(self, target)

    def use_medicine(self, medicine, target) -> None:
        medicine.use(self, target)
        self.inventory.remove(medicine.name, quantity=1)

    def use_product(self, product, target) -> None:
        product.use(self, target)
        self.inventory.remove(product.name, quantity=1)

    def calculate_damage(
        self,
        target,
        base_value: float,
        skill_multiplier: float = 1.0,
        is_skill: bool = False,
    ) -> tuple[float, bool]:
        """
        供 AutoBattleAI._calculate_skill_value 调用。
        返回 (damage, is_crit)。
        """
        import random
        is_crit = random.random() < self.crit
        damage  = base_value * skill_multiplier
        if is_crit:
            damage *= self.crit_damage

        target_def    = getattr(target, "defense", 0)
        pen           = self.penetration / 100.0
        effective_def = target_def * (1 - pen)
        final         = max(1.0, damage - effective_def)
        return final, is_crit

    def update_stats(self) -> None:
        """
        同步属性上限（BattleEngine 每回合调用）。
        装备加成、Buff 加成在 property 里实时计算，
        这里只做 HP/MP 的 clamp。
        """
        self.stats.hp = min(self.stats.hp, self.stats.max_hp)
        self.stats.mp = min(self.stats.mp, self.stats.max_mp)

    # ══════════════════════════════════════════
    #  任务接口
    # ══════════════════════════════════════════

    def check_tasks_for_kill(self, enemy) -> None:
        """
        击杀敌人后检查任务进度。
        注意：QuestHandler 也会通过 DeathEvent 调用 register_kill，
        因此这里只做「任务完成条件检查」，不重复计数。
        """
        for task in list(self.accepted_tasks):
            if task.check_completion(self):
                task.complete(self)

    def update_tasks_after_battle(self) -> None:
        """战斗结束后统一检查所有任务完成状态。"""
        for task in list(self.accepted_tasks):
            if task.check_completion(self):
                task.complete(self)

    # ══════════════════════════════════════════
    #  结算接口（BattleEngine._finalize 调用）
    # ══════════════════════════════════════════

    def reset_medicine_effects(self) -> None:
        """清除战斗中药品的临时加成。"""
        for attr, delta in self._medicine_effects.items():
            if hasattr(self.stats, attr):
                setattr(self.stats, attr, getattr(self.stats, attr) - delta)
        self._medicine_effects.clear()

    def reset_skill_bonuses(self) -> None:
        """清除战斗中技能的临时加成。"""
        for attr, delta in self._skill_bonuses.items():
            if hasattr(self.stats, attr):
                setattr(self.stats, attr, getattr(self.stats, attr) - delta)
        self._skill_bonuses.clear()

    # ══════════════════════════════════════════
    #  背包接口
    # ══════════════════════════════════════════

    def add_to_inventory(self, item, quantity: int = 1) -> bool:
        return self.inventory.add(item, quantity)

    def display_inventory(self) -> None:
        print(self.inventory.summary())

    # ══════════════════════════════════════════
    #  装备接口
    # ══════════════════════════════════════════

    def equip(self, item) -> bool:
        category = getattr(item, "category", None)
        if category is None:
            EventBus.emit(WarningEvent(
                message=f"【{item.name}】没有 category，无法装备"
            ))
            return False

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
        if category not in self._equipment:
            EventBus.emit(WarningEvent(
                message=f"{self.name} 没有装备【{category}】部位"
            ))
            return False
        item = self._equipment.pop(category)
        self.inventory.add(item, quantity=1)
        return True

    def get_equipment(self, category: str) -> object | None:
        return self._equipment.get(category)

    def use_equipment(self, equipment, target=None) -> bool:
        if getattr(equipment, "category", None) != "法宝":
            EventBus.emit(WarningEvent(
                message=f"【{equipment.name}】不是法宝，不能使用"
            ))
            return False
        equipment.use(self, target)
        return True

    # ══════════════════════════════════════════
    #  显示
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

    def __str__(self) -> str:
        return f"Player({self.name}, Lv.{self.level}, HP:{self.hp}/{self.max_hp})"
