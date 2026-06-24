"""Maze data structure for maze generator."""

from __future__ import annotations

from collections import UserList, deque
from typing import NamedTuple, TypedDict

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


class CellState(TypedDict):
    """Serializable wall state for one wall-entry cell."""

    top: bool
    left: bool


class MazeState(TypedDict):
    """Serializable maze payload."""

    width: int
    height: int
    walls: list[list[CellState]]


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
        # walls[x][y] contains wall info for the cell at (x, y)
        self.walls = []
        for x in range(width + 1):  # +1 for hidden column
            self.walls.append([])
            for _ in range(height + 1):  # +1 for hidden row
                # Each cell has top and left walls
                self.walls[x].append(Cell(top=True, left=True))

    def _top_line_for(self, row: int) -> str:
        line = "+"
        for x in range(self.width):
            line += "--" if self.walls[x][row].top else "  "
            line += "+"
        return line

    def _middle_line_for(self, row: int, path: Path) -> str:
        line = ""
        for x in range(self.width):
            line += "|" if self.walls[x][row].left else " "
            line += "##" if (x, row) in path else "  "
        line += "|" if self.walls[self.width][row].left else " "
        return line

    def __str__(self) -> str:
        """Return an ASCII-art rendering of the maze."""
        return self.highlighted_path(Path())

    def serialize(self) -> MazeState:
        """Serialize maze dimensions and wall states.

        Returns:
            A payload containing dimensions and all top/left wall values.
        """
        walls: list[list[CellState]] = [
            [
                {
                    "top": self.walls[x][y].top,
                    "left": self.walls[x][y].left,
                }
                for y in range(self.height + 1)
            ]
            for x in range(self.width + 1)
        ]

        return {
            "width": self.width,
            "height": self.height,
            "walls": walls,
        }

    @classmethod
    def deserialize(cls, data: MazeState) -> Maze:
        """Build a maze instance from serialized wall states.

        Returns:
            A reconstructed maze with the same dimensions and wall values.
        """
        maze = cls(data["width"], data["height"])
        for x in range(maze.width + 1):
            for y in range(maze.height + 1):
                cell = data["walls"][x][y]
                maze.walls[x][y].top = cell["top"]
                maze.walls[x][y].left = cell["left"]
        return maze

    def highlighted_path(self, path: Path) -> str:
        """Return an ASCII-art rendering of the maze with a path highlighted."""
        lines: list[str] = []

        for y in range(self.height):
            lines.extend((self._top_line_for(y), self._middle_line_for(y, path)))

        lines.append(self._top_line_for(self.height))
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
            return not self.walls[x][y].left
        if nx == x + 1 and ny == y:
            return not self.walls[x + 1][y].left
        if nx == x and ny == y - 1:
            return not self.walls[x][y].top
        if nx == x and ny == y + 1:
            return not self.walls[x][y + 1].top

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

    def is_connected(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
    ) -> bool:
        """Check if there is a path from start to end in the maze.

        Args:
            start_x: start column (0-based)
            start_y: start row (0-based)
            end_x: end column (0-based)
            end_y: end row (0-based)

        Returns:
            True if end is reachable from start, False otherwise.

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
            return True

        visited = set()
        queue = deque([(start_x, start_y)])
        visited.add((start_x, start_y))

        while queue:
            x, y = queue.popleft()
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if (nx, ny) == (end_x, end_y):
                    return True
                if (nx, ny) not in visited and self._can_move(x, y, nx, ny):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return False
