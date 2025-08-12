import json
import os
import re
from decimal import Decimal
from common.module.item import Equipment, Skill


def parse_attribute_value(value, top_level=False):
    if isinstance(value, dict):
        # 仅在顶层解析并实例化对象
        if top_level and "__class__" in value:
            class_name = value.pop("__class__")
            if class_name == "Equipment":
                return Equipment(**{k: parse_attribute_value(v) for k, v in value.items()})
            elif class_name == "Skill":
                return Skill(**{k: parse_attribute_value(v) for k, v in value.items()})
        # 对嵌套字典递归解析，保留字典结构
        return {k: parse_attribute_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        # 递归解析列表
        return [parse_attribute_value(item) for item in value]
    elif isinstance(value, str):
        # 解析字符串化的表达式
        if re.match(r'^\w+_\d+$', value):
            lib_name, item_id = value.rsplit('_', 1)
            return (lib_name, int(item_id))
        # 解析数值字符串
        try:
            return float(value) if '.' in value else int(value)
        except ValueError:
            return value  # 返回原始字符串
    elif isinstance(value, Decimal):
        return float(value)  # 转换 Decimal 为 float
    return value  # 直接返回非特殊类型


def load_library_from_json(filepath, target_class):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)

    if target_class == Equipment:
        data = data.get("equipment_library", data)
    elif target_class == Skill:
        data = data.get("skill_library", data)

    library = {}
    for key, attributes in data.items():
        try:
            parsed_key = int(key)
        except ValueError:
            print(f"Skipping key {key}: cannot convert to int")
            continue

        parsed_attributes = parse_attribute_value(attributes, top_level=True)
        library[parsed_key] = parsed_attributes

    print(f"Loaded keys: {library.keys()}")
    return library


# 使用具体的加载函数
def load_equipment_library():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(base_dir, 'data', 'item', 'equipment.json')
    return load_library_from_json(filepath, Equipment)


def load_skill_library():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(base_dir, 'data', 'item', 'skill.json')
    return load_library_from_json(filepath, Skill)


# 加载数据
equipment_library = load_equipment_library()
print("Loaded Equipment Library:", equipment_library)

skill_library = load_skill_library()
print("Loaded Skill Library:", skill_library)


def debug_library(library):
    for key, value in library.items():
        print(f"ID: {key}")
        # 调用递归打印函数打印嵌套数据
        debug_nested_structure(value)
        print("-" * 40)


# 使用递归打印函数，支持任意嵌套结构
def debug_nested_structure(obj, indent=0):
    """递归打印嵌套结构"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            print(" " * indent + f"{key}:")
            debug_nested_structure(value, indent + 4)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            print(" " * indent + f"[{idx}]:")
            debug_nested_structure(item, indent + 4)
    else:
        print(" " * indent + str(obj))


print("Equipment Library:")
debug_library(equipment_library)


print("\nSkill Library:")
debug_library(skill_library)


def debug_specific_attributes(library, attributes):
    for key, instance in library.items():
        print(f"ID: {key}")
        for attr in attributes:
            print(f"{attr}: {getattr(instance, attr, 'Attribute not found')}")
        print("-" * 40)




