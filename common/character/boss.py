import copy
import random
from library.enemy_library import enemy_library
from common.character.enemy import Enemy
from common.battle.combatant import Combatant


class Boss(Enemy):
    """
    Boss 繼承 Enemy。
    在 Enemy 基礎上增加：
    - summon_list / logic_module（外部 AI 腳本）
    - equipment（Boss 可以有裝備）
    - buffs 可被 abolish（置 None），代表「修為高深莫測」
    """

    def __init__(
        self,
        number, name, description, level,
        hp, mp, max_hp, max_mp,
        attack, defense, speed,
        crit, crit_damage,
        resistance, penetration,
        drops, chance_drops, exp_drops,
        skills=None, equipment=None,
        summon_list=None, logic_module=None,
    ):
        super().__init__(
            number, name, description, level,
            hp, mp, max_hp, max_mp,
            attack, defense, speed,
            crit, crit_damage,
            resistance, penetration,
            drops, chance_drops, exp_drops,
            skills=skills,
        )
        # Boss 覆寫 equipment（Enemy 預設為空列表）
        self.equipment   = equipment   if equipment   is not None else []
        self.summon_list = summon_list if summon_list is not None else []
        self.logic_module = logic_module

    # ── Boss 特有：召喚 ───────────────────────────────────────

    def summon(self) -> list[Enemy]:
        """從 enemy_library 實例化 summon_list 中的敵人，注入 battle 引用。"""
        summoned = []
        for enemy_id in self.summon_list:
            template = enemy_library[enemy_id]
            new_enemy = Enemy(
                number      = template.number,
                name        = template.name,
                description = template.description,
                level       = template.level,
                hp          = template.hp,
                mp          = template.mp,
                max_hp      = template.max_hp,
                max_mp      = template.max_mp,
                attack      = template.attack,
                defense     = template.defense,
                speed       = template.speed,
                crit        = template.crit,
                crit_damage = template.crit_damage,
                resistance  = template.resistance,
                penetration = template.penetration,
                drops       = copy.deepcopy(template.drops),
                chance_drops= copy.deepcopy(template.chance_drops),
                exp_drops   = template.exp_drops,
                skills      = copy.deepcopy(template.skills),
            )
            new_enemy.battle = self.battle
            summoned.append(new_enemy)
        return summoned

    # ── Boss 特有：Buff 廢除 ──────────────────────────────────

    def add_buff(self, new_buff):
        """buffs 為 None 時代表此 Boss 免疫 Buff。"""
        if self.buffs is None:
            print("该boss修为高深莫测，无法被添加buff")
            return
        super().add_buff(new_buff)

    def remove_buff(self, buff_name=None, buff_type=None):
        if self.buffs is None:
            return
        super().remove_buff(buff_name=buff_name, buff_type=buff_type)

    def remove_all_buffs(self):
        if self.buffs is None:
            return
        super().remove_all_buffs()

    def abolish_buffs(self):
        """永久免疫 Buff（置 None）。"""
        self.buffs = None

    def refresh_buffs(self):
        """恢復 Buff 可用狀態。"""
        self.buffs = []

    # ── AI 行動（委託 logic_module）──────────────────────────

    def choose_action(self, engine) -> None:
        """
        優先使用 logic_module.boss_logic(boss, battle)。
        沒有 logic_module 時退回普通敵人 AI。
        """
        if self.logic_module:
            self.logic_module.boss_logic(self, engine)
        else:
            super().choose_action(engine)

    # ── deepcopy ─────────────────────────────────────────────

    def __deepcopy__(self, memo):
        new_boss = type(self)(
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
            copy.deepcopy(self.equipment,    memo),
            self.summon_list,    # 召喚列表不深拷貝（模板引用）
            # logic_module 是外部模組，不深拷貝
        )
        self._copy_base_fields(new_boss, memo)
        new_boss.logic_module = self.logic_module
        # buffs 可能是 None（abolish 狀態），_copy_base_fields 已處理正常情況
        # 但若原本是 None，需要覆寫回來
        if self.buffs is None:
            new_boss.buffs = None
        return new_boss
