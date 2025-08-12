from library.material_library import material_library

# 定义铜板
copper_coin = material_library[100000]

# 定义灵石
spirit_stone = material_library[110000]

# 货币兑换比例
EXCHANGE_RATE = 1000  # 1 灵石 = 1000 铜板


def convert_to_copper(spirit_stones):
    """将灵石转换为铜板"""
    return spirit_stones * EXCHANGE_RATE


def convert_to_spirit(copper_coins):
    """将铜板转换为灵石"""
    return copper_coins // EXCHANGE_RATE