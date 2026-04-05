import copy
from common.battle.combatant import Combatant


class Ally(Combatant):
    """
    隊友角色。
    與 Enemy 的區別：
    - 無掉落物 / 經驗值
    - use_equipment 是遍歷所有裝備逐一使用（而非單件）
    - choose_action 目前為簡單 AI，後續可擴展為策略模式
    """

    def __init__(
        self,
        number, name, description, level,
        hp, mp, max_hp, max_mp,
        attack, defense, speed,
        crit, crit_damage,
        resistance, penetration,
        skills=None, equipment=None,
    ):
        super().__init__(
            number, name, description, level,
            hp, mp, max_hp, max_mp,
            attack, defense, speed,
            crit, crit_damage,
            resistance, penetration,
            skills=skills,
            equipment=equipment,
        )

    # ── Ally 特有：use_equipment 遍歷所有裝備 ────────────────
    # 注意：Combatant.use_equipment 是單件法寶，
    # Ally 的行為是把所有裝備都用一遍，語義不同，故覆寫。

    def use_equipment(self, target):
        for equip in self.equipment:
            equip.use(self, target)

    # ── AI 行動 ───────────────────────────────────────────────

    def choose_action(self, engine) -> None:
        """
        隊友簡單 AI：
        - 有技能時 50% 機率使用隨機技能
        - 否則普通攻擊隨機敵人
        後續可替換為策略物件（Strategy Pattern）。
        """
        import random

        alive_enemies = [e for e in engine.enemies if e.is_alive]
        if not alive_enemies:
            return

        if self.battle_skills and random.random() < 0.5:
            skill  = random.choice(self.battle_skills)
            target = random.choice(alive_enemies)
            self.use_skill(skill, target)
        else:
            target = random.choice(alive_enemies)
            self.perform_attack(target)

    # ── deepcopy ─────────────────────────────────────────────

    def __deepcopy__(self, memo):
        new_ally = type(self)(
            self.number,
            self.name,
            self.description,
            self.level,
            self.hp,       # ⚠️ 原始碼此處 hp/max_hp 順序傳反，已修正
            self.mp,
            self.max_hp,
            self.max_mp,
            self.attack,
            self.defense,
            self.speed,
            self.crit,
            self.crit_damage,
            self.resistance,
            self.penetration,
            copy.deepcopy(self.skills,    memo),
            copy.deepcopy(self.equipment, memo),
        )
        self._copy_base_fields(new_ally, memo)
        return new_ally

    # ── 顯示 ──────────────────────────────────────────────────

    def __str__(self):
        return (
            f"Ally({self.name}, Level: {self.level}, "
            f"HP: {self.hp}/{self.max_hp}, MP: {self.mp}/{self.max_mp}, "
            f"ATK: {self.attack}, DEF: {self.defense}, SPD: {self.speed}, "
            f"CRIT: {self.crit}%, CRIT DMG: {self.crit_damage}%, "
            f"RES: {self.resistance}%, PEN: {self.penetration}%)"
        )