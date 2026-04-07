"""
BattleEngine
战斗主循环，组装所有子模块。
所有战斗消息一律通过 EventBus 发送。
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

# ── 新增：战斗层 Handler 上下文 ──────────────────────────────
from core.handlers import BattleHandlerContext


class BattleEngine:

    def __init__(self, player, allies: list, enemies: list):
        # ── 战场成员 ──────────────────────────────────────────
        self.player  = player
        self.allies  = [copy.deepcopy(a) for a in allies]
        self.enemies = [copy.deepcopy(e) for e in enemies]

        if not self.player and not self.enemies:
            raise ValueError("没有玩家或敌人，无法开始战斗。")

        # ── 子模块 ────────────────────────────────────────────
        self.turn_manager   = TurnManager()
        self.buff_processor = BuffProcessor()
        self.drop_processor = DropProcessor()
        self.auto_ai        = AutoBattleAI()
        self.action_menu    = ActionMenu()

        # ── 战斗状态 ──────────────────────────────────────────
        self.auto_battle      = False
        self.defeated_enemies = []
        self._turn_count      = 0

        # ── 注入 battle 引用 ──────────────────────────────────
        self._inject_battle_ref()

        # ── 复制战斗用技能 ────────────────────────────────────
        self._copy_battle_skills()

        # ── 建立初始回合顺序 ──────────────────────────────────
        self.turn_manager.build_order(self.player, self.allies, self.enemies)

        # ── 注册战斗层 Handler（修改1：新增）─────────────────
        self._handler_ctx = BattleHandlerContext(self)

    # ── 初始化辅助 ────────────────────────────────────────────

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

    # ── 主循环 ────────────────────────────────────────────────

    def run(self) -> str:
        """
        执行完整战斗。
        返回："win" / "loss"
        """
        status = "ongoing"

        while status == "ongoing":
            self._turn_count += 1

            EventBus.emit(TurnStartEvent(
                turn=self._turn_count,
                order=[p.name for p in self.turn_manager.order],
            ))

            # 1. 处理所有 Buff（含计时递减）
            self.buff_processor.apply_buffs(self._all_participants())

            # 2. 同步玩家属性上限
            if self.player:
                self.player.update_stats()
            self._clamp_hp_mp(self._all_participants())

            # 3. 依回合顺序行动
            status = self._run_turn()
            if status != "ongoing":
                break

            # 4. 移除死亡角色 + 更新顺序
            self._remove_dead()
            self.turn_manager.update_order(self.player, self.allies, self.enemies)

        # ── 战斗结束后处理 ────────────────────────────────────
        self._finalize(status)
        return status

    # ── 回合执行 ──────────────────────────────────────────────

    def _run_turn(self) -> str:
        i = 0
        order = self.turn_manager.order

        while i < len(order):
            participant = order[i]

            if participant.hp <= 0:
                i += 1
                continue

            # 状态异常查询（修改2：删除 tick_minor_status 调用）
            action_state = self.turn_manager.tick_status(participant)
            if action_state in ("stunned", "paralyzed"):
                i += 1
                continue

            # 行动
            result = self._participant_act(participant)

            if result == "back":
                continue

            if result == "end_battle":
                return "win"

            # 修改2：删除 tick_minor_status(participant)
            # 沉默 / 致盲计时已由 buff_processor.apply_buffs()
            # 在每回合开始统一处理，无需在行动后单独递减

            # 检查战斗状态
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

    # ── 状态检查 ──────────────────────────────────────────────

    def _check_status(self) -> str:
        player_down = self.player is None or self.player.hp <= 0
        allies_down = all(a.hp <= 0 for a in self.allies)
        enemies_down = all(e.hp <= 0 for e in self.enemies)  # ← 修复

        if player_down and allies_down:
            return "loss"
        if enemies_down:
            return "win"
        return "ongoing"

    # ── 死亡处理 ──────────────────────────────────────────────

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

                self.drop_processor.process(self.player, enemy)
                self.defeated_enemies.append(enemy)
                self.enemies.remove(enemy)

        for ally in self.allies[:]:
            if ally.hp <= 0:
                EventBus.emit(DeathEvent(name=ally.name, is_enemy=False))

        self.allies = [a for a in self.allies if a.hp > 0]

        if self.player and self.player.hp <= 0:
            EventBus.emit(DeathEvent(name=self.player.name, is_enemy=False))

    # ── 结算 ──────────────────────────────────────────────────

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

        # 修改3：注销战斗层 Handler
        self._handler_ctx.teardown()

        if status == "win" and self.player:
            self.player.update_tasks_after_battle()
            self.player.display_inventory()

    # ── 辅助 ──────────────────────────────────────────────────

    @staticmethod
    def _clamp_hp_mp(participants: list):
        for p in participants:
            if p.hp > 1.1 * p.max_hp:
                p.hp = 1.1 * p.max_hp
            if p.mp > p.max_mp:
                p.mp = p.max_mp
