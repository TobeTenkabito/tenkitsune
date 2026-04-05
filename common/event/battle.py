"""
戰鬥相關事件
─────────────────────────────────────────────
回合、行動、狀態異常、Buff、死亡掉落、戰鬥結果
"""

from __future__ import annotations
from dataclasses import dataclass
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
    