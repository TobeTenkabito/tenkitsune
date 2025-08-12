import random
from .currency import copper_coin, spirit_stone, convert_to_copper, convert_to_spirit
from library.market_library import market_library
from .item import Material


class Market:
    def __init__(self):
        self.items_for_sale = self.refresh_market()

    def refresh_market(self):
        items = random.sample(list(market_library.values()), k=min(len(market_library), 7))
        for item in items:
            item.price = max(1, round(item.price * random.uniform(0.8, 1.2)))
        return items

    def get_market_item(self, item_index):
        if 1 <= item_index <= len(self.items_for_sale):
            return self.items_for_sale[item_index - 1]  # 索引从0开始
        return None

    def sell_item(self, player, item, quantity):
        if item.quantity < quantity:
            return False, "数量不足，无法出售。"

        total_price = max(1, round(item.price * 0.25)) * quantity
        copper_coin.quantity += total_price
        player.remove_from_inventory(item, quantity)
        return True, f"成功出售 {quantity} 个 {item.name}，获得 {total_price} 个铜板。"

    def buy_item(self, player, item, quantity):
        if item not in self.items_for_sale:
            return False, "该物品不在市场中。"
        if item.quantity < quantity:
            return False, "市场库存不足，无法购买。"

        total_price = item.price * quantity
        player_copper_coins = player.get_material_quantity(copper_coin.number)
        player_spirit_stones = player.get_material_quantity(spirit_stone.number)

        total_available_copper = player_copper_coins + convert_to_copper(player_spirit_stones)

        if total_available_copper < total_price:
            return False, "铜板和灵石不足，无法购买。"

        if player_copper_coins >= total_price:
            player.decrease_material_quantity(copper_coin.number, total_price)
        else:
            remaining_price = total_price - player_copper_coins
            required_spirit_stones = convert_to_spirit(remaining_price)
            player.decrease_material_quantity(copper_coin.number, player_copper_coins)
            player.decrease_material_quantity(spirit_stone.number, required_spirit_stones)

        player.add_to_inventory(Material(item.number, item.name, item.description, item.quality, item.price, quantity))
        item.quantity -= quantity
        if item.quantity == 0:
            self.items_for_sale.remove(item)
        return True, f"成功购买 {quantity} 个 {item.name}，花费 {total_price} 个铜板。"

    def display_items(self):
        for item in self.items_for_sale:
            print(f"{item.name} (价格: {item.price} 铜板, 数量: {item.quantity})")
