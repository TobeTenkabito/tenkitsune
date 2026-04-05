from collections import defaultdict
from typing import Callable, Any


class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners = defaultdict(list)
        return cls._instance

    def subscribe(self, event: str, callback: Callable):
        self._listeners[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable):
        self._listeners[event].remove(callback)

    def emit(self, event: str, **kwargs):
        for callback in self._listeners[event]:
            callback(**kwargs)


# 全局單例
bus = EventBus()
