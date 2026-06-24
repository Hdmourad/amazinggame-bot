import math
import socket
import sys
import time
from collections import defaultdict, deque

HOST = "127.0.0.1"
PORT = 16210
NAME = "AM_MH"

if len(sys.argv) >= 4:
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])
    NAME = sys.argv[3]

GRID = 15
GOAL = (14, 14)

MAX_SPEED_EXPLORE = 1.10
MAX_SPEED_RACE = 1.35

ANGLE_OK = 8
STOP_SPEED = 0.10


class SmartBot:
    def __init__(self):
        self.last_explore = 1
        self.race_mode = False

        self.visited = set()
        self.visit_count = defaultdict(int)
        self.walls = set()
        self.open_paths = set()

        self.last_cell = None
        self.stuck = 0
        self.last_turn = "RIGHT"
        self.pending_sensor = None

    def parse_sensors(self, line):
        p = line.split()
        if len(p) != 10:
            return None

        return {
            "time": float(p[0]),
            "explore": int(p[1]),
            "x": float(p[2]),
            "y": float(p[3]),
            "orientation": float(p[4]) % 360,
            "speed": float(p[5]),
            "front": float(p[6]),
            "right": float(p[7]),
            "rear": float(p[8]),
            "left": float(p[9]),
        }

    def cell(self, x, y):
        return int(math.floor(x)), int(math.floor(y))

    def in_grid(self, c):
        return 0 <= c[0] < GRID and 0 <= c[1] < GRID

    def edge(self, a, b):
        return tuple(sorted([a, b]))

    def dir_vec(self, ori):
        if ori < 45 or ori >= 315:
            return (1, 0)
        if ori < 135:
            return (0, -1)
        if ori < 225:
            return (-1, 0)
        return (0, 1)

    def right_vec(self, dx, dy):
        return (-dy, dx)

    def left_vec(self, dx, dy):
        return (dy, -dx)

    def update_map(self, s):
        c = self.cell(s["x"], s["y"])
        dx, dy = self.dir_vec(s["orientation"])

        dirs = {
            "front": (dx, dy),
            "right": self.right_vec(dx, dy),
            "left": self.left_vec(dx, dy),
        }

        for side, v in dirs.items():
            n = (c[0] + v[0], c[1] + v[1])

            if not self.in_grid(n):
                continue

            e = self.edge(c, n)

            if s[side] < 0.50:
                self.walls.add(e)
                self.open_paths.discard(e)
            elif e not in self.walls:
                self.open_paths.add(e)

    def neighbors(self, c, known_only=False):
        x, y = c
        possible = [
            (x + 1, y),
            (x, y + 1),
            (x - 1, y),
            (x, y - 1),
        ]

        result = []

        for n in possible:
            if not self.in_grid(n):
                continue

            e = self.edge(c, n)

            if e in self.walls:
                continue

            if known_only and e not in self.open_paths:
                continue

            result.append(n)

        return result

    def bfs(self, start, goal, known_only=False):
        q = deque([(start, [])])
        seen = {start}

        while q:
            c, path = q.popleft()

            if c == goal:
                return path

            for n in self.neighbors(c, known_only):
                if n not in seen:
                    seen.add(n)
                    q.append((n, path + [n]))

        return []

    def count_frontier(self, c):
        score = 0

        for n in self.neighbors(c, known_only=False):
            if n not in self.visited:
                score += 1

            e = self.edge(c, n)

            if e not in self.walls and e not in self.open_paths:
                score += 1

        return score

    def exploration_path(self, start):
        q = deque([(start, [])])
        seen = {start}

        best_path = []
        best_score = -999999

        while q:
            c, path = q.popleft()

            if path:
                score = 0

                if c not in self.visited:
                    score += 180

                score += self.count_frontier(c) * 80
                score -= self.visit_count[c] * 80
                score += c[0] * 3
                score += c[1] * 3
                score -= len(path) * 6

                if score > best_score:
                    best_score = score
                    best_path = path

            for n in self.neighbors(c, known_only=False):
                if n not in seen:
                    seen.add(n)
                    q.append((n, path + [n]))

        return best_path

    def target_angle(self, current, target):
        dx = target[0] - current[0]
        dy = target[1] - current[1]

        if dx == 1:
            return 0
        if dx == -1:
            return 180
        if dy == -1:
            return 90
        if dy == 1:
            return 270

        return 0

    def angle_diff(self, target, current):
        return (target - current + 180) % 360 - 180

    def drive_to_cell(self, s, target):
        current = self.cell(s["x"], s["y"])
        speed = s["speed"]
        front = s["front"]

        max_speed = MAX_SPEED_RACE if self.race_mode else MAX_SPEED_EXPLORE

        wanted = self.target_angle(current, target)
        diff = self.angle_diff(wanted, s["orientation"])

        danger = 0.45 + speed * 1.10

        if front < danger:
            if speed > STOP_SPEED:
                return "DECELERATE"

            if s["right"] >= s["left"]:
                self.last_turn = "RIGHT"
                return "TURN_RIGHT"

            self.last_turn = "LEFT"
            return "TURN_LEFT"

        if abs(diff) > ANGLE_OK:
            if speed > STOP_SPEED:
                return "DECELERATE"

            if diff > 0:
                self.last_turn = "LEFT"
                return "TURN_LEFT"

            self.last_turn = "RIGHT"
            return "TURN_RIGHT"

        if speed < max_speed:
            return "ACCELERATE"

        return "ACCELERATE"

    def choose_command(self, s):
        c = self.cell(s["x"], s["y"])

        self.visited.add(c)
        self.visit_count[c] += 1

        if c == self.last_cell:
            self.stuck += 1
        else:
            self.stuck = 0
            self.last_cell = c

        if self.stuck > 25:
            self.stuck = 0

            if s["speed"] > STOP_SPEED:
                return "DECELERATE"

            if s["front"] > 0.85:
                return "ACCELERATE"

            return "TURN_RIGHT" if s["right"] >= s["left"] else "TURN_LEFT"

        if not self.race_mode:
            path = self.exploration_path(c)
        else:
            path = self.bfs(c, GOAL, known_only=True)

            if not path:
                path = self.bfs(c, GOAL, known_only=False)

        if path:
            return self.drive_to_cell(s, path[0])

        if s["front"] > 1.00:
            return "ACCELERATE"

        if s["speed"] > STOP_SPEED:
            return "DECELERATE"

        return "TURN_RIGHT" if s["right"] >= s["left"] else "TURN_LEFT"

    def register_player(self, f):
        f.write("0\n")
        f.write(NAME + "\n")
        f.flush()

        response = f.readline().strip()
        print("SERVER:", response)

        if response != "OK":
            print("Inscription refusée:", response)
            return False

        start = f.readline().strip()
        print("START:", start)

        if start != "START":
            print("Début de partie non reçu:", start)
            return False

        return True

    def read_sensor_line(self, f):
        if self.pending_sensor is not None:
            line = self.pending_sensor
            self.pending_sensor = None
            return line

        f.write("GET_SENSORS\n")
        f.flush()
        return f.readline().strip()

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        while True:
            try:
                sock.connect((HOST, PORT))
                break
            except OSError:
                print(f"Could not connect to {HOST}:{PORT}, retrying...")
                time.sleep(1)

        f = sock.makefile("rw")

        if not self.register_player(f):
            sock.close()
            return

        print(f"CONNECTED to {HOST}:{PORT} as {NAME}")

        while True:
            line = self.read_sensor_line(f)

            if not line:
                break

            if line == "BLOCKED":
                print("BLOCKED")
                time.sleep(0.5)
                continue

            s = self.parse_sensors(line)

            if not s:
                print("Bad sensors:", line)
                continue

            if self.last_explore == 1 and s["explore"] == 0:
                print("===== MODE COURSE =====")
                self.race_mode = True

            self.last_explore = s["explore"]

            self.update_map(s)
            cmd = self.choose_command(s)

            f.write(cmd + "\n")
            f.flush()

            rep = f.readline().strip()

            if self.parse_sensors(rep):
                self.pending_sensor = rep
                rep = "SENSOR_RECEIVED"

            print(
                f"t={s['time']:.2f} "
                f"mode={'RACE' if self.race_mode else 'EXPLORE'} "
                f"pos=({s['x']:.2f},{s['y']:.2f}) "
                f"ori={s['orientation']:.0f} "
                f"spd={s['speed']:.2f} "
                f"F={s['front']:.2f} "
                f"R={s['right']:.2f} "
                f"L={s['left']:.2f} "
                f"cmd={cmd} "
                f"rep={rep}"
            )

            time.sleep(0.03)

        sock.close()


if __name__ == "__main__":
    SmartBot().run()
