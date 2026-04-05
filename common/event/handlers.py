"""
Handler 基類與內建實作
─────────────────────────────────────────────
BattleHandler          : 基類，子類 override on_xxx
ConsoleBattleHandler   : 終端輸出
SilentBattleHandler    : 靜默（測試用）
JsonCollectorHandler   : JSON 收集（WebSocket / 前端用）
"""

from __future__ import annotations
from common.event.bus import BattleEvent, _to_snake
from common.event.battle import (
    TurnStartEvent, TurnOrderUpdatedEvent,
    AttackEvent, SkillUsedEvent, MissEvent,
    StatusAppliedEvent, StatusBlockedActionEvent, StatusExpiredEvent,
    BuffAppliedEvent, BuffTickEvent, BuffExpiredEvent,
    DeathEvent, ExpGainedEvent, DropEvent,
    BattleResultEvent, SummonEvent,
)
from common.event.system.__init__ import WarningEvent, HealEvent
from common.event.player import (
    LevelUpEvent, StatChangedEvent,
    ItemAddedEvent, ItemRemovedEvent,
    SkillEquippedEvent, SkillRemovedEvent, EquipmentEquippedEvent,
)
from common.event.quest import (
    TaskProgressEvent, TaskCompletedEvent,
    NpcInteractionEvent, DungeonProgressEvent,
)


# ══════════════════════════════════════════════
#  Handler 基類
# ══════════════════════════════════════════════

class BattleHandler:
    def handle(self, event: BattleEvent) -> None:
        method = f"on_{_to_snake(event.__class__.__name__)}"
        handler = getattr(self, method, self.on_unhandled)
        handler(event)

    def on_unhandled(self, event: BattleEvent) -> None:
        pass


# ══════════════════════════════════════════════
#  終端輸出 Handler
# ══════════════════════════════════════════════

class ConsoleBattleHandler(BattleHandler):

    # ── 回合 ──────────────────────────────────

    def on_turn_start_event(self, e: TurnStartEvent):
        print(f"\n{'━'*40}")
        print(f"  第 {e.turn} 回合開始！")
        print(f"  回合順序：{' → '.join(e.order)}")
        print(f"{'━'*40}")

    def on_turn_order_updated_event(self, e: TurnOrderUpdatedEvent):
        print(f"[回合] 更新順序：{' → '.join(e.order)}")

    # ── 行動 ──────────────────────────────────

    def on_attack_event(self, e: AttackEvent):
        crit = "【暴擊】" if e.is_critical else ""
        print(f"[攻擊] {e.attacker} → {e.target}  {crit}造成 {e.damage:.0f} 傷害")

    def on_skill_used_event(self, e: SkillUsedEvent):
        targets = "、".join(e.targets)
        print(f"[技能] {e.user} 對 {targets} 使用了【{e.skill_name}】")
        for eff in e.effects:
            sign = "+" if eff["change"] > 0 else ""
            print(f"       {eff['attr']} {sign}{eff['change']:.0f}")

    def on_miss_event(self, e: MissEvent):
        print(f"[攻擊] {e.attacker} 攻擊 {e.target}，但未命中！")

    # ── 狀態異常 ──────────────────────────────

    def on_status_applied_event(self, e: StatusAppliedEvent):
        print(f"[狀態] {e.target} 陷入【{e.status}】狀態，持續 {e.rounds} 回合。")

    def on_status_blocked_action_event(self, e: StatusBlockedActionEvent):
        print(f"[狀態] {e.target} 因【{e.status}】無法行動。（剩餘 {e.rounds_remaining} 回合）")

    def on_status_expired_event(self, e: StatusExpiredEvent):
        print(f"[狀態] {e.target} 的【{e.status}】狀態解除。")

    # ── Buff ──────────────────────────────────

    def on_buff_applied_event(self, e: BuffAppliedEvent):
        print(f"[Buff] {e.target} 獲得【{e.buff_name}】，持續 {e.duration} 回合。")

    def on_buff_tick_event(self, e: BuffTickEvent):
        print(f"[Buff] {e.target} 的【{e.buff_name}】剩餘 {e.duration_remaining} 回合。")

    def on_buff_expired_event(self, e: BuffExpiredEvent):
        print(f"[Buff] {e.target} 的【{e.buff_name}】已到期移除。")

    # ── 死亡 / 掉落 ───────────────────────────

    def on_death_event(self, e: DeathEvent):
        role = "敵人" if e.is_enemy else "隊友"
        print(f"[死亡] {role}【{e.name}】已倒下！")

    def on_exp_gained_event(self, e: ExpGainedEvent):
        print(f"[經驗] {e.player} 獲得 {e.amount} 經驗（累計：{e.total_exp}）")

    def on_drop_event(self, e: DropEvent):
        print(f"[掉落] {e.enemy} 掉落：")
        for item in e.items:
            print(f"       {item['name']} × {item['quantity']}")

    def on_battle_result_event(self, e: BattleResultEvent):
        result_str = "勝利 🎉" if e.result == "win" else "敗北 💀"
        print(f"\n{'═'*40}")
        print(f"  戰鬥結束：{result_str}")
        print(f"  共 {e.turn_count} 回合")
        print(f"  擊敗敵人：{', '.join(e.defeated_enemies)}")
        print(f"  獲得總經驗：{e.total_exp}")
        print(f"{'═'*40}")

    def on_summon_event(self, e: SummonEvent):
        print(f"[召喚] {e.summoner} 召喚了【{e.ally_name}】加入戰鬥！")

    # ── 系統 ──────────────────────────────────

    def on_warning_event(self, e: WarningEvent):
        print(f"[警告] {e.message}")

    def on_heal_event(self, e: HealEvent):
        print(f"[治療] {e.target} 透過【{e.source}】恢復了 {e.amount:.0f} HP")

    # ── 玩家成長 ──────────────────────────────

    def on_level_up_event(self, e: LevelUpEvent):
        print(f"[升級] {e.player} 升至 Lv.{e.new_level}！")

    def on_stat_changed_event(self, e: StatChangedEvent):
        sign = "+" if e.delta >= 0 else ""
        print(f"[屬性] {e.player} {e.attribute} {sign}{e.delta}（來源：{e.source}）")

    # ── 背包 ──────────────────────────────────

    def on_item_added_event(self, e: ItemAddedEvent):
        tag = "新獲得" if e.is_new else "疊加"
        print(f"[背包] {tag}【{e.item_name}】× {e.quantity}")

    def on_item_removed_event(self, e: ItemRemovedEvent):
        print(f"[背包] 移除【{e.item_name}】× {e.quantity}")

    # ── 技能 / 裝備 ───────────────────────────

    def on_skill_equipped_event(self, e: SkillEquippedEvent):
        print(f"[技能] {e.player} 裝備了【{e.skill_name}】")

    def on_skill_removed_event(self, e: SkillRemovedEvent):
        print(f"[技能] {e.player} 移除了【{e.skill_name}】")

    def on_equipment_equipped_event(self, e: EquipmentEquippedEvent):
        print(f"[裝備] {e.player} 裝備了【{e.equipment_name}】（{e.category}）")

    # ── 任務 / NPC / 秘境 ─────────────────────

    def on_task_progress_event(self, e: TaskProgressEvent):
        print(f"[任務] 【{e.task_name}】{e.description}")

    def on_task_completed_event(self, e: TaskCompletedEvent):
        print(f"[任務] 【{e.task_name}】已完成！")

    def on_npc_interaction_event(self, e: NpcInteractionEvent):
        print(f"[NPC] {e.action}（id={e.npc_id}）{e.detail}")

    def on_dungeon_progress_event(self, e: DungeonProgressEvent):
        if e.floor == -1:
            print(f"[秘境] 秘境 {e.dungeon_id} 通關！")
        else:
            print(f"[秘境] 秘境 {e.dungeon_id} 最高層：{e.floor}")


# ══════════════════════════════════════════════
#  靜默 Handler（測試用）
# ══════════════════════════════════════════════

class SilentBattleHandler(BattleHandler):
    pass


# ══════════════════════════════════════════════
#  JSON 收集 Handler（WebSocket / 前端用）
# ══════════════════════════════════════════════

class JsonCollectorHandler(BattleHandler):
    def __init__(self):
        self._events: list[dict] = []

    def handle(self, event: BattleEvent) -> None:
        self._events.append(event.to_dict())

    def flush(self) -> list[dict]:
        events, self._events = self._events, []
        return events