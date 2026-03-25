"""Maze generation algorithms."""

import random
from typing import NamedTuple

from .maze import Maze

MIN_PATHS = 10


class WallToRemove(NamedTuple):
    """Represents a wall to potentially remove during maze generation."""

    x: int
    y: int
    is_top: bool


class DisjointSet:
    """Union-find helper for connectivity tracking."""

    def __init__(self, size: int) -> None:
        """Initialize disjoint set for `size` elements."""
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, i: int) -> int:
        """Find root of node i with path compression."""
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        """Union two sets and return True if merged."""
        ri = self.find(i)
        rj = self.find(j)
        if ri == rj:
            return False
        if self.rank[ri] < self.rank[rj]:
            ri, rj = rj, ri
        self.parent[rj] = ri
        if self.rank[ri] == self.rank[rj]:
            self.rank[ri] += 1
        return True


def _wall_neighbors(
    wall: WallToRemove,
    width: int,
    height: int,
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    if wall.is_top:
        a = (wall.x, wall.y - 1)
        b = (wall.x, wall.y)
    else:
        a = (wall.x - 1, wall.y)
        b = (wall.x, wall.y)

    def _valid(pos: tuple[int, int]) -> bool:
        px, py = pos
        return 0 <= px < width and 0 <= py < height

    return (a if _valid(a) else None), (b if _valid(b) else None)


def _cell_index(x: int, y: int, width: int) -> int:
    return y * width + x


class MazeCarver:
    """Encapsulate wall carving with union-find and open-edge threshold."""

    def __init__(
        self,
        maze: Maze,
        possible_walls: list[WallToRemove],
        dsu: DisjointSet,
        start_node: int,
        end_node: int,
        min_open_edges: int,
    ) -> None:
        """Initialize carver state."""
        self.maze = maze
        self.possible_walls = possible_walls
        self.dsu = dsu
        self.start_node = start_node
        self.end_node = end_node
        self.min_open_edges = min_open_edges

    def carve(self) -> None:
        """Carve walls until the target condition is reached."""
        open_edges = 0
        for wall in self.possible_walls:
            neighbors = _wall_neighbors(wall, self.maze.width, self.maze.height)
            if neighbors[0] is None or neighbors[1] is None:
                continue

            idx_a = _cell_index(neighbors[0][0], neighbors[0][1], self.maze.width)
            idx_b = _cell_index(neighbors[1][0], neighbors[1][1], self.maze.width)
            if self.dsu.find(idx_a) == self.dsu.find(idx_b):
                continue

            if wall.is_top:
                self.maze.walls[wall.x][wall.y].top = False
            else:
                self.maze.walls[wall.x][wall.y].left = False

            self.dsu.union(idx_a, idx_b)
            open_edges += 1

            if (
                self.dsu.find(self.start_node) == self.dsu.find(self.end_node)
                and open_edges >= self.min_open_edges
            ):
                return


def _verify_path_requirement(
    maze: Maze,
    min_paths: int,
) -> bool:
    paths = maze.paths(0, 0, maze.width - 1, maze.height - 1)
    return len(paths) >= min_paths


def _open_more_walls(
    maze: Maze,
    possible_walls: list[WallToRemove],
    min_paths: int,
) -> None:
    for wall in possible_walls:
        if wall.is_top and maze.walls[wall.x][wall.y].top:
            maze.walls[wall.x][wall.y].top = False
        elif not wall.is_top and maze.walls[wall.x][wall.y].left:
            maze.walls[wall.x][wall.y].left = False

        if _verify_path_requirement(maze, min_paths):
            return


def generate_maze(
    width: int,
    height: int,
    min_paths: int = MIN_PATHS,
    min_open_edges: int | None = None,
) -> Maze:
    """Generate a maze by random wall removals with fast connectivity heuristics."""
    maze = Maze(width, height)

    if min_open_edges is None:
        min_open_edges = max(1, (width * height) // 3)

    possible_walls: list[WallToRemove] = []
    for x in range(width):
        for y in range(height):
            if y < height - 1:  # horizontal wall below this cell
                possible_walls.append(WallToRemove(x=x, y=y + 1, is_top=True))
            if x < width - 1:  # vertical wall to the right
                possible_walls.append(WallToRemove(x=x + 1, y=y, is_top=False))

    random.shuffle(possible_walls)

    dsu = DisjointSet(width * height)
    start_node = _cell_index(0, 0, width)
    end_node = _cell_index(width - 1, height - 1, width)

    MazeCarver(
        maze=maze,
        possible_walls=possible_walls,
        dsu=dsu,
        start_node=start_node,
        end_node=end_node,
        min_open_edges=min_open_edges,
    ).carve()

    if _verify_path_requirement(maze, min_paths):
        return maze

    _open_more_walls(maze, possible_walls, min_paths)

    return maze
