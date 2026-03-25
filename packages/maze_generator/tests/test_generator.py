"""Tests for maze generation."""

from maze_generator import generate_maze


def test_generate_maze_basic() -> None:
    """Test that generate_maze creates a maze with at least 10 paths."""
    maze = generate_maze(20, 20)
    assert maze.width == 20
    assert maze.height == 20
    paths = maze.paths(0, 0, 19, 19)
    assert len(paths) >= 10
    print(maze)
    assert False


def test_generate_maze_small() -> None:
    """Test generate_maze on a small maze."""
    maze = generate_maze(2, 2)
    assert maze.width == 2
    assert maze.height == 2
    paths = maze.paths(0, 0, 1, 1)
    # For 2x2, max paths might be less than 10, but should be at least 1
    assert len(paths) >= 1
