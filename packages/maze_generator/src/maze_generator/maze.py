"""Maze data structure for maze generator."""

from collections import UserList
from typing import NamedTuple

from .cell import Cell


class CellCoord(NamedTuple):
    """Coordinate in the maze, with x/y grid positions."""

    x: int
    y: int


class Path(UserList):
    """Represents a path as a list of cell coordinates."""

    def __str__(self) -> str:
        """Return a user-readable representation of the path."""
        return "[" + ", ".join(f"({c.x},{c.y})" for c in self.data) + "]"


class Maze:
    """Represents a maze with walls between cells.

    The maze includes a hidden row and column of walls to ensure
    the perimeter is always walled.
    """

    def __init__(self, width: int, height: int) -> None:
        """Initialize a maze with given dimensions.

        Args:
            width: Number of cells horizontally
            height: Number of cells vertically
        """
        self.width = width
        self.height = height

        # Initialize walls grid with extra row/column for perimeter
        # walls[row][col] contains wall info for the cell at (row, col)
        self.walls = []
        for row in range(height + 1):  # +1 for hidden row
            self.walls.append([])
            for _ in range(width + 1):  # +1 for hidden column
                # Each cell has top and left walls
                self.walls[row].append(Cell(top=True, left=True))

    def __str__(self) -> str:
        """Return an ASCII-art rendering of the maze."""
        lines: list[str] = []

        def top_line_for(row: int) -> str:
            line = "+"
            for x in range(self.width):
                line += "-" if self.walls[row][x].top else " "
                line += "+"
            return line

        def middle_line_for(row: int) -> str:
            line = ""
            for x in range(self.width):
                line += "|" if self.walls[row][x].left else " "
                line += " "
            line += "|" if self.walls[row][self.width].left else " "
            return line

        for y in range(self.height):
            lines.extend((top_line_for(y), middle_line_for(y)))

        lines.append(top_line_for(self.height))
        return "\n".join(lines)

    def paths(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
    ) -> list[Path]:
        """Return all simple paths from start to end in the maze.

        Only paths that do not revisit a cell are counted.

        Args:
            start_x: start column (0-based)
            start_y: start row (0-based)
            end_x: end column (0-based)
            end_y: end row (0-based)

        Returns:
            Number of distinct simple paths from start to end.

        Raises:
            ValueError: if any coordinate is outside the maze bounds.
        """
        if not (0 <= start_x < self.width and 0 <= start_y < self.height):
            msg = "start coordinates out of maze bounds"
            raise ValueError(msg)

        if not (0 <= end_x < self.width and 0 <= end_y < self.height):
            msg = "end coordinates out of maze bounds"
            raise ValueError(msg)

        if (start_x, start_y) == (end_x, end_y):
            path = Path([CellCoord(start_x, start_y)])
            print(path)  # noqa: T201
            return [path]

        return self._find_paths(start_x, start_y, end_x, end_y)

    def _can_move(self, x: int, y: int, nx: int, ny: int) -> bool:
        if nx < 0 or nx >= self.width or ny < 0 or ny >= self.height:
            return False

        if nx == x - 1 and ny == y:
            return not self.walls[y][x].left
        if nx == x + 1 and ny == y:
            return not self.walls[y][x + 1].left
        if nx == x and ny == y - 1:
            return not self.walls[y][x].top
        if nx == x and ny == y + 1:
            return not self.walls[y + 1][x].top

        return False

    def _find_paths(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
    ) -> list[Path]:
        visited: set[tuple[int, int]] = set()
        result: list[Path] = []
        current: Path = Path()

        def dfs(x: int, y: int) -> None:
            current.append(CellCoord(x, y))
            visited.add((x, y))

            if (x, y) == (end_x, end_y):
                found = Path(current)
                result.append(found)
            else:
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if (nx, ny) not in visited and self._can_move(x, y, nx, ny):
                        dfs(nx, ny)

            visited.remove((x, y))
            current.pop()

        dfs(start_x, start_y)
        return result
