# tests/test_map_dungeon.py
import unittest
from unittest.mock import Mock, patch
import logging
from common.interface.map_interface_new import MapInterface
from common.interface.dungeon_interface_new import DungeonInterface
from game_engine import GameEngine
from common.interact.map_interact import Map
from common.interact.dungeon_interact import Dungeon, DungeonFloor
from common.interface.bag_interface_new import BagInterface


class TestMapDungeon(unittest.TestCase):
    def setUp(self):
        # 设置日志（避免日志重复配置）
        logging.getLogger('').handlers = []  # 清空所有日志处理器
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_game.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Setting up test environment")

        # 模拟 player
        self.player = Mock()
        self.player.name = "TestPlayer"
        self.player.hp = 100
        self.player.exp = 1000
        self.player.inventory = []
        self.player.npcs_removed = []
        self.player.highest_floor = {}
        self.player.dungeons_cleared = set()
        self.player.accepted_tasks = []
        self.player.has_item.return_value = True

        # 模拟 game_state
        self.game_state = Mock()
        self.game_state.get_player.return_value = self.player

        # 模拟 Map
        self.map_obj = Mock(spec=Map)
        self.map_obj.number = 1
        self.map_obj.name = "TestMap"
        self.map_obj.description = "A test map"
        self.map_obj.adjacent_maps = {2: {"distance": 10, "direction": "双向"}}
        self.map_obj.npcs = [Mock(number=1, name="TestNPC", description="A test NPC")]
        self.map_obj.battles = [[Mock(name="Enemy1")]]
        self.map_obj.collectible_items = {
            "草药": {"item": Mock(name="草药"), "success_rate": 0.8, "quantity_range": (1, 3)}
        }
        self.map_obj.dungeons = [Mock(number=1, name="TestDungeon", description="A test dungeon")]
        self.map_obj.can_enter.return_value = (True, "可以进入地图")
        self.map_obj.get_npcs.return_value = [{"number": 1, "name": "TestNPC", "description": "A test NPC"}]
        self.map_obj.get_battles.return_value = [{"index": 0, "enemies": ["Enemy1"]}]
        self.map_obj.get_collectibles.return_value = [{"name": "草药", "success_rate": 0.8, "quantity_range": (1, 3)}]
        self.map_obj.get_dungeons.return_value = [{"number": 1, "name": "TestDungeon", "description": "A test dungeon"}]
        self.game_state.get_map.return_value = self.map_obj

        # 模拟 Dungeon 和 DungeonFloor
        self.floor = Mock(spec=DungeonFloor)
        self.floor.number = 1
        self.floor.description = "First floor"
        self.floor.npc = None
        self.floor.enemies = [Mock(name="Enemy1")]
        self.floor.completed = False
        self.dungeon = Mock(spec=Dungeon)
        self.dungeon.number = 1
        self.dungeon.name = "TestDungeon"
        self.dungeon.description = "A test dungeon"
        self.dungeon.floors = [self.floor]
        self.dungeon.highest_floor = 0
        self.dungeon.completed = False
        self.dungeon.can_replay_after_completion = True
        # 不设置 can_enter，假设无需权限检查
        self.game_state.get_dungeon.return_value = self.dungeon

        # 模拟 Battle
        self.battle = Mock()
        self.battle.run_battle.return_value = "win"
        self.battle.check_battle_status.return_value = "win"

        # 模拟 NPC
        self.npc = Mock()
        self.npc.number = 1
        self.npc.name = "TestNPC"
        self.game_state.get_npc.return_value = self.npc

        # 模拟 Task
        self.task = Mock()
        self.task.check_completion.return_value = False
        self.player.accepted_tasks = [self.task]

        # 初始化 GameEngine
        self.dlc_manager = Mock()
        self.game_engine = GameEngine(self.game_state, self.dlc_manager)
        self.game_engine.current_player = self.player

    def test_map_interface_get_map_menu(self):
        """测试 MapInterface.get_map_menu"""
        map_interface = MapInterface(self.player, self.game_state)
        self.game_state.get_available_maps.return_value = [self.map_obj]

        result = map_interface.get_map_menu()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "地图选择")
        self.assertEqual(len(result["maps"]), 1)
        self.assertEqual(result["maps"][0]["id"], 1)
        self.assertEqual(result["maps"][0]["name"], "TestMap")

    def test_map_interface_explore_area_success(self):
        """测试 MapInterface.explore_area 成功进入地图"""
        map_interface = MapInterface(self.player, self.game_state)

        result = map_interface.explore_area(1)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "正在探索 TestMap: A test map")
        self.assertEqual(result["map_id"], 1)
        self.assertEqual(len(result["npcs"]), 1)
        self.assertEqual(result["npcs"][0]["name"], "TestNPC")
        self.assertEqual(len(result["battles"]), 1)
        self.assertEqual(len(result["collectibles"]), 1)
        self.assertEqual(len(result["dungeons"]), 1)

    def test_map_interface_explore_area_no_access(self):
        """测试 MapInterface.explore_area 无权限进入"""
        map_interface = MapInterface(self.player, self.game_state)
        self.map_obj.can_enter.return_value = (False, "缺少通行证")

        result = map_interface.explore_area(1)

        self.assertEqual(result["error"], "缺少通行证")

    def test_map_interface_interact_with_npc(self):
        """测试 MapInterface.interact_with_npc"""
        map_interface = MapInterface(self.player, self.game_state)

        result = map_interface.interact_with_npc(1, 1)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "与 TestNPC 交互")
        self.assertEqual(result["next_action"], "npc")
        self.assertEqual(result["npc_id"], 1)

    def test_map_interface_collect_item_success(self):
        """测试 MapInterface.collect_item 采集成功"""
        map_interface = MapInterface(self.player, self.game_state)
        self.map_obj.collect_item.return_value = (True, {"item": "草药", "quantity": 2})

        result = map_interface.collect_item(1, "草药")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "成功采集到 草药 x 2")
        self.assertEqual(result["item"], "草药")
        self.assertEqual(result["quantity"], 2)
        self.assertEqual(result["next_action"], "bag")

    def test_map_interface_collect_item_failure(self):
        """测试 MapInterface.collect_item 采集失败"""
        map_interface = MapInterface(self.player, self.game_state)
        self.map_obj.collect_item.return_value = (False, {"error": "采集 草药 失败"})

        result = map_interface.collect_item(1, "草药")

        self.assertEqual(result["error"], "采集 草药 失败")

    def test_map_interface_start_battle_win(self):
        """测试 MapInterface.start_battle 战斗胜利"""
        map_interface = MapInterface(self.player, self.game_state)
        self.map_obj.handle_battle.return_value = {"result": "win"}

        result = map_interface.start_battle(1, 0)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "TestPlayer 战胜了敌人！")
        self.assertEqual(result["battle_result"], "win")
        self.assertIsNone(result["next_action"])

    def test_map_interface_start_battle_loss(self):
        """测试 MapInterface.start_battle 战斗失败"""
        map_interface = MapInterface(self.player, self.game_state)
        self.map_obj.handle_battle.return_value = {
            "result": "loss",
            "hp": 1,
            "exp_loss": 50,
            "exp_loss_percentage": 0.05
        }

        result = map_interface.start_battle(1, 0)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "战斗失败，你被野怪击晕！")
        self.assertEqual(result["battle_result"], "loss")
        self.assertEqual(result["next_action"], "map")
        self.assertEqual(result["loss_info"]["hp"], 1)
        self.assertEqual(result["loss_info"]["exp_loss"], 50)

    def test_map_interface_enter_dungeon(self):
        """测试 MapInterface.enter_dungeon"""
        map_interface = MapInterface(self.player, self.game_state)

        result = map_interface.enter_dungeon(1, 1)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "进入秘境 TestDungeon")
        self.assertEqual(result["next_action"], "dungeon")
        self.assertEqual(result["dungeon_id"], 1)

    def test_dungeon_interface_get_dungeon_menu(self):
        """测试 DungeonInterface.get_dungeon_menu"""
        dungeon_interface = DungeonInterface(self.player, self.game_state)
        self.game_state.get_available_dungeons.return_value = [self.dungeon]

        result = dungeon_interface.get_dungeon_menu()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "秘境选择")
        self.assertEqual(len(result["dungeons"]), 1)
        self.assertEqual(result["dungeons"][0]["id"], 1)
        self.assertEqual(result["dungeons"][0]["name"], "TestDungeon")

    def test_dungeon_interface_enter_dungeon(self):
        """测试 DungeonInterface.enter_dungeon"""
        dungeon_interface = DungeonInterface(self.player, self.game_state)
        self.dungeon.apply_npc_affection_impact.return_value = []

        result = dungeon_interface.enter_dungeon(1)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "进入了秘境: TestDungeon - A test dungeon")
        self.assertEqual(result["dungeon_id"], 1)
        self.assertEqual(len(result["floors"]), 1)
        self.assertEqual(result["floors"][0]["number"], 1)

    def test_dungeon_interface_enter_floor_battle_win(self):
        """测试 DungeonInterface.enter_floor 战斗胜利"""
        dungeon_interface = DungeonInterface(self.player, self.game_state)
        self.floor.get_rewards.return_value = [{"type": "item", "item": Mock(name="宝物"), "quantity": 1}]
        self.floor.apply_rewards.return_value = [{"type": "item", "name": "宝物", "quantity": 1}]
        self.floor.apply_buffs.return_value = []

        with patch('common.interact.dungeon_interface_new.Battle', return_value=self.battle):
            result = dungeon_interface.enter_floor(1, 1)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "楼层 1 完成！战斗胜利！")
        self.assertEqual(result["battle_result"], "win")
        self.assertEqual(result["next_action"], "bag")
        self.assertEqual(len(result["rewards"]), 1)
        self.assertEqual(result["rewards"][0]["name"], "宝物")

    def test_dungeon_interface_enter_floor_battle_loss(self):
        """测试 DungeonInterface.enter_floor 战斗失败"""
        dungeon_interface = DungeonInterface(self.player, self.game_state)
        self.battle.run_battle.return_value = "loss"
        self.battle.check_battle_status.return_value = "loss"
        self.dungeon.handle_loss.return_value = {"hp": 1, "exp_loss": 50, "exp_loss_percentage": 0.05}
        self.floor.apply_buffs.return_value = []

        with patch('common.interact.dungeon_interface_new.Battle', return_value=self.battle):
            result = dungeon_interface.enter_floor(1, 1)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "楼层 1 战斗失败！")
        self.assertEqual(result["battle_result"], "loss")
        self.assertEqual(result["next_action"], "map")
        self.assertEqual(result["loss_info"]["hp"], 1)
        self.assertEqual(result["loss_info"]["exp_loss"], 50)

    def test_dungeon_interface_enter_floor_with_npc(self):
        """测试 DungeonInterface.enter_floor 遇到 NPC"""
        dungeon_interface = DungeonInterface(self.player, self.game_state)
        self.floor.npc = Mock(number=1, name="TestNPC")

        result = dungeon_interface.enter_floor(1, 1)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "遇到了 NPC: TestNPC")
        self.assertEqual(result["next_action"], "npc")
        self.assertEqual(result["npc_id"], 1)

    def test_game_engine_process_map_choice_explore(self):
        """测试 GameEngine.process_map_choice 探索地图"""
        result = self.game_engine.process_map_choice(1, {"map_id": 1})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "正在探索 TestMap: A test map")
        self.assertEqual(result["map_id"], 1)

    def test_game_engine_process_map_choice_collect_with_task(self):
        """测试 GameEngine.process_map_choice 采集触发任务"""
        self.map_obj.collect_item.return_value = (True, {"item": "草药", "quantity": 2})
        self.task.check_completion.return_value = True

        result = self.game_engine.process_map_choice(3, {"map_id": 1, "item_name": "草药"})

        self.assertEqual(result["title"], "任务界面")  # 假设 TaskInterface.get_task_menu 返回此标题
        self.task.check_completion.assert_called_with(self.player)

    def test_game_engine_process_map_choice_npc(self):
        """测试 GameEngine.process_map_choice NPC 交互跳转"""
        with patch.object(self.game_engine, 'process_npc_interaction') as mock_npc:
            mock_npc.return_value = {"status": "success", "message": "NPC 交互菜单"}
            result = self.game_engine.process_map_choice(2, {"map_id": 1, "npc_id": 1})

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["message"], "NPC 交互菜单")
            mock_npc.assert_called_with(1)

    def test_game_engine_process_map_choice_dungeon(self):
        """测试 GameEngine.process_map_choice 秘境跳转"""
        with patch.object(DungeonInterface, 'enter_dungeon') as mock_dungeon:
            mock_dungeon.return_value = {"status": "success", "message": "进入了秘境"}
            result = self.game_engine.process_map_choice(5, {"map_id": 1, "dungeon_id": 1})

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["message"], "进入了秘境")
            mock_dungeon.assert_called_with(1)

    def test_game_engine_process_dungeon_choice_floor_bag(self):
        """测试 GameEngine.process_dungeon_choice 楼层奖励跳转背包"""
        self.floor.get_rewards.return_value = [{"type": "item", "item": Mock(name="宝物"), "quantity": 1}]
        self.floor.apply_rewards.return_value = [{"type": "item", "name": "宝物", "quantity": 1}]
        self.floor.apply_buffs.return_value = []

        with patch('common.interact.dungeon_interface_new.Battle', return_value=self.battle):
            with patch.object(BagInterface, 'get_inventory') as mock_bag:
                mock_bag.return_value = {"items": ["宝物"]}
                result = self.game_engine.process_dungeon_choice(2, {"dungeon_id": 1, "floor_number": 1})

                self.assertEqual(result["items"], ["宝物"])
                mock_bag.assert_called_once()

    def test_game_engine_process_dungeon_choice_floor_map(self):
        """测试 GameEngine.process_dungeon_choice 战斗失败跳转地图"""
        self.battle.run_battle.return_value = "loss"
        self.battle.check_battle_status.return_value = "loss"
        self.dungeon.handle_loss.return_value = {"hp": 1, "exp_loss": 50, "exp_loss_percentage": 0.05}
        self.floor.apply_buffs.return_value = []

        with patch('common.interact.dungeon_interface_new.Battle', return_value=self.battle):
            with patch.object(MapInterface, 'get_map_menu') as mock_map:
                mock_map.return_value = {"title": "地图选择"}
                result = self.game_engine.process_dungeon_choice(2, {"dungeon_id": 1, "floor_number": 1})

                self.assertEqual(result["title"], "地图选择")
                mock_map.assert_called_once()


if __name__ == '__main__':
    unittest.main()