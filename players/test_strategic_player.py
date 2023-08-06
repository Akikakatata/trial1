import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())

from lib.player_base import Player, PlayerShip

class CustomPlayer(Player):
    def action(self):
        act = random.choice(["move", "attack"])

        if act == "move":
            ship = random.choice(list(self.positions.keys()))
            to = random.choice(self.field)
            while not self.can_move_to_position(ship, to):
                to = random.choice(self.field)
            print(f"{ship} moved from {self.positions[ship]} to {to}")
            self.positions[ship] = to
            return json.dumps({"moved": {"ship": ship, "distance": [to[0] - self.positions[ship][0], to[1] - self.positions[ship][1]]}})
        else:
            # Implement your attack logic here
            # For example, you can randomly choose a target position to attack
            target_pos = random.choice(self.field)
            print(f"Attacking position: {target_pos}")
            return json.dumps({"attack": {"position": target_pos}})

# Create an instance of the Player class
player = CustomPlayer()

print("Action Result:", player.action())
