from pathlib import Path
from core.registry import registry

_BASE = Path(__file__).parent.parent / "data"

_MANIFEST = {
    # category          filepath
    "equipment" :  _BASE / "item/equipment.json",
    "skill"     :  _BASE / "item/skill.json",
    "product"   :  _BASE / "item/product.json",
    "material"  :  _BASE / "item/material.json",
    "medicine"  :  _BASE / "item/medicine.json",
    "warp"      :  _BASE / "item/warp.json",
    "enemy"     :  _BASE / "character/enemy.json",
    "boss"      :  _BASE / "character/boss.json",
    "ally"      :  _BASE / "character/ally.json",
    "map"       :  _BASE / "scenario/map.json",
    "dungeon"   :  _BASE / "scenario/dungeon.json",
    "npc"       :  _BASE / "interact/npc.json",
    "lottery"   :  _BASE / "interact/lottery.json",
    "market"    :  _BASE / "interact/market.json",
    "task"      :  _BASE / "interact/task.json",
}

def load_all():
    for category, path in _MANIFEST.items():
        if path.exists():
            registry.load(category, path)
        else:
            print(f"[DataLoader] WARNING: {path} not found, skipping.")
            