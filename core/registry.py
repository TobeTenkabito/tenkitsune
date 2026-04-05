from pathlib import Path
from core.parser import load_json_to_dict

class Registry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._store: dict[str, dict[int, object]] = {}
        return cls._instance

    def load(self, category: str, filepath: str | Path):
        """加載 JSON 並存入指定 category"""
        data = load_json_to_dict(str(filepath))
        self._store[category] = data
        print(f"[Registry] '{category}' loaded → {len(data)} entries")

    def get(self, category: str, key: int) -> object | None:
        return self._store.get(category, {}).get(key)

    def get_all(self, category: str) -> dict[int, object]:
        return self._store.get(category, {})

    def has(self, category: str, key: int) -> bool:
        return key in self._store.get(category, {})

registry = Registry()