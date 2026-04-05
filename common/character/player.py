import copy
import random
from common.battle.combatant import Combatant
from common.module.item import Equipment, Material, Product, Skill, Medicine, Warp
from common.module.cultivation import CultivationSystem


# ══════════════════════════════════════════════════════════════
#  輔助函數：複製 Item
# ══════════════════════════════════════════════════════════════

def _clone_item(item):
    if isinstance(item, Equipment):
        base = dict(
            number=item.number, name=item.name, description=item.description,
            quality=item.quality, category=item.category, price=item.price,
            quantity=item.quantity,
            hp=item.hp, mp=item.mp, attack=item.attack, defense=item.defense,
            speed=item.speed, crit=item.crit, crit_damage=item.crit_damage,
            resistance=item.resistance, penetration=item.penetration,
        )
        if item.category == "法宝":
            base.update(
                target_type=item.target_type, target_scope=item.target_scope,
                effect_duration=item.effect_duration,
                effect_changes=item.effect_changes, cost=item.cost,
            )
        return Equipment(**base)
    if isinstance(item, Medicine):
        return Medicine(
            number=item.number, name=item.name, description=item.description,
            quality=item.quality, price=item.price, quantity=item.quantity,
            effect_changes=item.effect_changes,
        )
    if isinstance(item, Product):
        return Product(
            number=item.number, name=item.name, description=item.description,
            quality=item.quality, price=item.price, quantity=item.quantity,
            target_type=item.target_type, target_scope=item.target_scope,
            effect_changes=item.effect_changes,
        )
    if isinstance(item, Material):
        return Material(
            number=item.number, name=item.name, description=item.description,
            quality=item.quality, price=item.price, quantity=item.quantity,
        )
    if isinstance(item, Skill):
        return Skill(
            number=item.number, name=item.name, description=item.description,
            price=item.price, quantity=item.quantity, quality=item.quality,
            target_type=item.target_type, target_scope=item.target_scope,
            effect_changes=item.effect_changes,
            frequency=item.frequency, cost=item.cost,
        )
    if isinstance(item, Warp):
        return Warp(
            number=item.number, name=item.name, description=item.description,
            price=item.price, quantity=item.quantity, quality=item.quality,
            target_map_number=item.target_map_number,
        )
    raise TypeError(f"未知的物品類型：{type(item)}")


# ══════════════════════════════════════════════════════════════
#  等級經驗查表
# ══════════════════════════════════════════════════════════════

_EXP_TABLE = [
    (1,   100),
    (10,  500),
    (20,  1000),
    (30,  2000),
    (40,  4000),
    (50,  8000),
    (60,  16000),
    (70,  32000),
    (80,  64000),
    (90,  128000),
    (100, 256000),
]

def _calc_max_exp(level: int) -> int:
    multiplier = 100
    for min_lv, mult in reversed(_EXP_TABLE):
        if level >= min_lv:
            multiplier = mult
            break
    return level * multiplier


# ══════════════════════════════════════════════════════════════
#  Player
# ══════════════════════════════════════════════════════════════

class Player(Combatant):

    def __init__(self, number, name, skill_library=None, ally_library=None):
        base_hp       = 100
        base_mp       = 100
        base_attack   = 100
        base_defense  = 80
        base_speed    = 50
        base_crit     = 5
        base_crit_dmg = 150
        base_res      = 0
        base_pen      = 0

        super().__init__(
            number=number, name=name,
            description="",
            level=1,
            hp=base_hp, mp=base_mp,
            max_hp=base_hp, max_mp=base_mp,
            attack=base_attack, defense=base_defense, speed=base_speed,
            crit=base_crit, crit_damage=base_crit_dmg,
            resistance=base_res, penetration=base_pen,
            skills=[], equipment=[],
        )

        # ── 注入的外部依賴 ────────────────────────────────────
        self._skill_library = skill_library or {}
        self._ally_library  = ally_library  or {}

        # ── 基礎屬性 ──────────────────────────────────────────
        self.base_hp          = base_hp
        self.base_mp          = base_mp
        self.base_attack      = base_attack
        self.base_defense     = base_defense
        self.base_speed       = base_speed
        self.base_crit        = base_crit
        self.base_crit_damage = base_crit_dmg
        self.base_resistance  = base_res
        self.base_penetration = base_pen

        # ── 成長 ──────────────────────────────────────────────
        self.exp               = 0
        self.max_exp           = _calc_max_exp(1)
        self.cultivation_point = 0

        # ── 各來源屬性加成 ────────────────────────────────────
        self._bonus_sources = {
            "task":        self._zero_bonus(),
            "dungeon":     self._zero_bonus(),
            "cultivation": self._zero_bonus(),
            "skill":       self._zero_bonus(),
        }

        # ── 背包 / 合成 ───────────────────────────────────────
        self.inventory       = []
        self.synthesis_slots = [None, None, None]

        # ── 遊戲進度 ──────────────────────────────────────────
        self.completed_tasks         = []
        self.accepted_tasks          = []
        self.ready_to_complete_tasks = []
        self.defeated_enemies        = {}
        self.highest_floor           = {}
        self.dungeon_clears          = {}
        self.dungeons_cleared        = set()
        self.talked_to_npcs          = set()
        self.given_items             = {}
        self.npcs_removed            = set()
        self.map_location            = None
        self.days                    = 1
        self.story_progress = {
            "current_chapter":    1,
            "current_node":       1,
            "completed_nodes":    [],
            "chapters_completed": {},
        }

        # ── DLC ───────────────────────────────────────────────
        self.traits         = None
        self.applied_traits = set()
        self.event          = None
        self.event_happened = set()

        # ── 鉤子 ──────────────────────────────────────────────
        self._after_update_hooks = []

        # ── 修為系統 ──────────────────────────────────────────
        self.cultivation_system = CultivationSystem(self, self._skill_library)

    # ── 向後相容的屬性別名 ────────────────────────────────────

    @staticmethod
    def _zero_bonus() -> dict:
        return dict(hp=0, mp=0, attack=0, defense=0, speed=0,
                    crit=0, crit_damage=0, resistance=0, penetration=0)

    def __setattr__(self, name, value):
        if not hasattr(self, "_bonus_sources"):
            super().__setattr__(name, value)
            return
        parts = name.split("_", 1)
        if (len(parts) == 2
                and parts[0] in self._bonus_sources
                and parts[1] in self._bonus_sources[parts[0]]):
            self._bonus_sources[parts[0]][parts[1]] = value
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        parts = name.split("_", 1)
        if len(parts) == 2:
            sources = object.__getattribute__(self, "_bonus_sources")
            if parts[0] in sources and parts[1] in sources[parts[0]]:
                return sources[parts[0]][parts[1]]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # ── 屬性計算 ──────────────────────────────────────────────

    def update_stats(self):
        src = self._bonus_sources

        self.max_hp       = self.base_hp
        self.max_mp       = self.base_mp
        self.attack       = self.base_attack
        self.defense      = self.base_defense
        self.speed        = self.base_speed
        self.crit         = self.base_crit
        self.crit_damage  = self.base_crit_damage
        self.resistance   = self.base_resistance
        self.penetration  = self.base_penetration

        for source in ("task", "dungeon", "cultivation", "skill"):
            b = src[source]
            self.max_hp      += b["hp"]
            self.max_mp      += b["mp"]
            self.attack      += b["attack"]
            self.defense     += b["defense"]
            self.speed       += b["speed"]
            self.crit        += b["crit"]
            self.crit_damage += b["crit_damage"]
            self.resistance  += b["resistance"]
            self.penetration += b["penetration"]

        for item in self.equipment:
            if isinstance(item, Equipment):
                self.max_hp      += item.hp
                self.max_mp      += item.mp
                self.attack      += item.attack
                self.defense     += item.defense
                self.speed       += item.speed
                self.crit        += item.crit
                self.crit_damage += item.crit_damage
                self.resistance  += item.resistance
                self.penetration += item.penetration

        self.max_hp = max(1, self.max_hp)
        self.max_mp = max(1, self.max_mp)

        self._trigger_after_update_hooks()

        self.hp = min(self.hp, self.max_hp)
        self.mp = min(self.mp, self.max_mp)

    # ── 升級 / 經驗 ───────────────────────────────────────────

    def update_max_exp(self):
        self.max_exp = _calc_max_exp(self.level)

    def gain_exp(self, amount: int):
        self.exp += amount
        while self.exp >= self.max_exp and self.level < 200:
            self.exp -= self.max_exp
            self.level_up()
        self.update_max_exp()

    def level_up(self):
        if self.level >= 200:
            return
        self.level        += 1
        self.base_hp       = 100 + (self.level - 1) * 50
        self.base_mp       = 100 + (self.level - 1) * 20
        self.base_attack   = 100 + (self.level - 1) * 10
        self.base_defense  = 80  + (self.level - 1) * 5
        self.base_speed    = 50  + (self.level - 1) * 2
        self.cultivation_point += 1
        self.cultivation_system.unused_points = self.cultivation_point
        self.update_stats()
        print(f"{self.name} 升级到 {self.level} 级!")

    # ── 屬性加成 ──────────────────────────────────────────────

    def gain_task_attribute(self, attribute: str, value):
        self._bonus_sources["task"][attribute] += value
        print(f"玩家的 {attribute} 增加了 {value} 点。")
        self.update_stats()

    def gain_dungeon_attribute(self, attribute: str, value):
        self._bonus_sources["dungeon"][attribute] += value
        print(f"玩家的 {attribute} 增加了 {value} 点（秘境奖励）。")
        self.update_stats()

    def reset_medicine_effects(self):
        self.hp = min(self.hp, self.max_hp)
        self.mp = min(self.mp, self.max_mp)
        print(f"{self.name} 的所有药品属性已重置。")

    def reset_skill_bonuses(self):
        for k in self._bonus_sources["skill"]:
            self._bonus_sources["skill"][k] = 0
        print(f"{self.name} 的所有技能影响已经移除。")

    # ── 裝備使用（法寶主動使用）─────────────────────────────
    # ⚠️ 補回漏掉的方法：Combatant 基類版本已覆蓋此邏輯，
    # 但 Player 有額外的「非法寶不能使用」提示，故保留覆寫。

    def use_equipment(self, equipment, target):
        if equipment.category == "法宝":
            equipment.use(self, target)
        else:
            print(f"{equipment.name} 不是法宝，不能使用。")

    # ── 背包 ──────────────────────────────────────────────────

    def add_to_inventory(self, item):
        for inv_item in self.inventory:
            if inv_item.number == item.number:
                inv_item.quantity += item.quantity
                self.update_stats()
                return
        new_item = _clone_item(item)
        self.inventory.append(new_item)
        print(f"已添加新的物品: {new_item.name}，数量: {new_item.quantity}")
        self.update_stats()

    def remove_from_inventory(self, item_number, quantity):
        for item in self.inventory:
            if item.number == item_number:
                if item.quantity >= quantity:
                    item.quantity -= quantity
                    if item.quantity <= 0:
                        self.inventory.remove(item)
                    print(f"已移除 {quantity} 个 {item.name}。")
                    return True
                else:
                    print(f"物品 {item.name} 的数量不足。")
                    return False
        print(f"背包中没有编号为 {item_number} 的物品。")
        return False

    def has_item(self, item) -> bool:
        return any(i.number == item.number for i in self.inventory)

    def use_item(self, item_number, target=None):
        for item in self.inventory:
            if item.number == item_number:
                item.use(self, target)
                return
        print(f"未找到编号为 {item_number} 的道具。")

    def get_inventory(self, item_type=None):
        if item_type:
            return [i for i in self.inventory if isinstance(i, item_type)]
        return self.inventory

    def get_inventory_item(self, item_number):
        for item in self.inventory:
            if item.number == item_number:
                return item
        print(f"背包中没有编号为 {item_number} 的物品。")
        return None

    def get_inventory_count(self, item_number) -> int:
        for item in self.inventory:
            if item.number == item_number:
                return item.quantity
        return 0

    def get_item_number_by_index(self, index):
        try:
            return self.inventory[index - 1].number
        except IndexError:
            print("错误：索引超出范围。")
            return None

    def inventory_summary(self, item_type=None) -> dict:
        summary = {}
        for item in self.inventory:
            if item_type and not isinstance(item, item_type):
                continue
            if item.number in summary:
                summary[item.number].quantity += item.quantity
            else:
                summary[item.number] = _clone_item(item)
        return summary

    def display_inventory(self, item_type=None):
        print("背包:")
        for i, item in enumerate(self.inventory_summary(item_type).values(), 1):
            print(f"{i}. {item.name} x {item.quantity}")

    # ── 技能欄 ────────────────────────────────────────────────

    def has_skill(self, skill_number) -> bool:
        return (
            any(i.number == skill_number for i in self.inventory) or
            any(s.number == skill_number for s in self.skills)
        )

    def add_to_skill(self, item):
        if len(self.skills) >= 9:
            print(f"技能栏已满，无法再装备 {item.name}。")
            return
        self.skills.append(item)
        self.update_stats()

    def remove_skill(self, skill_number) -> bool:
        for skill in self.skills:
            if skill.number == skill_number:
                self.skills.remove(skill)
                print(f"已从技能栏移除技能 {skill.name}。")
                return True
        print(f"技能栏中没有编号为 {skill_number} 的技能。")
        return False

    # ── 裝備欄 ────────────────────────────────────────────────

    _EQUIP_LIMIT = {"武器": 1, "防具": 1, "饰品": 1, "法宝": 3}

    def add_to_equipment(self, item):
        limit   = self._EQUIP_LIMIT.get(item.category, 0)
        current = sum(1 for e in self.equipment if e.category == item.category)
        if current >= limit:
            print(f"{item.category} 已达上限，无法再装备 {item.name}。")
            return
        self.equipment.append(item)
        self.update_stats()

    # ── 材料 ──────────────────────────────────────────────────

    def get_material_quantity(self, material_number) -> int:
        return sum(
            i.quantity for i in self.inventory
            if isinstance(i, (Material, Equipment)) and i.number == material_number
        )

    def decrease_material_quantity(self, material_number, amount) -> bool:
        remaining = amount
        for item in self.inventory[:]:
            if isinstance(item, (Material, Equipment)) and item.number == material_number:
                if item.quantity > remaining:
                    item.quantity -= remaining
                    return True
                else:
                    remaining -= item.quantity
                    self.inventory.remove(item)
                    if remaining <= 0:
                        return True
        return remaining <= 0

    # ── 合成 ──────────────────────────────────────────────────

    def set_synthesis_slot(self, slot_index, material):
        if 0 <= slot_index < len(self.synthesis_slots):
            self.synthesis_slots[slot_index] = material

    def clear_synthesis_slots(self):
        self.synthesis_slots = [None, None, None]

    # ── 道具使用 ──────────────────────────────────────────────

    def use_medicine(self, medicine, target):
        if medicine.quantity > 0:
            medicine.use(self, target)
            if medicine.quantity == 0:
                self.inventory.remove(medicine)
        else:
            print(f"{medicine.name} 数量不足，无法使用。")

    def use_product(self, product, target):
        if product.quantity > 0:
            product.use(self, target, summon_func=self._make_summon_func())
            if product.quantity == 0:
                self.inventory = [i for i in self.inventory if i.number != product.number]
        else:
            print(f"{product.name} 数量不足，无法使用。")

    def _make_summon_func(self):
        ally_lib = self._ally_library

        def summon_ally(user, effect_change):
            summon_number = effect_change.get("number")
            if summon_number not in ally_lib:
                print("无效的召唤编号，无法召唤队友。")
                return
            if any(a.number == summon_number for a in user.battle.allies):
                print(f"{ally_lib[summon_number].name} 已经在战斗中，无法再次召唤。")
                return
            if len(user.battle.allies) >= 3:
                print("友方队伍已达到上限，无法召唤更多队友。")
                return
            summoned = copy.copy(ally_lib[summon_number])
            user.battle.allies.append(summoned)
            user.battle.update_turn_order()
            print(f"{user.name} 召唤了 {summoned.name} 进入战斗！")

        return summon_ally

    # ── 任務 ──────────────────────────────────────────────────

    def check_tasks_for_kill(self, defeated_enemy):
        for task in self.accepted_tasks:
            for condition in task.completion_conditions:
                if "kill" not in condition:
                    continue
                kc = condition["kill"]
                if defeated_enemy.number != kc["enemy_id"]:
                    continue
                kc["current_count"] = kc.get("current_count", 0) + 1
                remaining = kc["count"] - kc["current_count"]
                print(f"任务 '{task.name}' 更新: 剩余击杀数: {remaining}")
                if kc["current_count"] >= kc["count"]:
                    print(f"任务 '{task.name}' 完成条件已满足。")

    def update_tasks_after_battle(self):
        for task in self.accepted_tasks[:]:
            if task.check_completion(self):
                print(f"任务 '{task.name}' 已完成！")
                task.complete(self)
            else:
                print(f"任务 '{task.name}' 未完成。")

    # ── NPC ───────────────────────────────────────────────────

    def talk_to_npc(self, npc_number):
        self.talked_to_npcs.add(npc_number)

    def has_talked_to_npc(self, npc_number) -> bool:
        return npc_number in self.talked_to_npcs

    def mark_remove_npc(self, npc_number):
        self.npcs_removed.add(npc_number)

    def give_item_to_npc(self, npc_id, item_number, quantity):
        self.given_items.setdefault(npc_id, {})
        self.given_items[npc_id][item_number] = (
            self.given_items[npc_id].get(item_number, 0) + quantity
        )
        print(f"玩家赠送 {quantity} 个物品（ID: {item_number}）给 NPC（ID: {npc_id}）")

    def get_item_given_to_npc(self, npc_id, item_number) -> int:
        return self.given_items.get(npc_id, {}).get(item_number, 0)

    # ── 秘境 ──────────────────────────────────────────────────

    def update_highest_floor(self, dungeon_id, floor_number):
        self.highest_floor[dungeon_id] = max(
            self.highest_floor.get(dungeon_id, 0), floor_number
        )
        print(f"玩家在此秘境的最高层数已更新为 {self.highest_floor[dungeon_id]}。")

    def mark_dungeon_cleared(self, dungeon_id):
        self.dungeons_cleared.add(dungeon_id)
        print("您神通广大，用出数个手段将秘境妖魔尽数斩杀，威震三界！")

    # ── 故事 ──────────────────────────────────────────────────

    def update_story_progress(self, chapter, node_id):
        self.story_progress["current_chapter"] = chapter
        self.story_progress["current_node"]    = node_id
        self.story_progress["chapters_completed"] = {}

    # ── 修為系統 ──────────────────────────────────────────────

    def load_cultivation_from_save_data(self, save_data):
        player_data            = save_data.get("player", {})
        self.cultivation_point = player_data.get("cultivation_point", 0)
        cultivation_data       = player_data.get("cultivation_system", {})
        self.cultivation_system.restore_from_save(cultivation_data)
        print(f"玩家 {self.name} 的修为系统已从存档中加载。")

    # ── DLC 鉤子 ──────────────────────────────────────────────

    def register_after_update_hook(self, hook):
        self._after_update_hooks.append(hook)

    def _trigger_after_update_hooks(self):
        for hook in self._after_update_hooks:
            hook(self)

    # ── choose_action ─────────────────────────────────────────

    def choose_action(self, engine) -> None:
        raise NotImplementedError("Player 的行動由 BattleEngine 處理。")

    # ── 顯示 ──────────────────────────────────────────────────

    def __str__(self):
        return (
            f"Player({self.number}, {self.name}, Level: {self.level}, "
            f"HP: {self.hp}/{self.max_hp}, MP: {self.mp}/{self.max_mp}, "
            f"ATK: {self.attack}, DEF: {self.defense}, SPD: {self.speed}, "
            f"CRIT: {self.crit}%, CRIT DMG: {self.crit_damage}%, "
            f"RES: {self.resistance}%, PEN: {self.penetration}%)"
        )