import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())

from lib.player_base import Player, PlayerShip

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("StrategicPlayer")

class StraPlayer(Player):
    def __init__(self, seed=0):
        while True:
            # Initialize the field as a 2x2 grid
            self.field = [[i, j] for i in range(Player.FIELD_SIZE)
                          for j in range(Player.FIELD_SIZE)]

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
                self.opponent_possible_positions = []
                break
        
        self.oppo_poss_posi_s = []
        self.oppo_poss_posi_c = []
        self.oppo_poss_posi_w = []
        self.my_HP = 6
        self.opponent_HP = 6
        super().__init__(self.positions)

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
                # Add the 8 cells around the attacked position to all three opponent's possible position lists
                for new_pos in around_attacked:
                    if new_pos not in self.oppo_poss_posi_s:
                        self.oppo_poss_posi_s.append(new_pos)
                    if new_pos not in self.oppo_poss_posi_w:
                        self.oppo_poss_posi_w.append(new_pos)
                    if new_pos not in self.oppo_poss_posi_c:
                        self.oppo_poss_posi_c.append(new_pos)
            elif "moved" in result:
                moved_ship = result["moved"]["ship"]
                movement = result["moved"]["distance"]
                # Update positions in the appropriate opponent's possible position list based on the ship's movement
                if moved_ship == "s":
                    self.oppo_poss_posi_s = [(x + movement[0], y + movement[1]) for x, y in self.oppo_poss_posi_s]
                elif moved_ship == "w":
                    self.oppo_poss_posi_w = [(x + movement[0], y + movement[1]) for x, y in self.oppo_poss_posi_w]
                elif moved_ship == "c":
                    self.oppo_poss_posi_c = [(x + movement[0], y + movement[1]) for x, y in self.oppo_poss_posi_c]
            #calculate HP of opponent and myself 
        if "condition" in json_data:
            condition_data = json_data["condition"]
            if "me" in condition_data:
                me_data = condition_data["me"]
                self.my_HP = me_data["w"]["hp"] + me_data["c"]["hp"] + me_data["s"]["hp"]
            if "enemy" in condition_data:
                enemy_data = condition_data["enemy"]
                self.opponent_HP = enemy_data["w"]["hp"] + enemy_data["c"]["hp"] + enemy_data["s"]["hp"]        

    def update_my_attack(self, json_str):
        print("Received JSON Data in update_my_attack:")
        print(json_str)
        json_data = json.loads(json_str)
        if "result" in json_data:
            result = json_data["result"]
            if "attacked" in result:
                if "near" in result["attacked"]:
                    attacked_pos = result["attacked"]["position"]
                    x, y = attacked_pos
                    # Calculate the 8 cells around the attacked position
                    around_attacked = [(x-1, y-1), (x-1, y), (x-1, y+1), (x, y-1), (x, y+1), (x+1, y-1), (x+1, y), (x+1, y+1)]
                    print(around_attacked)
                    # Add the 8 cells around the attacked position to the corresponding opponent's possible position list
                    for new_pos in around_attacked:
                        if "w" in result["attacked"]["near"] and new_pos not in self.oppo_poss_posi_w:
                            self.oppo_poss_posi_w.append(new_pos)
                            self.oppo_poss_posi_w.remove(attacked_pos)
                        if "c" in result["attacked"]["near"] and new_pos not in self.oppo_poss_posi_c:
                            self.oppo_poss_posi_c.append(new_pos)
                            self.oppo_poss_posi_c.remove(attacked_pos)
                        if "s" in result["attacked"]["near"] and new_pos not in self.oppo_poss_posi_s:
                            self.oppo_poss_posi_s.append(new_pos)
                            self.oppo_poss_posi_s.remove(attacked_pos)
                if "hit" in result["attacked"]: 
                    attacked_pos = result["attacked"]["position"]
                    if "w" in result["attacked"]["hit"]:
                        self.oppo_poss_posi_w = []
                        self.oppo_poss_posi_w.append(attacked_pos)
                    if "c" in result["attacked"]["hit"]:
                        self.oppo_poss_posi_c = []
                        self.oppo_poss_posi_c.append(attacked_pos)
                    if "s" in result["attacked"]["hit"]:
                        self.oppo_poss_posi_s = []
                        self.oppo_poss_posi_s.append(attacked_pos)
                if "hit" or "near" not in result["attacked"]: 
                    if attacked_pos in self.oppo_poss_posi_w:
                        self.oppo_poss_posi_w.remove(attacked_pos)
                    if attacked_pos in self.oppo_poss_posi_c:
                        self.oppo_poss_posi_c.remove(attacked_pos)
                    if attacked_pos in self.oppo_poss_posi_s:
                        self.oppo_poss_posi_s.remove(attacked_pos)
            else: 
                pass

        if "condition" in json_data:
            condition_data = json_data["condition"]
            if "me" in condition_data:
                me_data = condition_data["me"]
                self.my_HP = me_data["w"]["hp"] + me_data["c"]["hp"] + me_data["s"]["hp"]
            if "enemy" in condition_data:
                enemy_data = condition_data["enemy"]
                self.opponent_HP = enemy_data["w"]["hp"] + enemy_data["c"]["hp"] + enemy_data["s"]["hp"]        
    
    def action(self):
        if self.opponent_HP< self.my_HP:
            act = random.choices(["move", "attack"], [2, 5], k=1)[0]
        elif self.opponent_HP > self.my_HP:
            act = random.choices(["move", "attack"], [5, 2], k=1)[0]
        else:
            act = random.choice(["move", "attack"])

        if act == "attack":
            if len(self.oppo_poss_posi_s) == 1: 
                to = self.oppo_poss_posi_s[0]
                if self.can_attack(to):
                    return json.dumps(self.attack(to))
            elif len(self.oppo_poss_posi_w) == 1: 
                to = self.oppo_poss_posi_w[0]
                if self.can_attack(to):
                    return json.dumps(self.attack(to))
            elif len(self.oppo_poss_posi_c) == 1:
                to = self.oppo_poss_posi_c[0]
                if self.can_attack(to):
                    return json.dumps(self.attack(to))
            else:
                combined_list = self.oppo_poss_posi_s + self.oppo_poss_posi_w + self.oppo_poss_posi_c
                to = random.choice(combined_list)
                while not self.can_attack(to):
                    to = random.choice(combined_list)
                return json.dumps(self.attack(to))

        if act == "move":
            ship = random.choice(list(self.ships.values()))
            to = random.choice(self.field)
            while not ship.can_reach(to) or self.is_adjacent_to_other_ship(to):
                to = random.choice(self.field)
            return json.dumps(self.move(ship.type, to))

    def is_adjacent_to_other_ship(self, position):
        for ship_position in self.positions.values():
            x, y = position
            x_ship, y_ship = ship_position
            if ((x == x_ship) or (y == y_ship)) or (abs(x - x_ship) <= 1 and abs(y - y_ship) <= 1):
                return True
        return False


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
            player = StraPlayer(seed=seed)
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
