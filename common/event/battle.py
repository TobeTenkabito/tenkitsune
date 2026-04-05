"""
戰鬥相關事件
─────────────────────────────────────────────
回合、行動、狀態異常、Buff、死亡掉落、戰鬥結果
"""

from __future__ import annotations
from dataclasses import dataclass, field
from common.event.bus import BattleEvent


# ── 回合 ──────────────────────────────────────

@dataclass
class TurnStartEvent(BattleEvent):
    turn: int
    order: list[str]

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
    effects: list[dict]

@dataclass
class MissEvent(BattleEvent):
    attacker: str
    target: str

# ── 傷害 / 治療 / 屬性 ────────────────────────

@dataclass
class DamageRequestEvent(BattleEvent):
    """
    請求對目標造成傷害。
    監聽器負責：護盾吸收 → 扣血 → 死亡判定。

    damage_type:
      "physical"  - 物理傷害（走防禦/穿透計算）
      "true"      - 真實傷害（無視防禦）
      "skill"     - 技能傷害（走 calculate_damage）
    """
    source: str
    target: str
    amount: float
    damage_type: str = "physical"       # "physical" | "true" | "skill"
    skill_multiplier: float = 1.0
    is_skill: bool = False

@dataclass
class HealRequestEvent(BattleEvent):
    """
    請求治療目標。
    監聽器負責：上限保護 → 加血/加藍。

    attr: "hp" | "mp"
    """
    source: str
    target: str
    amount: float
    attr: str = "hp"

@dataclass
class StatChangeRequestEvent(BattleEvent):
    """
    請求修改目標的某個屬性（非 hp/mp）。
    監聽器負責：邊界保護 → 寫入。

    scope:
      "battle"  - 戰鬥臨時值（BattleState / skill_ 前綴）
      "base"    - 永久基礎值（慎用）
    """
    source: str
    target: str
    attr: str
    change: float
    scope: str = "battle"

# ── Buff ──────────────────────────────────────

@dataclass
class BuffRequestEvent(BattleEvent):
    """
    請求對目標施加 Buff / Debuff。
    監聽器負責：刷新或新增，並呼叫 apply_effect()。

    buff_type: "buff" | "debuff" | "status"
    effect 格式：
      {"attribute": "attack", "value": 50}          # 固定值
      {"attribute": "hp",     "value": -30}          # 每回合 DoT
      {"attribute": "stunned"}                       # 機制類（無 value）
    """
    source: str
    target: str
    buff_name: str
    buff_type: str
    duration: int
    effect: dict = field(default_factory=dict)
    chance: float = 1.0                              # 施加成功率 0.0~1.0

@dataclass
class BuffRemoveRequestEvent(BattleEvent):
    """
    請求移除目標的 Buff。

    scope:
      "name"   - 移除指定名稱
      "type"   - 移除指定類型（buff / debuff）
      "all"    - 移除全部
    """
    source: str
    target: str
    scope: str                                       # "name" | "type" | "all"
    buff_name: str = ""
    buff_type: str = ""

# ── 狀態異常 ──────────────────────────────────

@dataclass
class StatusAppliedEvent(BattleEvent):
    target: str
    status: str
    rounds: int

@dataclass
class StatusBlockedActionEvent(BattleEvent):
    target: str
    status: str
    rounds_remaining: int

@dataclass
class StatusExpiredEvent(BattleEvent):
    target: str
    status: str

# ── Buff 生命週期（通知用，非請求）──────────────

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
    items: list[dict]

# ── 戰鬥結果 ──────────────────────────────────

@dataclass
class BattleResultEvent(BattleEvent):
    result: str
    turn_count: int
    defeated_enemies: list[str]
    total_exp: int

# ── 召喚 ──────────────────────────────────────

@dataclass
class SummonEvent(BattleEvent):
    summoner: str
    ally_name: str