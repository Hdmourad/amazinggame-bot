import socket
import time
import math
from collections import deque

HOST = "127.0.0.1"
PORT = 16210
NAME = "MouradSmartBot"

GRID = 15
GOAL = (14, 14)

MAX_SPEED_EXPLORE = 0.45
MAX_SPEED_RACE = 0.75

TURN_THRESHOLD = 15


class SmartBot:

    def __init__(self):

        self.visited = set()

        self.walls = set()

        self.open_paths = set()

        self.race_mode = False

        self.last_explore = 1

        self.turn_memory = None

        self.blocked_counter = 0

    def parse_sensors(self, line):

        parts = line.split()

        if len(parts) != 10:
            return None

        return {
            "time": float(parts[0]),
            "explore": int(parts[1]),
            "x": float(parts[2]),
            "y": float(parts[3]),
            "orientation": float(parts[4]) % 360,
            "speed": float(parts[5]),
            "front": float(parts[6]),
            "right": float(parts[7]),
            "rear": float(parts[8]),
            "left": float(parts[9]),
        }

    def current_cell(self, x, y):

        return int(math.floor(x)), int(math.floor(y))

    def normalize_edge(self, a, b):

        return tuple(sorted([a, b]))

    def in_grid(self, cell):

        x, y = cell

        return 0 <= x < GRID and 0 <= y < GRID

    def direction_vector(self, orientation):

        if orientation < 45 or orientation >= 315:
            return (1, 0)

        if 45 <= orientation < 135:
            return (0, -1)

        if 135 <= orientation < 225:
            return (-1, 0)

        return (0, 1)

    def rotate_right(self, dx, dy):

        return (-dy, dx)

    def rotate_left(self, dx, dy):

        return (dy, -dx)

    def update_map(self, info):

        current = self.current_cell(info["x"], info["y"])

        dx, dy = self.direction_vector(info["orientation"])

        front_cell = (current[0] + dx, current[1] + dy)

        rdx, rdy = self.rotate_right(dx, dy)
        right_cell = (current[0] + rdx, current[1] + rdy)

        ldx, ldy = self.rotate_left(dx, dy)
        left_cell = (current[0] + ldx, current[1] + ldy)

        if info["front"] < 0.50:
            self.walls.add(self.normalize_edge(current, front_cell))
        else:
            self.open_paths.add(self.normalize_edge(current, front_cell))

        if info["right"] < 0.50:
            self.walls.add(self.normalize_edge(current, right_cell))
        else:
            self.open_paths.add(self.normalize_edge(current, right_cell))

        if info["left"] < 0.50:
            self.walls.add(self.normalize_edge(current, left_cell))
        else:
            self.open_paths.add(self.normalize_edge(current, left_cell))

    def neighbors(self, cell):

        x, y = cell

        possible = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ]

        result = []

        for n in possible:

            if not self.in_grid(n):
                continue

            edge = self.normalize_edge(cell, n)

            if edge in self.walls:
                continue

            result.append(n)

        return result

    def bfs(self, start, goal):

        queue = deque([(start, [])])

        visited = {start}

        while queue:

            current, path = queue.popleft()

            if current == goal:
                return path

            for n in self.neighbors(current):

                if n not in visited:

                    visited.add(n)

                    queue.append((n, path + [n]))

        return []

    def exploration_target(self, start):

        queue = deque([start])

        seen = {start}

        while queue:

            current = queue.popleft()

            if current not in self.visited:
                return current

            for n in self.neighbors(current):

                if n not in seen:

                    seen.add(n)

                    queue.append(n)

        return GOAL

    def angle_to_cell(self, x, y, target):

        tx, ty = target

        cx = tx + 0.5
        cy = ty + 0.5

        return (-math.degrees(math.atan2(cy - y, cx - x))) % 360

    def angle_diff(self, target, current):

        return (target - current + 180) % 360 - 180

    def choose_command(self, info):

        current = self.current_cell(info["x"], info["y"])

        self.visited.add(current)

        speed = info["speed"]

        front = info["front"]
        right = info["right"]
        left = info["left"]

        max_speed = (
            MAX_SPEED_RACE
            if self.race_mode
            else MAX_SPEED_EXPLORE
        )

        danger_distance = 0.45 + speed * 1.4

        safe_distance = 1.0 + speed * 1.0

        # =========================
        # ANTI COLLISION
        # =========================

        if front < danger_distance:

            if speed > 0.05:
                return "DECELERATE"

            if right > left and right > 0.60:
                self.turn_memory = "RIGHT"
                return "TURN_RIGHT"

            if left >= right and left > 0.60:
                self.turn_memory = "LEFT"
                return "TURN_LEFT"

            if self.turn_memory == "RIGHT":
                return "TURN_RIGHT"

            return "TURN_LEFT"

        # =========================
        # EXPLORATION
        # =========================

        if not self.race_mode:

            if front > safe_distance:

                if speed < max_speed:
                    return "ACCELERATE"

            if right > front + 0.5 and right > left:

                if speed > 0.10:
                    return "DECELERATE"

                return "TURN_RIGHT"

            if left > front + 0.5 and left > right:

                if speed > 0.10:
                    return "DECELERATE"

                return "TURN_LEFT"

            if speed < max_speed:
                return "ACCELERATE"

            return "ACCELERATE"

        # =========================
        # MODE COURSE
        # =========================

        path = self.bfs(current, GOAL)

        if path:

            next_cell = path[0]

            target_angle = self.angle_to_cell(
                info["x"],
                info["y"],
                next_cell
            )

            diff = self.angle_diff(
                target_angle,
                info["orientation"]
            )

            if abs(diff) > TURN_THRESHOLD:

                if speed > 0.10:
                    return "DECELERATE"

                if diff > 0:
                    return "TURN_LEFT"

                return "TURN_RIGHT"

        if front > safe_distance:

            if speed < max_speed:
                return "ACCELERATE"

        if front < 0.90 and speed > 0.15:
            return "DECELERATE"

        return "ACCELERATE"

    def run(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        while True:

            try:
                sock.connect((HOST, PORT))
                break

            except OSError:

                print("Serveur pas prêt...")
                time.sleep(1)

        f = sock.makefile("rw")

        f.write(NAME + "\n")
        f.flush()

        print("CONNECTED")

        while True:

            f.write("GET_SENSORS\n")
            f.flush()

            line = f.readline().strip()

            if not line:
                break

            if line == "BLOCKED":

                print("BLOCKED")

                time.sleep(0.5)

                continue

            info = self.parse_sensors(line)

            if not info:
                continue

            # changement phase

            if self.last_explore == 1 and info["explore"] == 0:

                print("\n===== MODE COURSE =====\n")

                self.race_mode = True

            self.last_explore = info["explore"]

            self.update_map(info)

            command = self.choose_command(info)

            f.write(command + "\n")
            f.flush()

            response = f.readline().strip()

            print(
                f"MODE={'RACE' if self.race_mode else 'EXPLORE'} "
                f"POS={self.current_cell(info['x'], info['y'])} "
                f"ORI={info['orientation']:.0f} "
                f"SPD={info['speed']:.2f} "
                f"F={info['front']:.2f} "
                f"R={info['right']:.2f} "
                f"L={info['left']:.2f} "
                f"CMD={command} "
                f"REP={response}"
            )

            time.sleep(0.05)

        sock.close()


if __name__ == "__main__":

    bot = SmartBot()

    bot.run()