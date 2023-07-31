


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

        self.opponent_possible_positions =  []
        self.opponent_HP = 6
        self.player_HP = 6
        
        
    def update_self_opponent_possible_positions(self, json_str):
        print("Received JSON Data in update_self_opponent_possible_positions:")
        print(json_str)
        json_data = json.loads(json_str) 
        if "result" in json_data:
            result = json_data["result"]
            if "attacked" in result:
                attacked_pos = result["attacked"]["position"]
                x, y = attacked_pos
                # Calculate the 8 cells around the attacked position
                around_attacked = [(x-1, y-1), (x-1, y), (x-1, y+1), (x, y-1), (x, y+1), (x+1, y-1), (x+1, y), (x+1, y+1)]
                print(around_attacked)
                # Add the 8 cells around the attacked position to possible opponent position list 
                for new_pos in around_attacked:
                    if new_pos not in self.opponent_possible_positions:
                        self.opponent_possible_positions.append(new_pos)
                if "hit" in result["attacked"] and "near" not in result:
                    self.player_HP -= 1
            elif "moved" in result:
                movement = result["moved"]["distance"]
                # Calculate new positions for each individual position in the opponent_possible_positions list
                for pos in self.opponent_possible_positions:
                    x, y = pos
                    new_pos = (x + movement[0], y + movement[1])
                    if new_pos in self.field and new_pos not in self.opponent_possible_positions:
                        self.opponent_possible_positions.append(new_pos)
            # Calculate total opponent's HP from their ship information
            elif "condition" in json_data and "enemy" in json_data["condition"]:
                enemy_info = json_data["condition"]["enemy"]
                self.opponent_HP = sum([ship_info["hp"] for ship_info in enemy_info.values()])


    def action(self):

        total_player_HP = sum(ship.hp for ship in self.ships.values())
        total_opponent_HP = self.opponent_HP


        if total_opponent_HP< total_player_HP:
            act = random.choices(["move", "attack"], [2, 5], k=1)[0]
        elif total_opponent_HP > total_player_HP:
            act = random.choices(["move", "attack"], [5, 2], k=1)[0]
        else:
            act = random.choice(["move", "attack"])

        print(f"Opponent's Possible Positions:")
        print(self.opponent_possible_positions)

        if act == "move":
            ship = random.choice(list(self.ships.values()))
            to = random.choice(self.field)
            while not ship.can_reach(to) or not self.overlap(to) is None:
                to = random.choice(self.field)
            return json.dumps(self.move(ship.type, to)) 
        elif act == "attack":
            if self.opponent_possible_positions:
                to = random.choice(self.opponent_possible_positions)
                while not self.can_attack(to):
                    to = random.choice(self.opponent_possible_positions)
                return json.dumps(self.attack(to))
            else:
                # Choose a random cell in the field since no opponent's positions are available
                to = random.choice(self.field)
                while not self.can_attack(to):
                    to = random.choice(self.field)
                return json.dumps(self.attack(to))
            

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
