from common.interface.bag_interface import BagInterface
from common.character.player import Player
from common.module.item import Equipment, Skill, Material, Product

def test_bag_interface():
    # 创建一个测试玩家
    player = Player(number=1, name="测试玩家")

    # 创建一些测试物品、技能和材料
    sword = Equipment(
        number=1001, name="长剑", description="锋利的长剑", quality="普通", category="武器", price=100, quantity=1,
        hp=0, mp=0, attack=10, defense=0, speed=5, crit=2, crit_damage=150, resistance=0, penetration=0
    )
    shield = Equipment(
        number=1002, name="盾牌", description="坚固的盾牌", quality="普通", category="防具", price=80, quantity=1,
        hp=50, mp=0, attack=0, defense=15, speed=0, crit=0, crit_damage=0, resistance=5, penetration=0
    )
    fireball_skill = Skill(
        number=2001, name="火球术", description="向敌人投掷火球，造成火焰伤害", quality="稀有", price=200, quantity=1,
        target_type="enemy", target_scope="single", effect_duration=3,
        effect_changes={"hp": {"multiplier": 1.2, "attribute": "attack"}}, cost={"mp": 20}
    )
    healing_potion = Product(
        number=3001, name="治疗药水", description="恢复少量生命值", quality="普通", price=30, quantity=3,
        target_type="ally", target_scope="single", effect_changes={"hp": 50}
    )
    iron_material = Material(
        number=4001, name="铁矿石", description="用于合成装备的基础材料", quality="普通", price=20, quantity=5
    )

    # 添加物品到玩家背包
    player.inventory.extend([sword, shield, fireball_skill, healing_potion, iron_material])

    # 创建 BagInterface 实例
    bag_interface = BagInterface(player)

    # 显示背包界面并允许操作
    bag_interface.show_bag_interface()

if __name__ == "__main__":
    test_bag_interface()