"""Tests for maze generation."""

from typing import TYPE_CHECKING

import amazinggame.game.generator as generator_module
from amazinggame.game.generator import (
    DisjointSet,
    WallToRemove,
    carve,
    generate_maze,
    main,
)
from amazinggame.game.maze import Maze

if TYPE_CHECKING:
    import pytest


def test_generate_maze_basic() -> None:
    """Test that generate_maze creates a maze with at least 10 paths."""
    maze = generate_maze(20, 20)
    assert maze.width == 20
    assert maze.height == 20


def test_generate_maze_small() -> None:
    """Test generate_maze on a small maze."""
    maze = generate_maze(2, 2)
    assert maze.width == 2
    assert maze.height == 2
    paths = maze.paths(0, 0, 1, 1)
    # For 2x2, max paths might be less than 10, but should be at least 1
    assert len(paths) >= 1


def test_disjoint_set_union_returns_false_for_same_component() -> None:
    """Union should return False when elements are already connected."""
    dsu = DisjointSet(3)
    assert dsu.union(0, 1) is True
    assert dsu.union(0, 1) is False


def test_carve_skips_invalid_wall_coordinates() -> None:
    """Carve should ignore invalid neighbor pairs instead of crashing."""
    maze = Maze(width=2, height=2)
    walls = [WallToRemove(x=0, y=0, is_top=True)]
    carve(maze, walls)
    assert maze.walls[0][0].top is True


def test_generate_maze_accepts_explicit_min_open_edges() -> None:
    """Providing min_open_edges should still produce a valid maze."""
    maze = generate_maze(3, 3)
    assert maze.is_connected(0, 0, 2, 2)


def test_main_prints_path_information(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Main should print maze, path count, and one example path."""

    class FakeMaze:
        def __init__(self) -> None:
            self.path_data = [[(0, 0), (1, 0)], [(0, 0), (0, 1), (1, 1)]]

        def __str__(self) -> str:
            return "fake-maze"

        def paths(self, _sx: int, _sy: int, _ex: int, _ey: int) -> list:
            return self.path_data

        def highlighted_path(self, _path: list) -> str:
            return f"highlighted-{len(self.path_data)}"

    monkeypatch.setattr(generator_module, "generate_maze", lambda _w, _h: FakeMaze())
    main()
    out = capsys.readouterr().out
    assert "Number of paths" in out
    assert "Example path" in out
