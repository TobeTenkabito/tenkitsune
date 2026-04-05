"""
BattleEngine
戰鬥主循環，組裝所有子模組。
所有戰鬥訊息一律透過 EventBus 發送。
"""

import copy

from common.character.player import Player
from common.character.ally   import Ally

from common.battle.turn_manager   import TurnManager
from common.battle.buff_processor import BuffProcessor
from common.battle.drop_processor import DropProcessor
from common.battle.auto_battle    import AutoBattleAI
from common.battle.action         import ActionMenu

from common.event import (
    EventBus,
    TurnStartEvent,
    DeathEvent,
    ExpGainedEvent,
    BattleResultEvent,
    WarningEvent,
)


class BattleEngine:

    def __init__(self, player, allies: list, enemies: list):
        # ── 戰場成員 ──────────────────────────────────────────
        self.player  = player
        self.allies  = [copy.deepcopy(a) for a in allies]
        self.enemies = [copy.deepcopy(e) for e in enemies]

        if not self.player and not self.enemies:
            raise ValueError("沒有玩家或敵人，無法開始戰鬥。")

        # ── 子模組 ────────────────────────────────────────────
        self.turn_manager   = TurnManager()
        self.buff_processor = BuffProcessor()
        self.drop_processor = DropProcessor()
        self.auto_ai        = AutoBattleAI()
        self.action_menu    = ActionMenu()

        # ── 戰鬥狀態 ──────────────────────────────────────────
        self.auto_battle      = False
        self.defeated_enemies = []
        self._turn_count      = 0

        # ── 注入 battle 引用 ──────────────────────────────────
        self._inject_battle_ref()

        # ── 複製戰鬥用技能 ────────────────────────────────────
        self._copy_battle_skills()

        # ── 建立初始回合順序 ──────────────────────────────────
        self.turn_manager.build_order(self.player, self.allies, self.enemies)

    # ── 初始化輔助 ────────────────────────────────────────────

    def _inject_battle_ref(self):
        for p in self._all_participants():
            p.battle = self

    def _copy_battle_skills(self):
        for p in self._all_participants():
            p.battle_skills = [copy.deepcopy(s) for s in p.skills]

    def _all_participants(self) -> list:
        return (
            ([self.player] if self.player else [])
            + self.allies
            + self.enemies
        )

    # ── 主循環 ────────────────────────────────────────────────

    def run(self) -> str:
        """
        執行完整戰鬥。
        返回："win" / "loss"
        """
        status = "ongoing"

        while status == "ongoing":
            self._turn_count += 1

            EventBus.emit(TurnStartEvent(
                turn=self._turn_count,
                order=[p.name for p in self.turn_manager.order],
            ))

            # 1. 處理所有 Buff
            self.buff_processor.apply_buffs(self._all_participants())

            # 2. 同步玩家屬性上限
            if self.player:
                self.player.update_stats()
            self._clamp_hp_mp(self._all_participants())

            # 3. 依回合順序行動
            status = self._run_turn()
            if status != "ongoing":
                break

            # 4. 移除死亡角色 + 更新順序
            self._remove_dead()
            self.turn_manager.update_order(self.player, self.allies, self.enemies)

        # ── 戰鬥結束後處理 ────────────────────────────────────
        self._finalize(status)
        return status

    # ── 回合執行 ──────────────────────────────────────────────

    def _run_turn(self) -> str:
        i = 0
        order = self.turn_manager.order

        while i < len(order):
            participant = order[i]

            if participant.hp <= 0:
                i += 1
                continue

            # 狀態異常計時
            action_state = self.turn_manager.tick_status(participant)
            if action_state in ("stunned", "paralyzed"):
                i += 1
                continue

            # 行動
            result = self._participant_act(participant)

            if result == "back":
                continue   # 不消耗回合，重新選擇

            if result == "end_battle":
                return "win"

            # 行動後遞減沉默 / 致盲
            self.turn_manager.tick_minor_status(participant)

            # 檢查戰鬥狀態
            status = self._check_status()
            if status != "ongoing":
                return status

            i += 1

        return "ongoing"

    def _participant_act(self, participant):
        if isinstance(participant, Player):
            if self.auto_battle:
                self.auto_ai.decide(participant, self)
                return "acted"
            else:
                return self.action_menu.run(participant, self)

        elif isinstance(participant, Ally):
            participant.choose_action(self)
            return "acted"

        else:
            participant.choose_action(self)
            return "acted"

    # ── 狀態檢查 ──────────────────────────────────────────────

    def _check_status(self) -> str:
        player_down  = self.player is None or self.player.hp <= 0
        allies_down  = all(a.hp <= 0 for a in self.allies)
        enemies_down = len(self.enemies) == 0

        if player_down and allies_down:
            return "loss"
        if enemies_down:
            return "win"
        return "ongoing"

    # ── 死亡處理 ──────────────────────────────────────────────

    def _remove_dead(self):
        for enemy in self.enemies[:]:
            if enemy.hp <= 0:
                EventBus.emit(DeathEvent(name=enemy.name, is_enemy=True))

                if self.player:
                    self.player.gain_exp(enemy.exp_drops)
                    EventBus.emit(ExpGainedEvent(
                        player=self.player.name,
                        amount=enemy.exp_drops,
                        total_exp=self.player.exp,
                    ))
                    self.player.check_tasks_for_kill(enemy)

                self.drop_processor.process(self.player, enemy)
                self.defeated_enemies.append(enemy)
                self.enemies.remove(enemy)

        for ally in self.allies[:]:
            if ally.hp <= 0:
                EventBus.emit(DeathEvent(name=ally.name, is_enemy=False))

        self.allies = [a for a in self.allies if a.hp > 0]

        if self.player and self.player.hp <= 0:
            EventBus.emit(DeathEvent(name=self.player.name, is_enemy=False))

    # ── 結算 ──────────────────────────────────────────────────

    def _finalize(self, status: str):
        self.buff_processor.clear_all(self._all_participants())

        if self.player:
            self.player.reset_medicine_effects()
            self.player.reset_skill_bonuses()

        total_exp = sum(e.exp_drops for e in self.defeated_enemies)

        EventBus.emit(BattleResultEvent(
            result=status,
            turn_count=self._turn_count,
            defeated_enemies=[e.name for e in self.defeated_enemies],
            total_exp=total_exp,
        ))

        if status == "win" and self.player:
            self.player.update_tasks_after_battle()
            self.player.display_inventory()

    # ── 輔助 ──────────────────────────────────────────────────

    @staticmethod
    def _clamp_hp_mp(participants: list):
        for p in participants:
            if p.hp > 1.1 * p.max_hp:
                p.hp = 1.1 * p.max_hp
            if p.mp > p.max_mp:
                p.mp = p.max_mp