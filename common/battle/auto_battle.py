"""
AutoBattleAI
自動戰鬥決策邏輯。
只負責「決策」，不直接修改戰場狀態。
"""
import random

from common.battle.event import (
    BattleEventBus,
    WarningEvent,
)


class AutoBattleAI:

    def decide(self, player, battle) -> None:
        """
        自動決策並執行一次行動。
        優先級：
          1. 血量 < 30% → 優先使用治療技能
          2. 選擇收益最高的技能
          3. 無合適技能 → 普通攻擊
        """
        if player.hp < 0.3 * player.max_hp:
            if self._try_heal(player, battle):
                return

        skill, target = self._choose_best_skill(player, battle)
        if skill and target:
            player.use_skill(skill, target)
            return

        target = self._pick_enemy(battle)
        if target:
            player.perform_attack(target)

    # ── 治療 ──────────────────────────────────────────────────

    def _try_heal(self, player, battle) -> bool:
        for skill in player.battle_skills:
            if (skill.target_type == "ally"
                    and "hp" in skill.effect_changes
                    and getattr(skill, "frequency", None) != 0):
                target = self._pick_ally(player, battle, scope=skill.target_scope)
                if target and (
                    (isinstance(target, list) and any(t.hp < t.max_hp for t in target))
                    or (not isinstance(target, list) and target.hp < target.max_hp)
                ):
                    player.use_skill(skill, target)
                    return True
        return False

    # ── 技能選擇 ──────────────────────────────────────────────

    def _choose_best_skill(self, player, battle):
        best_skill, best_value, best_target = None, -float("inf"), None

        for skill in player.battle_skills:
            if getattr(skill, "frequency", None) is not None and skill.frequency <= 0:
                continue
            target = self._pick_target(player, battle, skill.target_type, skill.target_scope)
            if not target:
                continue
            if not self._can_afford(skill, player):
                continue
            value = self._calculate_skill_value(skill, player, target)
            if value > best_value:
                best_value, best_skill, best_target = value, skill, target

        return best_skill, best_target

    def _calculate_skill_value(self, skill, user, target) -> float:
        total_value = 0.0
        single_target = target if not isinstance(target, list) else target[0]

        for attr, effect_change in skill.effect_changes.items():
            if attr != "hp":
                continue
            source_attr = effect_change.get("attribute", "attack")
            base_value = getattr(
                single_target if effect_change.get("source") == "target" else user,
                source_attr, 0
            )
            multiplier = effect_change.get("multiplier", 1.0)

            if source_attr in ("attack", "defense"):
                try:
                    # calculate_damage 現在返回 (damage, is_critical)
                    damage, _ = user.calculate_damage(
                        single_target, base_value,
                        skill_multiplier=multiplier, is_skill=True
                    )
                    total_value += max(0.0, damage)
                except Exception as e:
                    BattleEventBus.emit(WarningEvent(message=f"AutoAI 計算傷害出錯：{e}"))
            else:
                change = base_value * multiplier
                total_value += max(0.0, change) if skill.target_type == "enemy" else max(0.0, -change)

        for cost_attr, cost_change in skill.cost.items():
            try:
                cost_value = (
                    cost_change if isinstance(cost_change, (int, float))
                    else getattr(user, cost_change.get("attribute", "hp"))
                         * cost_change.get("multiplier", 1.0)
                )
                total_value -= abs(cost_value)
            except Exception as e:
                BattleEventBus.emit(WarningEvent(message=f"AutoAI 計算消耗出錯：{e}"))

        return total_value

    def _can_afford(self, skill, player) -> bool:
        for cost_attr, cost_change in skill.cost.items():
            try:
                cost_value = (
                    cost_change if isinstance(cost_change, (int, float))
                    else getattr(player, cost_change.get("attribute", "hp"))
                         * cost_change.get("multiplier", 1.0)
                )
                if cost_value > getattr(player, cost_attr, 0):
                    return False
            except Exception as e:
                BattleEventBus.emit(WarningEvent(message=f"AutoAI 消耗檢查出錯：{e}"))
                return False
        return True

    # ── 目標選擇 ──────────────────────────────────────────────

    def _pick_target(self, player, battle, target_type: str, target_scope: str):
        if target_scope == "all":
            return (
                [e for e in battle.enemies if e.hp > 0]
                if target_type == "enemy"
                else [player] + [a for a in battle.allies if a.hp > 0]
            )
        if target_type == "enemy":
            return self._pick_enemy(battle)
        return self._pick_ally(player, battle)

    def _pick_enemy(self, battle):
        available = [e for e in battle.enemies if e.hp > 0]
        return random.choice(available) if available else None

    def _pick_ally(self, player, battle, scope="single"):
        available = [player] + [a for a in battle.allies if a.hp > 0]
        if scope == "user":
            return player
        return random.choice(available) if available else None