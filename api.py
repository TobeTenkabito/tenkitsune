from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
from game_engine import GameEngine  # 假设 GameEngine 在 game_engine.py 中
from all.gamestate import game_state
from all.dlcmanager import DLCManager

# 初始化 FastAPI
app = FastAPI(title="天狐修炼纪 API")

# 初始化 GameEngine（假设 game_state 和 dlc_manager 已定义）
game_engine = GameEngine(game_state, dlc_manager=DLCManager())


# Pydantic 模型用于验证请求体
class ActionRequest(BaseModel):
    action_id: int


class ChoiceRequest(BaseModel):
    choice: int


class SlotRequest(BaseModel):
    slot_number: int


# API 端点
@app.get("/game/title")
async def get_title_screen():
    """获取标题屏幕选项"""
    return game_engine.choose_at_main()


@app.post("/game/title/choice")
async def process_title_choice(request: ChoiceRequest):
    """处理标题屏幕选择"""
    result = game_engine.process_main_choice(request.choice)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/game/main")
async def get_main_screen():
    """获取主游戏界面"""
    result = game_engine.action_system()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/game/action")
async def process_action(request: ActionRequest):
    """处理主界面动作"""
    result = game_engine.process_action(request.action_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/game/player")
async def get_player_condition():
    """获取玩家状态"""
    result = game_engine.player_condition()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/game/save")
async def save_game(request: SlotRequest):
    """保存游戏"""
    result = game_engine.save_game(game_engine.current_player, request.slot_number)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/game/load")
async def load_game(request: SlotRequest):
    """加载游戏"""
    player = game_engine.load_game(request.slot_number)
    if player is None:
        raise HTTPException(status_code=400, detail="Failed to load game")
    return game_engine.enter_main_screen()


@app.get("/game/save_slots")
async def get_save_slots():
    """获取存档列表"""
    return game_engine.load_game_from_memory()


@app.post("/game/story")
async def start_story(request: SlotRequest):
    """进入故事模式"""
    result = game_engine.start_story(request.slot_number)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/game/story/choice")
async def process_story_choice(request: ChoiceRequest):
    """处理故事模式选择"""
    # 假设 story_manager 和 save_callback 已存储在 game_engine 中
    result = game_engine.process_story_choice(request.choice, game_engine.story_manager, game_engine.save_callback)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/game/debug")
async def toggle_debug():
    """切换调试模式"""
    return game_engine.debug_mod()


@app.get("/game/main")
async def get_main_screen():
    result = game_engine.action_system()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/game/action")
async def process_action(request: ActionRequest):
    result = game_engine.process_action(request.action_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/lottery/choice")
async def process_lottery_choice(request: ChoiceRequest):
    result = game_engine.process_lottery_choice(request.choice)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/bag/choice")
async def process_bag_choice(request: ChoiceRequest):
    result = game_engine.process_bag_choice(request.choice, request.data.get("number") if request.data else None)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/cultivation/choice")
async def process_cultivation_choice(request: ChoiceRequest):
    result = game_engine.process_cultivation_choice(request.choice, request.data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/task/choice")
async def process_task_choice(request: ChoiceRequest):
    result = game_engine.process_task_choice(request.choice, request.data.get("number") if request.data else None)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# 启动服务器
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
