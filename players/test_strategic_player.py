import unittest
from strategy_player import StrategicPlayer
import json

class TestStrategicPlayer(unittest.TestCase):

    def test_action_move(self):
        # Test action when it selects "move"
        player = StrategicPlayer()
        player.ships = {
            "w": {
                "type": "w",
                "position": [1, 1],
                "hp": 3
            }
        }
        player.opppnent_possible_positions = {
            's': [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)],
            'w': [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)],
            'c': [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)]
        }

        action_json = player.action()
        action_data = json.loads(action_json)

        self.assertIn("move", action_data)  # The result should contain "move" key
        self.assertIn("ship", action_data["move"])  # The "move" key should contain "ship" key
        self.assertIn("to", action_data["move"])  # The "move" key should contain "to" key

    def test_action_attack(self):
        # Test action when it selects "attack"
        player = StrategicPlayer()
        player.ships = {
            "w": {
                "type": "w",
                "position": [1, 1],
                "hp": 3
            }
        }
        player.opppnent_possible_positions = {
            's': [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)],
            'w': [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)],
            'c': [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)]
        }

        action_json = player.action()
        action_data = json.loads(action_json)

        self.assertIn("attack", action_data)  # The result should contain "attack" key
        self.assertIn("to", action_data["attack"])  # The "attack" key should contain "to" key

if __name__ == '__main__':
    unittest.main()
