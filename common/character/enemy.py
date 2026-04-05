import copy
from common.battle.combatant import Combatant


class Enemy(Combatant):
    """
    普通敵人。
    在 Combatant 基礎上增加：掉落物、經驗值、module_object。
    """

    def __init__(
        self,
        number, name, description, level,
        hp, mp, max_hp, max_mp,
        attack, defense, speed,
        crit, crit_damage,
        resistance, penetration,
        drops, chance_drops, exp_drops,
        skills=None,
    ):
        super().__init__(
            number, name, description, level,
            hp, mp, max_hp, max_mp,
            attack, defense, speed,
            crit, crit_damage,
            resistance, penetration,
            skills=skills,
            equipment=[],
        )
        self.drops        = drops
        self.chance_drops = chance_drops if chance_drops else []
        self.exp_drops    = exp_drops

        # 外部 AI 模組，不可深拷貝
        self.module_object = None

    # ── AI 行動 ───────────────────────────────────────────────

    def choose_action(self, engine) -> None:
        """
        普通敵人 AI：
        - 先檢查是否能行動（眩暈 / 麻痹）
        - 有技能時 50% 機率使用隨機技能
        - 否則普通攻擊隨機目標
        """
        import random

        if not self.can_act():
            return

        targets = [engine.player] + engine.allies

        if self.battle_skills and random.random() < 0.5:
            skill  = random.choice(self.battle_skills)
            target = random.choice(targets)
            self.use_skill(skill, target)
        else:
            target = random.choice(targets)
            self.perform_attack(target)

    # ── deepcopy ─────────────────────────────────────────────

    def __deepcopy__(self, memo):
        new_enemy = type(self)(
            self.number,
            self.name,
            self.description,
            self.level,
            self.hp,
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
            copy.deepcopy(self.drops,        memo),
            copy.deepcopy(self.chance_drops, memo),
            self.exp_drops,
            copy.deepcopy(self.skills,       memo),
        )
        self._copy_base_fields(new_enemy, memo)
        new_enemy.module_object = None
        return new_enemy