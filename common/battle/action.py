"""
ActionMenu
負責玩家回合的所有輸入互動。
不直接修改戰場狀態，不直接 print，
狀態提示一律透過 EventBus 發送。
"""

from common.module.item import Skill, Equipment, Medicine, Product
from common.event import (
    EventBus,
    StatusBlockedActionEvent,
    WarningEvent,
)


class ActionMenu:

    def run(self, player, battle) -> str:
        """
        顯示主選單，執行玩家選擇的行動。
        返回值：
          "acted"      - 成功執行一個行動，回合結束
          "back"       - 玩家選擇返回（不消耗回合）
          "end_battle" - 玩家確認結束戰鬥
        """
        while True:
            self._display_status(player, battle)
            print(f"\n{'─'*30}")
            print(f"  {player.name} 的回合！請選擇行動：")
            print("  1. 普通攻擊")
            print("  2. 使用技能")
            print("  3. 使用法寶")
            print("  4. 使用藥品")
            print("  5. 使用道具")
            print("  6. 開啟／關閉自動戰鬥")
            print("  7. 返回上一級")
            print("  8. 結束戰鬥")
            print(f"{'─'*30}")
            choice = input("請輸入選項編號：").strip()

            if choice == "1":
                if self._attack(player, battle):
                    return "acted"

            elif choice == "2":
                if self._use_skill(player, battle):
                    return "acted"

            elif choice == "3":
                if self._use_equipment(player, battle):
                    return "acted"

            elif choice == "4":
                if self._use_medicine(player, battle):
                    return "acted"

            elif choice == "5":
                if self._use_product(player, battle):
                    return "acted"

            elif choice == "6":
                battle.auto_battle = not battle.auto_battle
                state = "開啟" if battle.auto_battle else "關閉"
                print(f"[自動戰鬥] 已{state}。")
                return "acted"

            elif choice == "7":
                return "back"

            elif choice == "8":
                if all(e.hp <= 0 for e in battle.enemies):
                    return "end_battle"
                else:
                    EventBus.emit(WarningEvent(
                        message="敵人尚未全部被擊敗，無法結束戰鬥。"
                    ))

            else:
                EventBus.emit(WarningEvent(
                    message="無效的選項，請重新輸入。"
                ))

    # ── 行動方法 ──────────────────────────────────────────────

    def _attack(self, player, battle) -> bool:
        if not player.can_attack():  # ← 替换 blind_rounds
            return False
        target = self.choose_target(battle, "enemy", "single")
        if target:
            player.perform_attack(target)
            return True
        return False

    def _use_skill(self, player, battle) -> bool:
        if not player.can_use_skill():  # ← 替换 silence_rounds
            return False
        skills = [s for s in player.battle_skills if isinstance(s, Skill)]
        if not skills:
            EventBus.emit(WarningEvent(message="你沒有可用的技能。"))
            return False
        skill = self.choose_item(skills)
        if not skill:
            return False
        target = self.choose_target(battle, skill.target_type, skill.target_scope)
        if target:
            player.use_skill(skill, target)
            return True
        return False

    def _use_medicine(self, player, battle) -> bool:
        medicines = [  # ← 修复迭代
            slot.item
            for slot in player.inventory._slots.values()
            if isinstance(slot.item, Medicine)
        ]
        if not medicines:
            EventBus.emit(WarningEvent(message="你沒有可用的藥品。"))
            return False
        medicine = self.choose_item(medicines)
        if not medicine:
            return False
        target = self.choose_target(battle, "ally", "single")
        if target:
            player.use_medicine(medicine, target)
            return True
        return False

    def _use_product(self, player, battle) -> bool:
        products = [  # ← 修复迭代
            slot.item
            for slot in player.inventory._slots.values()
            if isinstance(slot.item, Product)
        ]
        if not products:
            EventBus.emit(WarningEvent(message="你沒有可用的道具。"))
            return False
        product = self.choose_item(products)
        if not product:
            return False
        target = self.choose_target(battle, product.target_type, product.target_scope)
        if target:
            player.use_product(product, target)
            return True
        return False


    def _use_equipment(self, player, battle) -> bool:
        equipments = [
            e for e in player.equipment
            if isinstance(e, Equipment) and e.category == "法宝"
        ]
        if not equipments:
            EventBus.emit(WarningEvent(message="你沒有可用的法寶。"))
            return False

        equipment = self.choose_item(equipments)
        if not equipment:
            return False

        target = self.choose_target(battle, equipment.target_type, equipment.target_scope)
        if target:
            player.use_equipment(equipment, target)
            return True
        return False

    # ── 通用選擇器 ────────────────────────────────────────────

    def choose_target(self, battle, target_type: str, target_scope: str):
        if target_type == "ally" and target_scope == "user":
            return battle.player

        while True:
            if target_scope == "all":
                targets = (
                    [e for e in battle.enemies if e.hp > 0]
                    if target_type == "enemy"
                    else [battle.player] + [a for a in battle.allies if a.hp > 0]
                )
                label = "全體敵人" if target_type == "enemy" else "全體我方"
                print(f"\n選擇目標：")
                print(f"  1. {label}（共 {len(targets)} 個）")
                print("  0. 返回上一級")
                choice = input("請輸入選項編號：").strip()
                if choice == "0":
                    return None
                if choice == "1":
                    return targets
                EventBus.emit(WarningEvent(message="無效的選項。"))

            else:
                if target_type == "enemy":
                    candidates = [e for e in battle.enemies if e.hp > 0]
                    if not candidates:
                        EventBus.emit(WarningEvent(message="沒有可選的敵人目標。"))
                        return None
                    print("\n選擇攻擊的敵人：")
                    for i, e in enumerate(candidates, 1):
                        print(f"  {i}. {e.name}（HP: {e.hp}/{e.max_hp}）")
                    print("  0. 返回上一級")
                    choice = input("請輸入選項編號：").strip()
                    if choice == "0":
                        return None
                    if choice.isdigit() and 1 <= int(choice) <= len(candidates):
                        return candidates[int(choice) - 1]
                    EventBus.emit(WarningEvent(message="無效的選項。"))

                elif target_type == "ally":
                    candidates = [battle.player] + [a for a in battle.allies if a.hp > 0]
                    print("\n選擇目標：")
                    for i, c in enumerate(candidates, 1):
                        print(f"  {i}. {c.name}（HP: {c.hp}/{c.max_hp}）")
                    print("  0. 返回上一級")
                    choice = input("請輸入選項編號：").strip()
                    if choice == "0":
                        return None
                    if choice.isdigit() and 1 <= int(choice) <= len(candidates):
                        return candidates[int(choice) - 1]
                    EventBus.emit(WarningEvent(message="無效的選項。"))

    def choose_item(self, items: list):
        while True:
            print("\n選擇使用的技能 / 法寶 / 道具：")
            for i, item in enumerate(items, 1):
                extra = ""
                if hasattr(item, "frequency") and item.frequency is not None:
                    extra = f"  [剩餘次數: {item.frequency}]"
                print(f"  {i}. {item.name} — {item.description}{extra}")
            print("  0. 返回上一級")
            choice = input("請輸入選項編號：").strip()
            if choice == "0":
                return None
            if choice.isdigit() and 1 <= int(choice) <= len(items):
                return items[int(choice) - 1]
            EventBus.emit(WarningEvent(message="無效的選項。"))

    # ── 狀態顯示 ──────────────────────────────────────────────
    # action.py 的 UI 渲染部分（選單本身）仍保留 print，
    # 因為這是純終端 UI 層，不屬於戰鬥邏輯事件。

    @staticmethod
    def _display_status(player, battle) -> None:
        print(f"\n{'═'*40}")
        print(f"  {player.name}  HP: {player.hp}/{player.max_hp}  MP: {player.mp}/{player.max_mp}")
        for ally in battle.allies:
            if ally.hp > 0:
                print(f"  {ally.name}  HP: {ally.hp}/{ally.max_hp}  MP: {ally.mp}/{ally.max_mp}")
        print(f"{'─'*40}")
        print("  敵人：")
        for enemy in battle.enemies:
            if enemy.hp > 0:
                print(f"    {enemy.name}  HP: {enemy.hp}/{enemy.max_hp}")
        print(f"{'═'*40}")