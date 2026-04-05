from common.module.battle import Battle
from .enemy_library import enemy_library
from .boss_library import boss_library
from .ally_library import ally_library


storyfight_library = {
    1: Battle(player=None, allies=[ally_library[700001]], enemies=[boss_library[600001], enemy_library[500000]]),
}
