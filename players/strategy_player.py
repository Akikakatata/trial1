import json
import os
import random
import socket
import sys
sys.path.append(os.getcwd())
from lib.player_base import Player, PlayerShip

class StrategicPlayer(Player):

    def __init__(self, seed=0):
        random.seed(seed)

        # Initialize the field as a 2x2 grid
        self.field = [[i, j] for i in range(Player.FIELD_SIZE)
                      for j in range(Player.FIELD_SIZE)]

        while True:
            # Randomly select three positions for the ships
            ps = random.sample(self.field, 3)
            self.positions = {'w': ps[0], 'c': ps[1], 's': ps[2]}

            # Validate that the ships are not in the same row, column, or diagonally adjacent
            validation = "fit"
            for i in range(len(self.positions)):
                for j in range(i + 1, len(self.positions)):
                    pos1 = self.positions[list(self.positions.keys())[i]]
                    pos2 = self.positions[list(self.positions.keys())[j]]
                    x1, y1 = pos1
                    x2, y2 = pos2

                    if ((x1 == x2) or (y1 == y2)) or (abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1):
                        validation = "unfit"
                        break  # No need to continue checking if one pair is unfit

                if validation == "unfit":
                    break

            if validation == "fit":
                super().__init__(self.positions)
                break

        self.opppnent_possible_positions = {
            's': [pos.copy() for pos in self.field],
            'w': [pos.copy() for pos in self.field],
            'c': [pos.copy() for pos in self.field]
        }
        
    def update_self_opponent_possible_positions(self, json_str):
        json_data = json.loads(json_str)
        if "result" in json_data:
            result = json_data["result"]
            if "attacked" in result:
                attacked_pos = result["attacked"]["position"]
                # Calculate the 9 cells around the attacked position
                around_attacked = [(x, y) for x in range(attacked_pos[0] - 1, attacked_pos[0] + 2)
                                for y in range(attacked_pos[1] - 1, attacked_pos[1] + 2)
                                if (x, y) in self.field]
                # Find the common positions between the previous self.opppnent_possible_positions
                # and the 9 cells around the attacked position
                self.opppnent_possible_positions = {k: [pos for pos in v if pos in around_attacked]
                                                    for k, v in self.opppnent_possible_positions.items()}
            elif "moved" in result:
                num_arrows = result["moved"]["distance"]
                # Update possible positions based on the direction and number of arrows
                for k, v in self.opppnent_possible_positions.items():
                    for pos in v:
                        new_pos = (pos[0] + num_arrows[0], pos[1] + num_arrows[1])
                        if new_pos in self.field:
                            pos[0], pos[1] = new_pos
                # Remove positions that are outside the field
                self.opppnent_possible_positions = {k: [pos for pos in v if pos in self.field]
                                                    for k, v in self.opppnent_possible_positions.items()}

    def action(self):
        act = random.choice(["move", "attack"])

        if act == "move":
            ship = random.choice(list(self.ships.values()))
            while True:
                to = random.choice(self.field)
                validation = "fit"
                for i in range(len(self.positions)):
                    for j in range(i + 1, len(self.positions)):
                        pos1 = list(to)
                        pos2 = self.positions[list(self.positions.keys())[j]]
                        x1, y1 = pos1
                        x2, y2 = pos2
                        if ((x1 == x2) or (y1 == y2)) or (abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1):
                            validation = "unfit"
                            break
                    if validation == "unfit":
                        break
                if validation == "fit":
                    return json.dumps(self.move(ship.type, to))

        elif act == "attack":
            ship_type = random.choice(list(self.opppnent_possible_positions.keys()))
            to = random.choice(self.opppnent_possible_positions[ship_type])
            while not self.can_attack(to):
                ship_type = random.choice(list(self.opppnent_possible_positions.keys()))
                to = random.choice(self.opppnent_possible_positions[ship_type])

            return json.dumps(self.attack(to))

def main(host, port, seed=0):
    assert isinstance(host, str) and isinstance(port, int)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        with sock.makefile(mode='rw', buffering=1) as sockfile:
            get_msg = sockfile.readline()
            print(get_msg)
            player = StrategicPlayer(seed=seed)
            sockfile.write(player.initial_condition() + '\n')

            while True:
                info = sockfile.readline().rstrip()
                print(info)
                if info == "your turn":
                    sockfile.write(player.action() + '\n')
                elif info == "waiting":
                    pass
                elif info == "you win":
                    break
                elif info == "you lose":
                    break
                elif info == "even":
                    break
                elif not info:
                    continue
                else:
                    print(info)
                    raise RuntimeError("unknown information " + info)

                # Receive opponent's action and update player's data
                get_msg = sockfile.readline()
                player.update_self_opponent_possible_positions(get_msg)

    print("Game over.")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Sample Player for Submaline Game")
    parser.add_argument(
        "host",
        metavar="H",
        type=str,
        help="Hostname of the server. E.g., localhost",
    )
    parser.add_argument(
        "port",
        metavar="P",
        type=int,
        help="Port of the server. E.g., 2000",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed of the player",
        required=False,
        default=0,
    )
    args = parser.parse_args()

    main(args.host, args.port, seed=args.seed)
