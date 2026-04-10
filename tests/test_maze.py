"""Tests for maze_generator.maze module."""

import pytest

from amazinggame.game.cell import Cell
from amazinggame.game.maze import CellCoord, Maze, Path


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
    assert len(maze.walls) == 3  # width + 1
    assert len(maze.walls[0]) == 3  # height + 1


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
    # Top row should all have top walls
    for col in range(maze.width + 1):
        assert maze.walls[col][0].top is True

    # Left column should all have left walls
    for row in range(maze.height + 1):
        assert maze.walls[0][row].left is True

    # Right column should have left walls (but this is the right edge)
    for row in range(maze.height + 1):
        assert maze.walls[maze.width][row].left is True

    # Bottom row should have top walls
    for col in range(maze.width + 1):
        assert maze.walls[col][maze.height].top is True


def test_paths_is_empty_when_walls_block_path() -> None:
    """Count is zero when there is no open passage."""
    maze = Maze(width=2, height=2)
    assert maze.paths(0, 0, 1, 1) == []


def test_paths_count_simple_open_maze() -> None:
    """Count paths on a fully opened 2x2 maze."""
    maze = Maze(width=2, height=2)
    for y in range(maze.height + 1):
        for x in range(maze.width + 1):
            maze.walls[x][y].top = False
            maze.walls[x][y].left = False

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
    for y in range(maze.height + 1):
        for x in range(maze.width + 1):
            maze.walls[x][y].top = False
            maze.walls[x][y].left = False

    all_paths = maze.paths(0, 0, 1, 1)
    assert len(all_paths) == 8


def test_maze_str_representation() -> None:
    """Verify maze ASCII rendering with all boundary walls present."""
    maze = Maze(width=1, height=1)
    maze.walls[0][0].top = True
    maze.walls[0][0].left = True
    maze.walls[0][1].left = True
    maze.walls[1][0].top = True

    expected = "+--+\n|  |\n+--+"
    assert str(maze) == expected


def test_paths_count_simple_maze_with_walls() -> None:
    """Count paths on a 3x3 maze with some walls."""
    maze = Maze(width=3, height=3)
    for y in range(maze.height):
        maze.walls[1][y].left = False
        maze.walls[2][y].left = False
    for x in range(maze.width):
        maze.walls[x][1].top = False
        maze.walls[x][2].top = False
    maze.walls[1][1].top = True
    maze.walls[1][2].top = True
    maze.walls[1][1].left = True
    maze.walls[2][1].left = True
    all_paths = maze.paths(0, 0, 2, 2)
    assert len(all_paths) == 2


def test_maze_is_connected() -> None:
    """Test connectivity check between start and end."""
    maze = Maze(width=2, height=2)
    # Initially, no paths
    assert not maze.is_connected(0, 0, 1, 1)

    # Open some walls
    for y in range(maze.height + 1):
        for x in range(maze.width + 1):
            maze.walls[x][y].top = False
            maze.walls[x][y].left = False

    # Now connected
    assert maze.is_connected(0, 0, 1, 1)


def test_paths_raises_for_out_of_bounds_coordinates() -> None:
    """Paths should raise ValueError for invalid start/end coordinates."""
    maze = Maze(width=2, height=2)
    with pytest.raises(ValueError, match="start coordinates out of maze bounds"):
        maze.paths(-1, 0, 1, 1)
    with pytest.raises(ValueError, match="end coordinates out of maze bounds"):
        maze.paths(0, 0, 2, 1)


def test_is_connected_raises_for_out_of_bounds_coordinates() -> None:
    """Connectivity should raise ValueError for invalid start/end coordinates."""
    maze = Maze(width=2, height=2)
    with pytest.raises(ValueError, match="start coordinates out of maze bounds"):
        maze.is_connected(-1, 0, 1, 1)
    with pytest.raises(ValueError, match="end coordinates out of maze bounds"):
        maze.is_connected(0, 0, 2, 1)


def test_is_connected_start_equals_end_is_true() -> None:
    """Connectivity is always true when start and end are the same cell."""
    maze = Maze(width=2, height=2)
    assert maze.is_connected(1, 1, 1, 1)


def test_maze_serialize_contains_dimensions_and_walls() -> None:
    """Serialized maze should include dimensions and all wall entries."""
    maze = Maze(width=2, height=1)
    maze.walls[1][1].top = False
    maze.walls[2][0].left = False

    data = maze.serialize()

    assert data["width"] == 2
    assert data["height"] == 1
    assert len(data["walls"]) == 3
    assert len(data["walls"][0]) == 2
    assert data["walls"][1][1]["top"] is False
    assert data["walls"][2][0]["left"] is False


def test_maze_deserialize_rebuilds_walls() -> None:
    """Deserialization should recreate a maze with the same wall states."""
    source = Maze(width=2, height=2)
    source.walls[1][0].left = False
    source.walls[0][2].top = False

    restored = Maze.deserialize(source.serialize())

    assert restored.width == source.width
    assert restored.height == source.height
    for x in range(source.width + 1):
        for y in range(source.height + 1):
            assert restored.walls[x][y].top is source.walls[x][y].top
            assert restored.walls[x][y].left is source.walls[x][y].left
