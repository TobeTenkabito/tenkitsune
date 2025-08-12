# interface/task_interface.py
import logging
from typing import List, Dict, Any


class TaskInterface:
    def __init__(self, player, game_state):
        self.player = player
        self.game_state = game_state
        self.logger = logging.getLogger('TaskInterface')
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            file_handler = logging.FileHandler('game.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def get_task_menu(self) -> Dict[str, Any]:
        """返回任务系统菜单选项"""
        self.logger.info("Fetching task system menu")
        return {
            "status": "success",
            "title": "任务系统",
            "options": [
                {"id": 1, "text": "查看当前任务"},
                {"id": 2, "text": "查看已完成任务"},
                {"id": 3, "text": "接取新任务"},
                {"id": 4, "text": "返回主界面"}
            ]
        }

    def get_current_tasks(self) -> Dict[str, Any]:
        """返回当前任务列表"""
        self.logger.info("Fetching current tasks")
        if self.player.accepted_tasks:
            tasks = [
                {"number": task.number, "name": task.name, "description": task.description}
                for task in self.player.accepted_tasks
            ]
            return {"status": "success", "tasks": tasks}
        return {"status": "success", "message": "你当前没有正在进行的任务", "tasks": []}

    def get_completed_tasks(self) -> Dict[str, Any]:
        """返回已完成任务列表"""
        self.logger.info("Fetching completed tasks")
        if self.player.completed_tasks:
            tasks = [{"number": task_number} for task_number in self.player.completed_tasks]
            return {"status": "success", "tasks": tasks}
        return {"status": "success", "message": "你还没有完成任何任务", "tasks": []}

    def get_available_tasks(self) -> Dict[str, Any]:
        """返回可接取任务列表"""
        self.logger.info("Fetching available tasks")
        available_tasks = [task for task in self.game_state.tasks if task.can_accept(self.player)]
        if available_tasks:
            tasks = [
                {"number": task.number, "name": task.name, "description": task.description}
                for task in available_tasks
            ]
            return {"status": "success", "tasks": tasks}
        return {"status": "success", "message": "当前没有可以接取的任务", "tasks": []}

    def accept_task(self, task_number: int) -> Dict[str, Any]:
        """接取指定任务"""
        self.logger.info(f"Attempting to accept task {task_number}")
        available_tasks = [task for task in self.game_state.tasks if task.can_accept(self.player)]
        for task in available_tasks:
            if task.number == task_number:
                task.accept(self.player)
                self.game_state.add_task_to_player(task.number)
                self.logger.info(f"Task {task.name} accepted successfully")
                return {"status": "success", "message": f"已接取任务: {task.name}"}
        self.logger.error(f"Invalid or unavailable task number: {task_number}")
        return {"error": f"无效的任务编号: {task_number}"}