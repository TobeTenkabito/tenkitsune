from common.module.dungeon import Dungeon, DungeonFloor
from .npc_library import npc_library
from .enemy_library import enemy_library
from .boss_library import boss_library
from .material_library import material_library
from copy import deepcopy, copy
from .storybuff_library import storybuff_library
dungeon_library = {
    10001: Dungeon(
        name="大沼泽",
        number=10001,
        description="一个人迹罕至的大沼泽，仅供测试。",
        floors=[
            DungeonFloor(
                number=1,
                description="第一层，有一个神秘商人 NPC 提供提示。",
                npc=npc_library[102],
                entry_buff=[storybuff_library["强化"]],
                enemies=[deepcopy(enemy_library[500001])],
                first_time_rewards=[
                    {"type": "item", "item": material_library[100001], "quantity": 5}
                ],
                rewards=[
                    {"type": "item", "item": material_library[100001], "quantity": 10}
                ],
                random_rewards=[
                    {"type": "item", "item": material_library[100003], "quantity": 1, "chance": 0.2}
                ]
            ),
            DungeonFloor(
                number=2,
                description="第二层，空无一物。",
                enemies=[],  # 无敌人
                rewards=[]  # 无奖励
            ),
            DungeonFloor(
                number=3,
                description="第三层，有一个强大的盗贼。",
                entry_buff=[storybuff_library["强化"]],
                enemies=[deepcopy(enemy_library[500003])],
                first_time_rewards=[
                    {"type": "item", "item": material_library[100002], "quantity": 5}
                ],
                rewards=[
                    {"type": "item", "item": material_library[100002], "quantity": 10}
                ],
                random_rewards=[
                    {"type": "item", "item": material_library[100004], "quantity": 1, "chance": 0.1}
                ]
            )
        ],
        can_replay_after_completion=True,
        npc_affection_impact={
            101: -10,
            102: 5,
        }
    ),
    10002: Dungeon(
        name="天狐村道馆",
        number=10002,
        description="白玉为徒弟设计的道馆，供训练使用",
        floors=[
            DungeonFloor(
                number=1,
                description="第一层，用改良训练木偶训练。",
                npc=None,
                entry_buff=[],
                enemies=[deepcopy(enemy_library[500012])],
                first_time_rewards=[
                    {"type": "item", "item": material_library[110000], "quantity": 2}
                ],
                rewards=[
                    {"type": "item", "item": material_library[110000], "quantity": 2}
                ],
                random_rewards=[
                    {"type": "item", "item": material_library[100000], "quantity": 1, "chance": 0}
                ]
            ),
            DungeonFloor(
                number=2,
                description="第二层，用训练木偶训练。",
                enemies=[deepcopy(enemy_library[500012])],
                first_time_rewards=[
                    {"type": "item", "item": material_library[110000], "quantity": 2}
                ],
                rewards=[
                    {"type": "item", "item": material_library[110000], "quantity": 2}
                ],
                random_rewards=[
                    {"type": "item", "item": material_library[100000], "quantity": 2, "chance": 0}
                ]
            ),
        ],
        can_replay_after_completion=True,
        npc_affection_impact={100: 2}
    ),
    10003: Dungeon(
        name="青鸾山深处",
        number=10003,
        description="这里有一条小径，似乎鲜有人知",
        floors=[
            DungeonFloor(
                number=1,
                description="林荫小道",
                npc=None,
                entry_buff=[],
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=2,
                description="密林深处",
                enemies=[deepcopy(enemy_library[500013])],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=3,
                description="青鸾湖",
                enemies=[copy(boss_library[600002])],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
        ],
        can_replay_after_completion=False,
        npc_affection_impact={}
    ),
    10004: Dungeon(
        name="伏魔山路",
        number=10004,
        description="郁郁葱葱的树林和灌丛，已经让人辨认不出这里曾经有路了",
        floors=[
            DungeonFloor(
                number=1,
                description="伏魔山外围",
                npc=None,
                entry_buff=[],
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=2,
                description="伏魔山小道",
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=3,
                description="降魔湖",
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
        ],
        can_replay_after_completion=True,
        npc_affection_impact={}
    ),
    10005: Dungeon(
        name="伏魔山庄",
        number=10005,
        description="废弃的山庄，断壁残垣昭示着往日的辉煌。",
        floors=[
            DungeonFloor(
                number=1,
                description="伏魔山庄外围",
                npc=None,
                entry_buff=[],
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=2,
                description="伏魔山庄庭院",
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=3,
                description="伏魔山庄大厅",
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
        ],
        can_replay_after_completion=False,
        npc_affection_impact={}
    ),

    10008: Dungeon(
        name="东市",
        number=10008,
        description="靖天皇城的东市，人来人往",
        floors=[
            DungeonFloor(
                number=1,
                description="铁匠铺",
                npc=None,
                entry_buff=[],
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=2,
                description="回春堂",
                npc=None,
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=3,
                description="观云观",
                npc=None,
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
        ],
        can_replay_after_completion=True,
        npc_affection_impact={}
    ),
    10009: Dungeon(
        name="西市",
        number=10009,
        description="靖天皇城的西市，人来人往",
        floors=[
            DungeonFloor(
                number=1,
                description="醉春阁",
                npc=None,
                entry_buff=[],
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=2,
                description="聚贤楼",
                npc=None,
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=3,
                description="苍月门总部",
                npc=None,
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
        ],
        can_replay_after_completion=True,
        npc_affection_impact={}
    ),
    10010: Dungeon(
        name="皇宫",
        number=10010,
        description="大玄王朝权力中枢",
        floors=[
            DungeonFloor(
                number=1,
                description="",
                npc=None,
                entry_buff=[],
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=2,
                description="",
                npc=None,
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
            DungeonFloor(
                number=3,
                description="",
                npc=None,
                enemies=[],
                first_time_rewards=[],
                rewards=[],
                random_rewards=[]
            ),
        ],
        can_replay_after_completion=True,
        npc_affection_impact={}
    )
}