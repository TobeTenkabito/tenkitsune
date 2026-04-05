# systems/battle_system.py
from core.ecs import world
from core.event_bus import bus
from components.stats import StatsComponent, BuffComponent

class BattleSystem:
    """純邏輯，不持有任何實體引用"""

    def __init__(self):
        # 訂閱事件
        bus.subscribe("battle_start", self.on_battle_start)
        bus.subscribe("action_attack", self.on_attack)

    def on_battle_start(self, participants: list[int], **kwargs):
        """按速度排序回合"""
        order = sorted(
            participants,
            key=lambda eid: world.get_component(eid, StatsComponent).base_speed,
            reverse=True
        )
        bus.emit("turn_order_determined", order=order)

    def on_attack(self, attacker_id: int, target_id: int, **kwargs):
        attacker = world.get_component(attacker_id, StatsComponent)
        target = world.get_component(target_id, StatsComponent)
        if not attacker or not target:
            return

        damage = self._calculate_damage(attacker, target)
        target.hp = max(0, target.hp - damage)

        bus.emit("damage_dealt",
                 attacker_id=attacker_id,
                 target_id=target_id,
                 amount=damage)

        if target.hp <= 0:
            bus.emit("entity_defeated", entity_id=target_id)

    def _calculate_damage(self, attacker: StatsComponent,
                           target: StatsComponent) -> int:
        import random
        is_crit = random.random() < attacker.base_crit / 100
        base = attacker.attack - target.base_defense
        base = max(1, base)
        return int(base * (attacker.base_crit_damage / 100) if is_crit else base)
