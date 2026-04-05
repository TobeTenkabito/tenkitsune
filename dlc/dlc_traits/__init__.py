from .traits import Trait
import tkinter as tk
import random


class DLCTraits:
    def __init__(self):
        from .traits_library import traits_library
        self.traits = traits_library  # 确保 traits_library 是包含 Trait 实例的字典

    def apply_to_player(self, player):
        # 确保 player.traits 不为 None，若为 None 则初始化为空字典
        if player.traits is None:
            player.traits = {}

        # 筛选出正面特质和负面特质
        positive_traits = [trait for trait in self.traits.values() if trait.nature == "positive"]
        negative_traits = [trait for trait in self.traits.values() if trait.nature == "negative"]

        # 随机选择并应用一个正面特质
        if positive_traits:
            positive_trait = random.choice(positive_traits)
            if positive_trait.name not in player.applied_traits:
                positive_trait.apply(player)  # 应用特质到玩家
                player.applied_traits.add(positive_trait.name)
                player.traits[positive_trait.name] = positive_trait
                print(f"应用正面特质: {positive_trait.name} 到玩家 {player.name}")

        # 随机选择并应用一个负面特质
        if negative_traits:
            negative_trait = random.choice(negative_traits)
            if negative_trait.name not in player.applied_traits:
                negative_trait.apply(player)  # 应用特质到玩家
                player.applied_traits.add(negative_trait.name)
                player.traits[negative_trait.name] = negative_trait
                print(f"应用负面特质: {negative_trait.name} 到玩家 {player.name}")

    def show_traits(self, player):
        """展示特质信息在Tkinter界面上"""
        # 创建弹出窗口
        trait_window = tk.Toplevel()
        trait_window.title("玩家特质信息")

        # 确保玩家有特质字典和已应用特质集合
        if hasattr(player, 'traits') and player.traits:
            traits = [(trait_name, trait) for trait_name, trait in player.traits.items()]
        else:
            traits = [("没有已应用的特质", None)]

        # 在窗口中展示特质信息（名称和描述）
        for trait_name, trait in traits:
            if trait is not None:
                label = tk.Label(trait_window, text=f"特质: {trait_name}\n描述: {trait.description}")
            else:
                label = tk.Label(trait_window, text=trait_name)  # 没有特质时的提示
            label.pack(pady=5)

    def reset_traits(self, player):
        """重置玩家的所有特质"""
        if hasattr(player, 'applied_traits'):
            player.applied_traits.clear()  # 清除所有已应用特质
        self.apply_to_player(player)  # 重新应用特质

    def register_trait_hooks(self, player):
        """注册特质影响钩子，使特质在玩家属性更新后自动应用"""

        def apply_traits_to_player(player):
            """应用玩家当前拥有的特质效果"""
            for trait_name in player.applied_traits:
                trait = self.traits.get(trait_name)
                # 确保特质存在并且是 Trait 实例
                if isinstance(trait, Trait):
                    trait.apply(player)
                else:
                    print(f"Error: {trait_name} 不是有效的 Trait 实例或未找到")

        # 注册钩子，确保每次调用玩家的 update_stats 后自动应用特质
        player.register_after_update_hook(apply_traits_to_player)