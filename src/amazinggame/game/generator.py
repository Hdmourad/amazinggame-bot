"""Maze generation algorithms."""

from __future__ import annotations

import random
from typing import NamedTuple, cast

from amazinggame.game.maze import Maze, Path


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
        """Find root of node i with path compression.

        Returns:
            Root representative index for node `i`.
        """
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        """Union two sets.

        Returns:
            True when the sets were merged, otherwise False.
        """
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


def carve(
    maze: Maze,
    possible_walls: list[WallToRemove],
) -> None:
    """Carve walls until the target condition is reached."""
    dsu = DisjointSet(maze.width * maze.height)
    for wall in possible_walls:
        neighbors = _wall_neighbors(wall, maze.width, maze.height)
        if neighbors[0] is None or neighbors[1] is None:
            continue

        idx_a = _cell_index(neighbors[0][0], neighbors[0][1], maze.width)
        idx_b = _cell_index(neighbors[1][0], neighbors[1][1], maze.width)
        if dsu.find(idx_a) == dsu.find(idx_b):
            continue

        if wall.is_top:
            maze.walls[wall.x][wall.y].top = False
        else:
            maze.walls[wall.x][wall.y].left = False

        dsu.union(idx_a, idx_b)


def generate_maze(
    width: int,
    height: int,
) -> Maze:
    """Generate a maze by random wall removals with fast connectivity heuristics.

    Returns:
        A maze where start and end are connected and at least 10 paths are targeted.
    """
    maze = Maze(width, height)

    possible_walls: list[WallToRemove] = []
    for x in range(width):
        for y in range(height):
            if y < height - 1:  # horizontal wall below this cell
                possible_walls.append(WallToRemove(x=x, y=y + 1, is_top=True))
            if x < width - 1:  # vertical wall to the right
                possible_walls.append(WallToRemove(x=x + 1, y=y, is_top=False))

    random.shuffle(possible_walls)
    carve(maze, possible_walls)

    min_paths = 10
    for wall in possible_walls:
        if len(maze.paths(0, 0, maze.width - 1, maze.height - 1)) >= min_paths:
            break

        if wall.is_top:
            maze.walls[wall.x][wall.y].top = False
        else:
            maze.walls[wall.x][wall.y].left = False

    for wall in possible_walls[int(len(possible_walls) * 0.85) :]:
        if wall.is_top:
            maze.walls[wall.x][wall.y].top = False
        else:
            maze.walls[wall.x][wall.y].left = False

    return maze


def main() -> None:
    """Run the maze generator application."""
    maze = generate_maze(30, 30)
    paths: list[Path] = maze.paths(0, 0, 29, 29)
    print(maze)  # noqa: T201
    print(f"Number of paths from (0, 0) to (29, 29): {len(paths)}")  # noqa: T201
    if paths:
        shortest_path = cast("Path", min(paths, key=len))
        print("Example path:", shortest_path)  # noqa: T201
        print(maze.highlighted_path(shortest_path))  # noqa: T201


if __name__ == "__main__":
    main()
