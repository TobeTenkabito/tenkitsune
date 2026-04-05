import json
import re
from decimal import Decimal


# 延遲導入，避免循環依賴
def _get_class_map():
    from common.module.item import Equipment, Skill, Medicine, Product, Material, Warp, Buff
    from common.character.enemy import Enemy
    from common.character.boss import Boss
    from common.character.ally import Ally
    from common.module.map import Map
    from common.module.dungeon import Dungeon, DungeonFloor
    from common.module.task import Task
    from common.module.battle import Battle
    from common.module.npc import NPC
    from common.module.lottery import Lottery


    return {
        "Equipment"  : Equipment,
        "Skill"      : Skill,
        "Medicine"   : Medicine,
        "Product"    : Product,
        "Material"   : Material,
        "Warp"       : Warp,
        "Buff"       : Buff,
        "Enemy"      : Enemy,
        "Boss"       : Boss,
        "Ally"       : Ally,
        "Map"        : Map,
        "Dungeon"    : Dungeon,
        "DungeonFloor": DungeonFloor,
        "Task"       : Task,
        "Battle"     : Battle,
        "NPC" : NPC,
        "Lottery" : Lottery,
    }


def parse_attribute_value(value, top_level=False):
    if isinstance(value, dict):
        if top_level and "__class__" in value:
            class_name = value.pop("__class__")
            cls_map = _get_class_map()
            cls = cls_map.get(class_name)
            if cls is None:
                raise ValueError(f"未知的 __class__: {class_name!r}")
            return cls(**{k: parse_attribute_value(v) for k, v in value.items()})
        return {k: parse_attribute_value(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [parse_attribute_value(item) for item in value]

    elif isinstance(value, str):
        # 保留 lib 引用格式：形如 "material_100000"
        if re.match(r'^\w+_\d+$', value):
            lib_name, item_id = value.rsplit('_', 1)
            return (lib_name, int(item_id))
        try:
            return float(value) if '.' in value else int(value)
        except ValueError:
            return value

    elif isinstance(value, Decimal):
        return float(value)

    return value


_WRAPPER_KEYS = {
    "equipment_library",
    "skill_library",
    "medicine_library",
    "product_library",
    "material_library",
    "warp_library",
    "enemy_library",
    "boss_library",
    "ally_library",
    "npc_library",
    "map_library",
    "dungeon_library",
    "lottery_library",
    "market_library",
    "task_library",
}


def load_json_to_dict(filepath: str) -> dict:
    """
    通用加載：自動剝離 wrapper key，返回 {int_id: instance} 字典。
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 自動剝離 wrapper key
    if isinstance(data, dict):
        keys = set(data.keys())
        wrapper = keys & _WRAPPER_KEYS
        if wrapper:
            data = data[wrapper.pop()]  # 取出真正的數據層

    result = {}
    for key, attributes in data.items():
        try:
            parsed_key = int(key)
        except ValueError:
            print(f"[Parser] Skipping non-int key: {key!r}")
            continue

        # 需要複製一份，因為 parse_attribute_value 會 pop __class__
        attrs_copy = json.loads(json.dumps(attributes))
        result[parsed_key] = parse_attribute_value(attrs_copy, top_level=True)

    return result
