"""Tests for maze_generator.maze module."""

from maze_generator.cell import Cell
from maze_generator.maze import CellCoord, Maze, Path


def test_maze_initialization_sets_width_and_height() -> None:
    """Maze should store width and height as public attributes."""
    maze = Maze(width=5, height=3)
    assert maze.width == 5
    assert maze.height == 3


def test_maze_has_walls_attribute() -> None:
    """Maze should have a public walls attribute."""
    maze = Maze(width=2, height=2)
    assert hasattr(maze, "walls")


def test_maze_walls_include_hidden_row_and_column() -> None:
    """Maze walls should include extra row and column for perimeter walls."""
    maze = Maze(width=2, height=2)
    # For a 2x2 maze, we need 3x3 walls (2 cells + 1 hidden per dimension)
    # This will fail initially - that's the red phase of TDD
    assert len(maze.walls) == 3  # height + 1
    assert len(maze.walls[0]) == 3  # width + 1


def test_maze_walls_are_two_types_top_and_left() -> None:
    """Each cell should have top and left wall information."""
    maze = Maze(width=1, height=1)
    # Each position should have both top and left wall data
    # This is a placeholder test - implementation will define the structure
    cell = maze.walls[0][0]
    assert isinstance(cell, Cell)
    assert hasattr(cell, "top")
    assert hasattr(cell, "left")


def test_maze_perimeter_walls_are_present() -> None:
    """All perimeter walls should be present (outer boundary)."""
    maze = Maze(width=2, height=2)
    # Check that all outer walls are present
    # Top row should all have top walls
    for col in range(maze.width + 1):
        assert maze.walls[0][col].top is True

    # Left column should all have left walls
    for row in range(maze.height + 1):
        assert maze.walls[row][0].left is True

    # Right column should have left walls (but this is the right edge)
    # Bottom row should have top walls
    for col in range(maze.width + 1):
        assert maze.walls[maze.height][col].top is True


def test_paths_is_empty_when_walls_block_path() -> None:
    """Count is zero when there is no open passage."""
    maze = Maze(width=2, height=2)
    assert maze.paths(0, 0, 1, 1) == []


def test_paths_count_simple_open_maze() -> None:
    """Count paths on a fully opened 2x2 maze."""
    maze = Maze(width=2, height=2)
    for row in range(maze.height + 1):
        for col in range(maze.width + 1):
            maze.walls[row][col].top = False
            maze.walls[row][col].left = False

    all_paths = maze.paths(0, 0, 1, 1)
    assert len(all_paths) == 2


def test_paths_start_equals_end() -> None:
    """Start equals end should produce exactly one path."""
    maze = Maze(width=2, height=2)
    all_paths = maze.paths(0, 0, 0, 0)
    assert len(all_paths) == 1
    assert all_paths[0] == Path([CellCoord(0, 0)])


def test_paths_count_simple_maze() -> None:
    """Count paths on a fully opened 3x3 maze."""
    maze = Maze(width=3, height=3)
    for row in range(maze.height + 1):
        for col in range(maze.width + 1):
            maze.walls[row][col].top = False
            maze.walls[row][col].left = False

    all_paths = maze.paths(0, 0, 1, 1)
    assert len(all_paths) == 8
