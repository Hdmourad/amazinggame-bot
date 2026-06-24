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
 
MAX_SPEED_EXPLORE = 1.80
MAX_SPEED_RACE = 2.05
 
VERY_CLOSE = 0.35
DANGER_FRONT = 0.80
SAFE_FRONT = 1.25
STOP_SPEED = 0.08
 
TURN_LOCK_STEPS = 10
UTURN_STEPS = 18
ESCAPE_ACCEL_STEPS = 10
 
 
class SmartBot:
    def __init__(self):
        self.race_mode = False
        self.last_explore = 1
 
        self.visited = set()
        self.visit_count = defaultdict(int)
        self.walls = set()
        self.open_paths = set()
 
        self.last_cell = None
        self.stuck_count = 0
 
        self.lock_turn = None
        self.lock_steps = 0
 
        self.uturn_steps = 0
        self.escape_steps = 0
 
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
        cx = int(math.floor(x))
        cy = int(math.floor(y))
        cx = max(0, min(GRID - 1, cx))
        cy = max(0, min(GRID - 1, cy))
        return cx, cy
 
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
 
            if s[side] < 0.55:
                self.walls.add(e)
                self.open_paths.discard(e)
            else:
                if e not in self.walls:
                    self.open_paths.add(e)
 
    def neighbors(self, c, known_only=False):
        x, y = c
        result = []
 
        for n in [(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)]:
            if not self.in_grid(n):
                continue
 
            e = self.edge(c, n)
 
            if e in self.walls:
                continue
 
            if known_only and e not in self.open_paths:
                continue
 
            result.append(n)
 
        return result
 
    def bfs(self, start, goal, known_only=True):
        q = deque([(start, [])])
        seen = {start}
 
        while q:
            c, path = q.popleft()
 
            if c == goal:
                return path
 
            for n in self.neighbors(c, known_only=known_only):
                if n not in seen:
                    seen.add(n)
                    q.append((n, path + [n]))
 
        return []
 
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
 
    def choose_best_turn(self, s):
        if s["right"] >= s["left"]:
            return "RIGHT"
        return "LEFT"
 
    def start_turn_lock(self, side, steps=TURN_LOCK_STEPS):
        self.lock_turn = side
        self.lock_steps = steps
 
    def start_uturn(self):
        self.uturn_steps = UTURN_STEPS
        self.escape_steps = ESCAPE_ACCEL_STEPS
        self.lock_turn = "RIGHT"
        self.lock_steps = 0
 
    def manage_uturn(self, s):
        if self.uturn_steps > 0:
            if s["speed"] > STOP_SPEED:
                return "DECELERATE"
 
            self.uturn_steps -= 1
            return "TURN_RIGHT"
 
        if self.escape_steps > 0:
            self.escape_steps -= 1
 
            if s["front"] < DANGER_FRONT:
                return "TURN_RIGHT"
 
            return "ACCELERATE"
 
        return None
 
    def manage_locked_turn(self, s):
        if self.lock_steps <= 0:
            return None
 
        if s["speed"] > 0.35:
            return "DECELERATE"
 
        self.lock_steps -= 1
 
        if self.lock_turn == "RIGHT":
            return "TURN_RIGHT"
 
        return "TURN_LEFT"
 
    def update_stuck(self, s):
        c = self.cell(s["x"], s["y"])
 
        self.visited.add(c)
        self.visit_count[c] += 1
 
        if c == self.last_cell and s["speed"] < 0.20:
            self.stuck_count += 1
        else:
            self.stuck_count = 0
            self.last_cell = c
 
    def exploration_command(self, s):
        uturn_cmd = self.manage_uturn(s)
        if uturn_cmd:
            return uturn_cmd
 
        locked_cmd = self.manage_locked_turn(s)
        if locked_cmd:
            return locked_cmd
 
        if self.stuck_count > 18:
            self.stuck_count = 0
            self.start_uturn()
            return "DECELERATE"
 
        dynamic_danger = DANGER_FRONT + s["speed"] * 0.95
 
        if s["front"] < VERY_CLOSE:
            if s["speed"] > STOP_SPEED:
                return "DECELERATE"
 
            self.start_uturn()
            return "TURN_RIGHT"
 
        if s["front"] < dynamic_danger:
            if s["speed"] > 0.35:
                return "DECELERATE"
 
            side = self.choose_best_turn(s)
            self.start_turn_lock(side, steps=14)
 
            if side == "RIGHT":
                return "TURN_RIGHT"
            return "TURN_LEFT"
 
        # Stratégie principale exploration : main droite rapide
        if s["right"] > 1.15 and s["speed"] < 0.65:
            self.start_turn_lock("RIGHT", steps=9)
            return "TURN_RIGHT"
 
        if s["front"] > SAFE_FRONT:
            if s["speed"] < MAX_SPEED_EXPLORE:
                return "ACCELERATE"
            return "DECELERATE"
 
        if s["speed"] > 0.35:
            return "DECELERATE"
 
        side = self.choose_best_turn(s)
        self.start_turn_lock(side, steps=10)
 
        if side == "RIGHT":
            return "TURN_RIGHT"
        return "TURN_LEFT"
 
    def race_command(self, s):
        uturn_cmd = self.manage_uturn(s)
        if uturn_cmd:
            return uturn_cmd
 
        locked_cmd = self.manage_locked_turn(s)
        if locked_cmd:
            return locked_cmd
 
        if self.stuck_count > 12:
            self.stuck_count = 0
            self.start_uturn()
            return "DECELERATE"
 
        current = self.cell(s["x"], s["y"])
 
        path = self.bfs(current, GOAL, known_only=True)
        if not path:
            path = self.bfs(current, GOAL, known_only=False)
 
        if not path:
            return self.exploration_command(s)
 
        target = path[0]
        wanted = self.target_angle(current, target)
        diff = self.angle_diff(wanted, s["orientation"])
 
        dynamic_danger = DANGER_FRONT + s["speed"] * 1.05
 
        if s["front"] < VERY_CLOSE:
            if s["speed"] > STOP_SPEED:
                return "DECELERATE"
 
            self.start_uturn()
            return "TURN_RIGHT"
 
        if s["front"] < dynamic_danger:
            if s["speed"] > 0.35:
                return "DECELERATE"
 
            side = self.choose_best_turn(s)
            self.start_turn_lock(side, steps=10)
 
            if side == "RIGHT":
                return "TURN_RIGHT"
            return "TURN_LEFT"
 
        if abs(diff) > 12:
            if s["speed"] > 0.70:
                return "DECELERATE"
 
            if diff > 0:
                self.start_turn_lock("LEFT", steps=5)
                return "TURN_LEFT"
 
            self.start_turn_lock("RIGHT", steps=5)
            return "TURN_RIGHT"
 
        if s["speed"] < MAX_SPEED_RACE:
            return "ACCELERATE"
 
        return "DECELERATE"
 
    def choose_command(self, s):
        self.update_stuck(s)
 
        if not self.race_mode:
            return self.exploration_command(s)
 
        return self.race_command(s)
 
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
 
        f.write("0\n")
        f.flush()
        f.write(NAME + "\n")
        f.flush()
 
        rep = f.readline().strip()
        if rep != "OK":
            print("Server rejected:", rep)
            sock.close()
            return
 
        start = f.readline().strip()
        if start != "START":
            print("Expected START, got:", start)
            sock.close()
            return
 
        print(f"CONNECTED to {HOST}:{PORT} as {NAME}")
 
        while True:
            f.write("GET_SENSORS\n")
            f.flush()
 
            line = f.readline().strip()
 
            if not line:
                break
 
            if line == "BLOCKED":
                self.start_uturn()
                time.sleep(0.5)
                continue
 
            s = self.parse_sensors(line)
            if not s:
                print("Bad sensors:", line)
                continue
 
            if self.last_explore == 1 and s["explore"] == 0:
                self.race_mode = True
                self.lock_steps = 0
                self.uturn_steps = 0
                self.escape_steps = 0
                self.stuck_count = 0
                print("===== MODE COURSE =====")
 
            self.last_explore = s["explore"]
 
            self.update_map(s)
 
            cmd = self.choose_command(s)
 
            f.write(cmd + "\n")
            f.flush()
 
            rep = f.readline().strip()
 
            print(
                f"t={s['time']:.2f} "
                f"mode={'RACE' if self.race_mode else 'EXPLORE'} "
                f"pos=({s['x']:.2f},{s['y']:.2f}) "
                f"ori={s['orientation']:.0f} "
                f"spd={s['speed']:.2f} "
                f"F={s['front']:.2f} "
                f"R={s['right']:.2f} "
                f"Rear={s['rear']:.2f} "
                f"L={s['left']:.2f} "
                f"visited={len(self.visited)} "
                f"stuck={self.stuck_count} "
                f"lock={self.lock_turn}:{self.lock_steps} "
                f"cmd={cmd} "
                f"rep={rep}"
            )
 
            time.sleep(0.01)
 
        sock.close()
 
 
if __name__ == "__main__":
    SmartBot().run()