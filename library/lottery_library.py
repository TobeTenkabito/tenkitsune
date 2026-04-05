from .material_library import material_library
from common.module.lottery import Lottery
lottery_library = {
    1: Lottery(
        name="装备材料池",
        rewards=[
            {"probability": 0.03, "item": material_library[100026]},  # 金罡晶
            {"probability": 0.10, "item": material_library[100059]},  # 天柱冰铁
            {"probability": 0.17, "item": material_library[100060]},  # 昆仑寒玉
            {"probability": 0.3, "item": material_library[100034]},  # 白金
            {"probability": 0.4, "item": material_library[100016]},  # 离火
        ],
    ),
    2: Lottery(
        name="npc测试",
        rewards=[
            {"probability": 0.03, "item": material_library[100004]},
            {"probability": 0.10, "item": material_library[100005]},
            {"probability": 0.17, "item": material_library[100006]},
            {"probability": 0.3, "item": material_library[100007]},
            {"probability": 0.4, "item": material_library[100008]},
        ],
    ),
}