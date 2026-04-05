import copy
from core.registry import registry
from common.character.enemy import Enemy
from common.event import EventBus, WarningEvent


class Boss(Enemy):
    """
    Boss 繼承 Enemy。
    在 Enemy 基礎上增加：
    - summon_list / logic_module（外部 AI 腳本）
    - equipment（Boss 可以有裝備）
    - buff_immune 旗標：True 時免疫所有 Buff（取代舊版 buffs = None）
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
        self.equipment    = equipment    if equipment    is not None else []
        self.summon_list  = summon_list  if summon_list  is not None else []
        self.logic_module = logic_module

        # Buff 免疫旗標（取代舊版 buffs = None）
        self.buff_immune: bool = False

    # ── Boss 特有：Buff 免疫 ──────────────────────────────────

    def apply_buff_to_state(self, buff) -> None:
        """
        直接施加 Buff 物件到 battle_state。
        buff_immune = True 時拒絕並發送警告。
        """
        if self.buff_immune:
            EventBus.emit(WarningEvent(
                message=f"【{self.name}】修為高深莫測，免疫 Buff【{buff.name}】。"
            ))
            return
        self.battle_state.apply_buff(buff)

    def request_buff(
        self,
        buff_name: str,
        buff_type: str,
        duration: int,
        effect: dict,
        source: str = "",
        chance: float = 1.0,
    ) -> None:
        """覆寫：buff_immune 時直接攔截，不 emit Event。"""
        if self.buff_immune:
            EventBus.emit(WarningEvent(
                message=f"【{self.name}】修為高深莫測，免疫 Buff【{buff_name}】。"
            ))
            return
        super().request_buff(
            buff_name=buff_name,
            buff_type=buff_type,
            duration=duration,
            effect=effect,
            source=source,
            chance=chance,
        )

    def abolish_buffs(self) -> None:
        """
        永久免疫 Buff，並清除當前所有 Buff。
        對應舊版 buffs = None。
        """
        self.battle_state.remove_all_buffs()
        self.buff_immune = True

    def refresh_buffs(self) -> None:
        """恢復 Buff 可用狀態。"""
        self.buff_immune = False

    # ── Boss 特有：召喚 ───────────────────────────────────────

    def summon(self) -> list[Enemy]:
        """
        從 registry 取得 'enemy' category 的模板，
        實例化 summon_list 中的敵人並注入 battle 引用。
        找不到模板時 emit WarningEvent 並跳過。
        """
        summoned = []
        for enemy_id in self.summon_list:
            template = registry.get("enemy", enemy_id)
            if template is None:
                EventBus.emit(WarningEvent(
                    message=f"【{self.name}】召喚失敗：找不到敵人模板 ID={enemy_id}。"
                ))
                continue

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

    # ── AI 行動（委託 logic_module）──────────────────────────

    def choose_action(self, engine) -> None:
        """
        先檢查是否能行動（眩暈 / 麻痹）。
        優先使用 logic_module.boss_logic(boss, engine)。
        沒有 logic_module 時退回普通敵人 AI。
        """
        if not self.can_act():
            return

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
        new_boss.buff_immune  = self.buff_immune
        return new_boss