import json
import os
import random
import socket
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("StrategicPlayer")

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

        self.opppnent_possible_positions = []
        self.opnnent_certain_positions = []

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

                # Find the overlap between the previous possible positions and the 9 cells around the attacked position
                self.opponent_possible_positions = list(set(map(tuple, self.opponent_possible_positions)) & set(around_attacked))

                # Convert the positions back to lists
                self.opponent_possible_positions = [list(pos) for pos in self.opponent_possible_positions]

            elif "moved" in result:
                num_arrows = result["moved"]["distance"]
                # Create a copy of the current possible positions
                current_possible_positions = self.opponent_possible_positions.copy()

                # Clear the current possible positions list
                self.opponent_possible_positions.clear()

                # Update possible positions based on the direction and number of arrows
                for pos in current_possible_positions:
                    for i in range(1, num_arrows + 1):
                        new_pos = (pos[0] + i * num_arrows[0], pos[1] + i * num_arrows[1])
                        if new_pos in self.field:
                            self.opponent_possible_positions.append(new_pos)

                # Add the original positions back to the list
                self.opponent_possible_positions.extend(current_possible_positions)

                # Remove duplicate positions
                self.opponent_possible_positions = list(set(map(tuple, self.opponent_possible_positions)))

                # Convert the positions back to lists
                self.opponent_possible_positions = [list(pos) for pos in self.opponent_possible_positions]


    def action(self):
        act = random.choice(["move", "attack"])

        print(f"Opponent's Possible Positions:")
        for ship_type, positions in self.opppnent_possible_positions.items():
            print(f"{ship_type}: {positions}")

        if act == "move":
            ship = random.choice(list(self.ships.values()))
            while True:
                to = random.choice(self.field)
                while not ship.can_reach(to) or not self.overlap(to) is None:
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


def main(host, port, seed=0):
    assert isinstance(host, str) and isinstance(port, int)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((host, port))
        except Exception as e:
            logger.error(f"Error connecting to the server: {e}")
            sys.exit(1)

        with sock.makefile(mode='rw', buffering=1) as sockfile:
            get_msg = sockfile.readline()
            logger.debug(get_msg)
            player = StrategicPlayer(seed=seed)
            sockfile.write(player.initial_condition()+'\n')

            while True:
                info = sockfile.readline().rstrip()
                logger.debug(info)
                if info == "your turn":
                    sockfile.write(player.action()+'\n')
                    get_msg = sockfile.readline()
                    player.update_self_opponent_possible_positions(get_msg)
                elif info == "waiting":
                    get_msg = sockfile.readline()
                    player.update_self_opponent_possible_positions(get_msg)
                elif info == "you win":
                    logger.info("You win!")
                    break
                elif info == "you lose":
                    logger.info("You lose!")
                    break
                elif info == "even":
                    logger.info("It's a tie (even)!")
                    break
                elif not info:
                    continue
                else:
                    logger.error("Unknown information received: " + info)
                    raise RuntimeError("Unknown information: " + info)

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

    try:
        args = parser.parse_args()
    except SystemExit as e:
        logger.error("Error parsing command-line arguments:", e)
        sys.exit(1)

    main(args.host, args.port, seed=args.seed)