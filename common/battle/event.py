"""
戰鬥事件系統
─────────────────────────────────────────────
設計原則：
  1. 戰鬥邏輯只呼叫 emit()，不直接 print
  2. Handler 決定如何輸出（終端 / WebSocket / GUI / 測試）
  3. 所有事件都是 dataclass，可直接序列化成 JSON

使用方式：
  # 發送事件
  from common.battle.event import BattleEventBus, DamageEvent
  BattleEventBus.emit(DamageEvent(attacker="狐狸", target="哥布林", damage=42))

  # 註冊 Handler（在遊戲入口處設定一次）
  BattleEventBus.register(ConsoleBattleHandler())
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import json


# ══════════════════════════════════════════════
#  事件基類
# ══════════════════════════════════════════════

@dataclass
class BattleEvent:
    """所有戰鬥事件的基類。"""

    def to_dict(self) -> dict:
        return {"type": self.__class__.__name__, **asdict(self)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ══════════════════════════════════════════════
#  具體事件定義
# ══════════════════════════════════════════════

# ── 回合 ──────────────────────────────────────

@dataclass
class TurnStartEvent(BattleEvent):
    turn: int
    order: list[str]          # 參與者名稱列表

@dataclass
class TurnOrderUpdatedEvent(BattleEvent):
    order: list[str]

# ── 行動 ──────────────────────────────────────

@dataclass
class AttackEvent(BattleEvent):
    attacker: str
    target: str
    damage: float
    is_critical: bool = False

@dataclass
class SkillUsedEvent(BattleEvent):
    user: str
    skill_name: str
    targets: list[str]
    effects: list[dict]       # [{"attr": "hp", "change": -50}, ...]

@dataclass
class MissEvent(BattleEvent):
    attacker: str
    target: str

# ── 狀態異常 ──────────────────────────────────

@dataclass
class StatusAppliedEvent(BattleEvent):
    target: str
    status: str               # "stunned" / "paralyzed" / "silenced" / "blinded"
    rounds: int

@dataclass
class StatusBlockedActionEvent(BattleEvent):
    target: str
    status: str               # 因為哪個狀態被阻止行動
    rounds_remaining: int

@dataclass
class StatusExpiredEvent(BattleEvent):
    target: str
    status: str

# ── Buff ──────────────────────────────────────

@dataclass
class BuffAppliedEvent(BattleEvent):
    target: str
    buff_name: str
    duration: int

@dataclass
class BuffTickEvent(BattleEvent):
    target: str
    buff_name: str
    duration_remaining: int

@dataclass
class BuffExpiredEvent(BattleEvent):
    target: str
    buff_name: str

# ── 死亡 / 掉落 ───────────────────────────────

@dataclass
class DeathEvent(BattleEvent):
    name: str
    is_enemy: bool

@dataclass
class ExpGainedEvent(BattleEvent):
    player: str
    amount: int
    total_exp: int

@dataclass
class DropEvent(BattleEvent):
    enemy: str
    items: list[dict]         # [{"name": "草藥", "quantity": 2}, ...]

# ── 戰鬥結果 ──────────────────────────────────

@dataclass
class BattleResultEvent(BattleEvent):
    result: str               # "win" / "loss"
    turn_count: int
    defeated_enemies: list[str]
    total_exp: int

# ── 警告 / 系統 ───────────────────────────────

@dataclass
class WarningEvent(BattleEvent):
    message: str

@dataclass
class HealEvent(BattleEvent):
    target: str
    amount: float
    source: str               # 技能名 / 藥品名


# ══════════════════════════════════════════════
#  Handler 基類
# ══════════════════════════════════════════════

class BattleHandler:
    """
    所有輸出 Handler 的基類。
    子類只需 override 需要的 on_xxx 方法。
    """

    def handle(self, event: BattleEvent) -> None:
        method = f"on_{_to_snake(event.__class__.__name__)}"
        handler = getattr(self, method, self.on_unhandled)
        handler(event)

    def on_unhandled(self, event: BattleEvent) -> None:
        pass   # 預設忽略未處理的事件


# ══════════════════════════════════════════════
#  內建 Handler：終端輸出
# ══════════════════════════════════════════════

class ConsoleBattleHandler(BattleHandler):
    """將戰鬥事件輸出到終端，替代所有 print()。"""

    def on_turn_start_event(self, e: TurnStartEvent):
        print(f"\n{'━'*40}")
        print(f"  第 {e.turn} 回合開始！")
        print(f"  回合順序：{' → '.join(e.order)}")
        print(f"{'━'*40}")

    def on_turn_order_updated_event(self, e: TurnOrderUpdatedEvent):
        print(f"[回合] 更新順序：{' → '.join(e.order)}")

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

    def on_status_applied_event(self, e: StatusAppliedEvent):
        print(f"[狀態] {e.target} 陷入【{e.status}】狀態，持續 {e.rounds} 回合。")

    def on_status_blocked_action_event(self, e: StatusBlockedActionEvent):
        print(f"[狀態] {e.target} 因【{e.status}】無法行動。（剩餘 {e.rounds_remaining} 回合）")

    def on_status_expired_event(self, e: StatusExpiredEvent):
        print(f"[狀態] {e.target} 的【{e.status}】狀態解除。")

    def on_buff_applied_event(self, e: BuffAppliedEvent):
        print(f"[Buff] {e.target} 獲得【{e.buff_name}】，持續 {e.duration} 回合。")

    def on_buff_tick_event(self, e: BuffTickEvent):
        print(f"[Buff] {e.target} 的【{e.buff_name}】剩餘 {e.duration_remaining} 回合。")

    def on_buff_expired_event(self, e: BuffExpiredEvent):
        print(f"[Buff] {e.target} 的【{e.buff_name}】已到期移除。")

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

    def on_warning_event(self, e: WarningEvent):
        print(f"[警告] {e.message}")

    def on_heal_event(self, e: HealEvent):
        print(f"[治療] {e.target} 透過【{e.source}】恢復了 {e.amount:.0f} HP")


# ══════════════════════════════════════════════
#  內建 Handler：靜默（測試用）
# ══════════════════════════════════════════════

class SilentBattleHandler(BattleHandler):
    """吞掉所有事件，用於單元測試。"""
    pass


# ══════════════════════════════════════════════
#  內建 Handler：JSON 收集器（WebSocket / 前端用）
# ══════════════════════════════════════════════

class JsonCollectorHandler(BattleHandler):
    """
    收集所有事件為 JSON 列表。
    適合 WebSocket 推送或前端回放。

    用法：
      handler = JsonCollectorHandler()
      BattleEventBus.register(handler)
      # ... 戰鬥結束後 ...
      events_json = handler.flush()   # 取出並清空
    """

    def __init__(self):
        self._events: list[dict] = []

    def handle(self, event: BattleEvent) -> None:
        self._events.append(event.to_dict())

    def flush(self) -> list[dict]:
        events, self._events = self._events, []
        return events


# ══════════════════════════════════════════════
#  EventBus（全域單例）
# ══════════════════════════════════════════════

class _BattleEventBus:
    """
    全域事件總線。
    - register(handler)  : 添加 Handler
    - unregister(handler): 移除 Handler
    - emit(event)        : 發送事件給所有 Handler
    - clear()            : 清空所有 Handler（測試用）
    """

    def __init__(self):
        self._handlers: list[BattleHandler] = []

    def register(self, handler: BattleHandler) -> None:
        self._handlers.append(handler)

    def unregister(self, handler: BattleHandler) -> None:
        self._handlers.remove(handler)

    def emit(self, event: BattleEvent) -> None:
        for handler in self._handlers:
            handler.handle(event)

    def clear(self) -> None:
        self._handlers.clear()


# 全域單例
BattleEventBus = _BattleEventBus()


# ══════════════════════════════════════════════
#  工具函數
# ══════════════════════════════════════════════

def _to_snake(name: str) -> str:
    """
    把 CamelCase 轉成 snake_case。
    例：DamageEvent → damage_event
    """
    import re
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()