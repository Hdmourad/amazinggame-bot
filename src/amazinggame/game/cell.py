"""Cell data structure for maze walls."""

from dataclasses import dataclass


@dataclass(frozen=False)
class Cell:
    """Represents a cell in the maze with wall information.

    Each cell has walls on its top and left sides.
    """

    top: bool = True
    left: bool = True
