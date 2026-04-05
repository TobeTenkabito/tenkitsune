from common.module.task import Task
from common.module.npc import NPC
from library.material_library import material_library
from common.character.player import Player
# 示例任务
task1 = Task(
    number=101,
    name="与猎人对话",
    description="去找猎人谈谈，了解更多信息。",
    quality="普通",
    repeatable=False,
    acceptance_conditions=[],
    completion_conditions=[{"talk_to_npc": 201}],
    rewards=[{"type": "item", "item": material_library[100001], "quantity": 5}]
)

# 示例 NPC
npc_hunter = NPC(
    number=201,
    name="猎人",
    description="一个经验丰富的猎人。",
    race="人类",
    affection=50,
    favorite_items=[material_library[100005]],
    daily_dialogue="今天的猎物可真多。",
    task_dialogue="有些事需要你帮忙。",
    finish_task_dialogue={
        101: "谢谢你来找我，这些信息对我们很有帮助。"
    },
    tasks=[task1]
)

# 玩家与 NPC 互动
player = Player(number=1, name="玩家")
npc_hunter.interact(player)