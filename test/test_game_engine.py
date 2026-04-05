import unittest
from unittest.mock import Mock
from game_engine import GameEngine
from common.character.player import Player


class TestGameEngine(unittest.TestCase):
    def setUp(self):
        # 模拟 game_state 和 dlc_manager
        self.game_state = Mock()
        self.dlc_manager = Mock()
        self.game_engine = GameEngine(self.game_state, self.dlc_manager)

        # 模拟玩家
        self.player = Player(1, "白夙")
        self.game_engine.current_player = self.player
        self.game_state.get_player.return_value = self.player

    def test_choose_at_main(self):
        result = self.game_engine.choose_at_main()
        self.assertEqual(result["title"], "天狐修炼纪")
        self.assertEqual(len(result["options"]), 3)
        self.assertEqual(result["options"][0]["text"], "旅途开始")

    def test_start_training(self):
        self.player.max_exp = 1000
        self.player.level = 1
        self.player.max_hp = 100
        self.player.max_mp = 50
        result = self.game_engine.start_training()
        self.assertEqual(result["status"], "success")
        self.assertIn("results", result)
        self.assertGreater(result["results"]["exp_gained"], 0)

    def test_save_game_no_player(self):
        self.game_engine.current_player = None
        result = self.game_engine.save_game(None, 1)
        self.assertEqual(result["error"], "No player to save")

    def test_debug_mod(self):
        result = self.game_engine.debug_mod()
        self.assertTrue(result["debug_mode"])
        result = self.game_engine.debug_mod()
        self.assertFalse(result["debug_mode"])


if __name__ == '__main__':
    unittest.main()
