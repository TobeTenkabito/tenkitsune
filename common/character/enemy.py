import copy
import uuid
from common.battle.combatant import Combatant


class Enemy(Combatant):
    """
    普通敵人。
    在 Combatant 基礎上增加：掉落物、經驗值、唯一ID、module_object。
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
            equipment=[],   # Enemy 無裝備欄
        )
        self.drops        = drops
        self.chance_drops = chance_drops if chance_drops else []
        self.exp_drops    = exp_drops

        # module_object 是不可深拷貝的外部模組，單獨處理
        self.module_object = None

    # ── AI 行動（子類可覆寫）─────────────────────────────────

    def choose_action(self, engine) -> None:
        """
        普通敵人 AI：
        - 有技能時 50% 機率使用隨機技能
        - 否則普通攻擊隨機目標
        目前 Enemy 沒有專屬邏輯，直接執行，不返回 Action 物件。
        後續接入 Action 系統時再封裝。
        """
        import random

        # 確定可攻擊的目標陣營
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
        # 公共字段統一由基類方法處理
        self._copy_base_fields(new_enemy, memo)
        # module_object 不可深拷貝，置 None
        new_enemy.module_object = None
        return new_enemy
