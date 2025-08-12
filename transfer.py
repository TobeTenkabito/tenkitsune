import ast
import json
from decimal import Decimal
from fractions import Fraction


def convert_decimal_to_float(data):
    if isinstance(data, dict):
        return {k: convert_decimal_to_float(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_decimal_to_float(element) for element in data]
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data


def parse_definitions(py_file_path, json_file_path):
    with open(py_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 将文件内容解析为 AST
    tree = ast.parse(content)
    parsed_data = {}

    # 遍历 AST 中的所有赋值节点
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # 检查是否是目标字典的赋值
            for target in node.targets:
                if isinstance(target, ast.Name):
                    dictionary_name = target.id

                    if isinstance(node.value, ast.Dict):
                        parsed_data[dictionary_name] = {}
                        # 遍历字典的每个键值对
                        for key, value in zip(node.value.keys, node.value.values):
                            # 获取字典的键
                            dict_key = ast.literal_eval(key)
                            # 解析类实例化定义
                            parsed_data[dictionary_name][dict_key] = parse_instance(value)

    # 将所有 Decimal 转换为 float 以兼容 JSON
    parsed_data = convert_decimal_to_float(parsed_data)

    # 将结果写入 JSON 文件
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(parsed_data, json_file, ensure_ascii=False, indent=4)

    print(f"数据已成功保存到 {json_file_path}")


# 解析类实例或字面量
def parse_instance(node):
    if isinstance(node, ast.Call):
        # 获取类名
        class_name = getattr(node.func, 'id', None) or f"{node.func.value.id}.{node.func.attr}"
        # 提取关键字参数
        attributes = {kw.arg: parse_node(kw.value) for kw in node.keywords}
        # 将类名和参数组合成一个字典
        return {"__class__": class_name, **attributes}
    else:
        # 直接解析字面量
        return parse_node(node)


def parse_node(node):
    if isinstance(node, ast.Constant):
        # 处理常量类型 (包括 int, float, str, None, bool)
        return Decimal(str(node.value)) if isinstance(node.value, float) else node.value
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        # 处理负数 (如 -1000 或 -0.5)
        operand = parse_node(node.operand)
        if isinstance(operand, (int, float, Decimal)):
            return -operand
        else:
            return f"-({operand})"  # 处理非数值操作数
    elif isinstance(node, ast.List):
        # 处理列表类型
        return [parse_node(element) for element in node.elts]
    elif isinstance(node, ast.Dict):
        # 处理字典类型
        return {parse_node(k): parse_node(v) for k, v in zip(node.keys, node.values)}
    elif isinstance(node, ast.Tuple):
        # 处理元组类型，转换为列表
        return [parse_node(element) for element in node.elts]
    elif isinstance(node, ast.Name):
        # 处理变量名
        return node.id
    elif isinstance(node, ast.Subscript):
        # 处理下标引用 (如 material_library[100000])
        return f"{parse_node(node.value)}[{parse_node(node.slice)}]"
    elif isinstance(node, ast.Call):
        # 处理函数调用 (如 random.randint(100, 500))
        func_name = getattr(node.func, 'id', None) or f"{node.func.value.id}.{node.func.attr}"
        args = [parse_node(arg) for arg in node.args]
        # 将函数和参数组合成字符串，确保在 JSON 中保留调用信息
        return f"{func_name}({', '.join(map(str, args))})"
    else:
        # 将无法解析的表达式转为字符串
        return ast.dump(node)


# 使用脚本
parse_definitions("../library/enemy_library.py", "../data/character/enemy.json")
parse_definitions("../library/ally_library.py", "../data/character/ally.json")
parse_definitions("../library/boss_library.py", "../data/character/boss.json")


parse_definitions("../library/skill_library.py", "../data/item/skill.json")
parse_definitions("../library/product_library.py", "../data/item/product.json")
parse_definitions("../library/material_library.py", "../data/item/material.json")
parse_definitions("../library/medicine_library.py", "../data/item/medicine.json")
parse_definitions("../library/equipment_library.py", "../data/item/equipment.json")
parse_definitions("../library/warp_library.py", "../data/item/warp.json")

parse_definitions("../library/map_library.py", "../data/scenario/map.json")
parse_definitions("../library/dungeon_library.py", "../data/scenario/dungeon.json")

parse_definitions("../library/npc_library.py", "../data/interact/npc.json")
parse_definitions("../library/lottery_library.py", "../data/interact/lottery.json")
parse_definitions("../library/market_library.py", "../data/interact/market.json")
parse_definitions("../library/task_library.py", "../data/interact/task.json")