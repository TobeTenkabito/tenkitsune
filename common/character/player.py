"""
Player
─────────────────────────────────────────────
繼承 Combatant，組合 Stats / Inventory / SkillSet
battle_state 由 Combatant.__init__ 建立，不重複創建

與舊版的差異：
  - 繼承 Combatant，刪除所有重複方法
  - can_act / take_damage / heal / perform_attack / calculate_damage 全部刪除
    → 繼承 Combatant 版本，自動獲得致盲檢查、AttackEvent、等級壓制、事件路由
  - crit / crit_damage 單位對齊 Combatant（百分比整數）
  - use_skill 覆寫：加入 MP 消耗邏輯
  - use_medicine 覆寫：正確調用 inventory.remove(name)
  - use_equipment 覆寫：返回 bool
  - heal() 刪除，繼承 Combatant 版本走事件路由
  - 護盾吸收移至 CombatHandler 統一處理
"""

from __future__ import annotations

from common.battle.combatant import Combatant
from common.event import (
    EventBus,
    WarningEvent,
    EquipmentEquippedEvent,
)
from components.stats     import Stats
from components.inventory import Inventory
from components.skills    import SkillSet


class Player(Combatant):

    def __init__(self, name: str):
        super().__init__(
            number      = 0,
            name        = name,
            description = "",
            level       = 1,
            hp          = 100.0,
            mp          = 50.0,
            max_hp      = 100.0,
            max_mp      = 50.0,
            attack      = 10.0,
            defense     = 5.0,
            speed       = 10.0,
            crit        = 5.0,      # Combatant 期望百分比整數
            crit_damage = 150.0,    # 同上
            resistance  = 0.0,
            penetration = 0.0,
            skills      = [],
            equipment   = [],
        )

        # ── 玩家獨有組件 ──────────────────────────
        self.stats     = Stats(owner=name)
        self.inventory = Inventory(owner=name)
        self.skill_set = SkillSet(owner=name)
        # battle_state 已由 Combatant.__init__ 建立，不重複創建

        # 裝備欄：每個部位只能裝一件
        self._equipment: dict[str, object] = {}

        # 任務列表（由外部系統寫入）
        self.accepted_tasks: list = []

        # 戰鬥期間的臨時加成（由藥品 / 技能寫入，結算時清除）
        self._medicine_effects: dict = {}
        self._skill_bonuses:    dict = {}

    # ══════════════════════════════════════════
    #  Stats 代理（覆蓋 Combatant 的普通字段）
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
        return self.stats.attack + self.battle_state.total_buff_modifier("attack")

    @property
    def defense(self) -> float:
        return self.stats.defense + self.battle_state.total_buff_modifier("defense")

    @property
    def speed(self) -> float:
        return self.stats.speed

    @property
    def crit(self) -> float:
        # Combatant.calculate_damage 期望百分比整數（5.0 = 5%）
        return self.stats.crit_rate * 100.0

    @property
    def crit_damage(self) -> float:
        # Combatant.calculate_damage 期望百分比整數（150.0 = 150%）
        return self.stats.crit_multi * 100.0

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

    @property
    def skills(self) -> list:
        """供 BattleEngine._copy_battle_skills 讀取。"""
        return self.skill_set.get_equipped()

    # ══════════════════════════════════════════
    #  覆寫：use_skill（加入 MP 消耗）
    # ══════════════════════════════════════════

    def use_skill(self, skill, target) -> None:
        """
        覆寫 Combatant.use_skill。
        在狀態檢查基礎上加入 MP 消耗邏輯。
        """
        if not self.can_act():
            return
        if not self.can_use_skill():
            return
        cost_mp = skill.cost.get("mp", 0)
        if not self.stats.consume_mp(cost_mp):
            return
        skill.use(self, target)

    # ══════════════════════════════════════════
    #  覆寫：use_medicine / use_equipment
    # ══════════════════════════════════════════

    def use_medicine(self, medicine, target) -> None:
        """
        覆寫 Combatant.use_medicine。
        正確調用 inventory.remove(name)（Combatant 版本傳對象，類型有誤）。
        """
        medicine.use(self, target)
        self.inventory.remove(medicine.name, quantity=1)

    def use_product(self, product, target) -> None:
        """使用丹藥 / 煉製品（玩家獨有）。"""
        product.use(self, target)
        self.inventory.remove(product.name, quantity=1)

    def use_equipment(self, equipment, target=None) -> bool:
        """
        覆寫 Combatant.use_equipment，返回 bool。
        只允許使用法寶類裝備。
        """
        if getattr(equipment, "category", None) != "法寶":
            EventBus.emit(WarningEvent(
                message=f"【{equipment.name}】不是法寶，不能使用"
            ))
            return False
        equipment.use(self, target)
        return True

    # ══════════════════════════════════════════
    #  經驗 / 升級
    # ══════════════════════════════════════════

    def gain_exp(self, amount: int) -> None:
        self.stats.gain_exp(amount)

    def update_stats(self) -> None:
        """
        clamp HP/MP 上限（BattleEngine 每回合調用）。
        裝備加成、Buff 加成在 property 裡實時計算，
        這裡只做 HP/MP 的 clamp。
        """
        self.stats.hp = min(self.stats.hp, self.stats.max_hp)
        self.stats.mp = min(self.stats.mp, self.stats.max_mp)

    # ══════════════════════════════════════════
    #  任務接口
    # ══════════════════════════════════════════

    def check_tasks_for_kill(self, enemy) -> None:
        """
        擊殺後檢查任務完成狀態。
        注意：不在此處呼叫 register_kill()，
        擊殺計數統一由 QuestHandler 監聽 DeathEvent 處理，避免雙重計數。
        """
        for task in list(self.accepted_tasks):
            if task.check_completion(self):
                task.complete(self)

    def update_tasks_after_battle(self) -> None:
        """戰鬥結束後統一檢查所有任務完成狀態。"""
        for task in list(self.accepted_tasks):
            if task.check_completion(self):
                task.complete(self)

    # ══════════════════════════════════════════
    #  結算接口（BattleEngine._finalize 調用）
    # ══════════════════════════════════════════

    def reset_medicine_effects(self) -> None:
        """清除戰鬥中藥品的臨時加成。"""
        for attr, delta in self._medicine_effects.items():
            if hasattr(self.stats, attr):
                setattr(self.stats, attr, getattr(self.stats, attr) - delta)
        self._medicine_effects.clear()

    def reset_skill_bonuses(self) -> None:
        """清除戰鬥中技能的臨時加成。"""
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
    #  裝備欄接口（玩家獨有：部位裝備欄）
    # ══════════════════════════════════════════

    def equip(self, item) -> bool:
        """
        裝備物品到部位欄。
        同部位舊裝備自動放回背包。
        """
        category = getattr(item, "category", None)
        if category is None:
            EventBus.emit(WarningEvent(
                message=f"【{item.name}】沒有 category，無法裝備"
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
        """卸下指定部位裝備，放回背包。"""
        if category not in self._equipment:
            EventBus.emit(WarningEvent(
                message=f"{self.name} 沒有裝備【{category}】部位"
            ))
            return False
        item = self._equipment.pop(category)
        self.inventory.add(item, quantity=1)
        return True

    def get_equipment(self, category: str) -> object | None:
        return self._equipment.get(category)

    # ══════════════════════════════════════════
    #  choose_action（實現 Combatant 抽象方法）
    # ══════════════════════════════════════════

    def choose_action(self, engine) -> None:
        """
        玩家回合由 ActionMenu 或 AutoBattleAI 驅動，
        不走 choose_action 路徑，這裡只是滿足接口要求。
        """
        pass

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

    def __str__(self) -> str:
        return (
            f"Player({self.name}, Lv.{self.level}, "
            f"HP:{self.hp:.0f}/{self.max_hp}, "
            f"MP:{self.mp:.0f}/{self.max_mp})"
        )

    def __repr__(self) -> str:
        return f"<Player {self.name} #{str(self.unique_id)[:8]}>"
