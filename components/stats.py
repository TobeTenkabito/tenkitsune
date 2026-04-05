"""
玩家屬性組件
─────────────────────────────────────────────
負責管理所有數值屬性：HP、MP、攻擊、防禦等
"""

from __future__ import annotations
from dataclasses import dataclass, field
from common.event import EventBus, WarningEvent, StatChangedEvent, LevelUpEvent


# ══════════════════════════════════════════════
#  屬性定義
# ══════════════════════════════════════════════

@dataclass
class Stats:
    # ── 基礎屬性 ──────────────────────────────
    level: int   = 1
    exp: int     = 0
    exp_to_next: int = 100

    max_hp: float  = 100.0
    hp: float      = 100.0
    max_mp: float  = 50.0
    mp: float      = 50.0

    # ── 戰鬥屬性 ──────────────────────────────
    attack: float   = 10.0
    defense: float  = 5.0
    speed: float    = 10.0
    crit_rate: float  = 0.05   # 5%
    crit_multi: float = 1.5    # 暴擊倍率

    # ── 修煉屬性 ──────────────────────────────
    spirit: float   = 0.0      # 靈力
    realm: int      = 0        # 境界

    # ── 擁有者名稱（用於事件）─────────────────
    owner: str = "unknown"

    # ══════════════════════════════════════════
    #  HP / MP 操作
    # ══════════════════════════════════════════

    def take_damage(self, amount: float) -> float:
        """承受傷害，回傳實際扣血量。"""
        actual = min(amount, self.hp)
        self.hp = max(0.0, self.hp - amount)
        return actual

    def heal(self, amount: float) -> float:
        """回復 HP，回傳實際回復量。"""
        actual = min(amount, self.max_hp - self.hp)
        self.hp = min(self.max_hp, self.hp + amount)
        return actual

    def consume_mp(self, amount: float) -> bool:
        """消耗 MP，MP 不足回傳 False。"""
        if self.mp < amount:
            EventBus.emit(WarningEvent(message=f"{self.owner} MP 不足（需要 {amount}，剩餘 {self.mp:.0f}）"))
            return False
        self.mp -= amount
        return True

    def restore_mp(self, amount: float) -> None:
        self.mp = min(self.max_mp, self.mp + amount)

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    # ══════════════════════════════════════════
    #  屬性修改
    # ══════════════════════════════════════════

    def modify(self, attribute: str, delta: float, source: str = "unknown") -> None:
        """
        修改任意屬性並發送 StatChangedEvent。
        attribute : Stats 上的欄位名稱，如 "attack"、"max_hp"
        """
        if not hasattr(self, attribute):
            EventBus.emit(WarningEvent(message=f"Stats.modify：未知屬性 '{attribute}'"))
            return
        old = getattr(self, attribute)
        setattr(self, attribute, old + delta)
        EventBus.emit(StatChangedEvent(
            player=self.owner,
            attribute=attribute,
            delta=delta,
            source=source,
        ))

    # ══════════════════════════════════════════
    #  經驗 / 升級
    # ══════════════════════════════════════════

    def gain_exp(self, amount: int) -> None:
        """獲得經驗值，自動處理升級。"""
        self.exp += amount
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self._level_up()

    def _level_up(self) -> None:
        self.level += 1
        self.exp_to_next = int(self.exp_to_next * 1.2)

        # 升級加成
        self.max_hp    += 10
        self.hp         = self.max_hp
        self.max_mp    += 5
        self.mp         = self.max_mp
        self.attack    += 2
        self.defense   += 1

        EventBus.emit(LevelUpEvent(player=self.owner, new_level=self.level))

    # ══════════════════════════════════════════
    #  顯示
    # ══════════════════════════════════════════

    def summary(self) -> str:
        return (
            f"Lv.{self.level} | "
            f"HP {self.hp:.0f}/{self.max_hp:.0f} | "
            f"MP {self.mp:.0f}/{self.max_mp:.0f} | "
            f"ATK {self.attack:.0f} | DEF {self.defense:.0f} | SPD {self.speed:.0f}"
        )
