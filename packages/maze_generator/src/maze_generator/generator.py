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


def generate_maze(width: int, height: int) -> Maze:
    """Generate a maze by randomly removing walls until >= MIN_PATHS paths.

    Returns:
        A Maze instance with sufficient connectivity.
    """
    maze = Maze(width, height)

    # List of possible walls to remove
    possible_walls = []
    for x in range(width):
        for y in range(height):
            if y < height - 1:  # horizontal wall below this cell
                possible_walls.append(WallToRemove(x=x, y=y + 1, is_top=True))
            if x < width - 1:  # vertical wall to the right
                possible_walls.append(WallToRemove(x=x + 1, y=y, is_top=False))

    random.shuffle(possible_walls)

    for wall in possible_walls:
        if wall.is_top:
            maze.walls[wall.x][wall.y].top = False
        else:
            maze.walls[wall.x][wall.y].left = False

        paths = maze.paths(0, 0, width - 1, height - 1)
        if len(paths) >= MIN_PATHS:
            return maze

    # If exhausted all walls and still < MIN_PATHS, return anyway
    return maze
