from common.module.item import Buff

storybuff_library = {
    "强化": Buff(name="强化", buff_type="buff", user=None, target=None, duration=3, effect={"attribute": "attack", "value": 50}),
    "护盾": Buff(name="护盾", buff_type="buff", user=None, target=None, duration=3, effect={"attribute": "defense", "value": 50}),
}