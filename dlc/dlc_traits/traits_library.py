from .traits import Trait

traits_library = {
    "稳重": Trait(name="稳重", description="拥有此特质的角色一般阅历丰富，拥有者气血上限增加5%", nature="positive", multiplier_effects={"max_hp": 0.05}),

    "冷静": Trait(name="冷静", description="拥有此特质的角色一般不会受到情绪波动的影响，拥有者法力上限增加5%", nature="positive", multiplier_effects={"max_mp": 0.05}),

    "勇敢": Trait(name="勇敢", description="拥有此特质的角色一般更加具有冒险精神，拥有者攻击力增加5%", nature="positive", multiplier_effects={"attack": 0.05}),

    "谨慎": Trait(name="谨慎", description="拥有此特质的角色一般更关注于事情的细节，拥有者暴击增加5%", nature="positive", numeric_effects={"crit": 5}),

    "坚毅": Trait(name="坚毅", description="拥有此特质的角色一般更能忍受非常之磨难，拥有者抗性增加3%", nature="positive", numeric_effects={"resistance": 3}),

    "多智": Trait(name="多智", description="拥有此特质的角色一般思维敏捷善于取巧，拥有者穿透增加3%", nature="positive", numeric_effects={"penetration": 3}),

    "懒惰": Trait(name="懒惰", description="拥有此特质的角色一般更疏于修炼，拥有者气血上限减少5%", nature="negative", multiplier_effects={"max_hp": -0.05}),

    "自负": Trait(name="自负", description="拥有此特质的角色一般相信自己无所不能，拥有者法力上限减少5%", nature="negative", multiplier_effects={"max_mp": -0.05}),

    "胆小": Trait(name="胆小", description="拥有此特质的角色一般畏首畏尾，拥有者攻击力减少5%", nature="negative", multiplier_effects={"attack": -0.05}),

    "多疑": Trait(name="多疑", description="拥有此特质的角色一般很难相信他人，拥有者防御力减少5%", nature="negative", multiplier_effects={"defense": -0.05}),

}