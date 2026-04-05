from all.gamestate import GameState
from common.module.npc import NPC
from library.boss_library import boss_library

# 初始化 GameState 类
game_state = GameState()
player = game_state.initialize_player(1, "测试玩家")

# 初始化 NPC 白玉
npc_baiyu = NPC(
    number=100,
    name="白玉",
    description="你的师傅，九尾天狐。",
    race="妖族",
    affection=90,
    favorite_items=[],
    daily_dialogue=["徒儿，近日可有好好修炼？",
                    "哦？又想听故事了……真拿你没办法。待我事毕……",
                    "仙狐村的来历……当年白子璋与我相约……没什么，你幻听了……",
                    "天狐一族灵力充沛，是以三界多图之。出门在外，护己周全……",
                    "你很闲吗？还不速速去修炼！",],
    task_dialogue="业精于勤，行成于思。",
    finish_task_dialogue="",
    tasks=[],
    exchange={},
    affection_dialogues={
        "low": ["自当勤加修炼。", "大道无情,不可怠惰。"],
        "medium": ["修炼有正道和魔道之别。",
                   "所谓正道即通过自身努力，与天地灵气共鸣。魔道则是夺取他人修为来助长自身。",
                   "在我看来，正道与魔道并无不同，一个夺天地造化，一个夺他人造化。只是后者显得更‘不道德’",],
        "high": ["万物生灵自有其法，假使有一天我不在你身边，你也要能自立自强。",
                 "重阳功能改善你的体质，千万要好好修炼。",
                 "打不过别人就跑，留得青山在，不怕没柴烧。"]
    },
    fight=[boss_library[690000]]
)

# 将 NPC 白玉 添加到全局游戏状态
game_state.add_npc(100, npc_baiyu)

# 测试与白玉互动
print("\n--- 与白玉互动 ---")
npc = game_state.get_npc(100)  # 获取白玉 NPC
if npc:
    npc.invoke_function_module(game_state.get_player())  # 与 NPC 进行互动
