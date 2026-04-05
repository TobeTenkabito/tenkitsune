# core/drop_resolver.py
import random
import re

# 白名單：只允許這些函數
_SAFE_FUNCS = {
    "random.randint": random.randint,
    "random.choice": random.choice,
    "random.uniform": random.uniform,
}

def resolve_quantity(value: int | str) -> int:
    """
    安全地解析 drop 數量。
    - 數字直接返回
    - 字符串只允許白名單函數，不用 eval
    """
    if isinstance(value, int):
        return value

    if isinstance(value, str):
        # 匹配 random.randint(a, b)
        m = re.fullmatch(r'random\.randint\((\d+),\s*(\d+)\)', value.strip())
        if m:
            return random.randint(int(m.group(1)), int(m.group(2)))

        # 匹配 random.choice([a, b, c])
        m = re.fullmatch(r'random\.choice\(\[(.+)\]\)', value.strip())
        if m:
            items = [int(x.strip()) for x in m.group(1).split(',')]
            return random.choice(items)

        raise ValueError(f"不支持的 drop 表達式: {value!r}")

    raise TypeError(f"無效的 quantity 類型: {type(value)}")


def resolve_drops(drops: list) -> list[tuple[int, int]]:
    """
    將 drops 列表解析為 [(item_id, quantity), ...]
    輸入: [[100000, "random.randint(100, 500)"], [100001, 1], ...]
    輸出: [(100000, 347), (100001, 1), ...]
    """
    return [(int(item_id), resolve_quantity(qty)) for item_id, qty in drops]
