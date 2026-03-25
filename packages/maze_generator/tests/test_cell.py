"""Tests for maze_generator.cell module."""

from maze_generator.cell import Cell


class TestCell:
    """Test cases for Cell class."""

    def test_cell_initialization_sets_top_and_left_walls(self) -> None:
        """Cell should initialize with top and left wall states."""
        cell = Cell(top=True, left=False)
        assert cell.top is True
        assert cell.left is False

    def test_cell_defaults_to_walls_present(self) -> None:
        """Cell should default to walls being present if not specified."""
        cell = Cell()
        assert cell.top is True
        assert cell.left is True

    def test_cell_can_change_wall_states(self) -> None:
        """Cell wall states should be modifiable."""
        cell = Cell(top=True, left=True)
        cell.top = False
        cell.left = False
        assert cell.top is False
        assert cell.left is False

    def test_cell_equality_based_on_wall_states(self) -> None:
        """Cells should be equal if they have the same wall states."""
        cell1 = Cell(top=True, left=False)
        cell2 = Cell(top=True, left=False)
        cell3 = Cell(top=False, left=True)

        assert cell1 == cell2
        assert cell1 != cell3

    def test_cell_string_representation(self) -> None:
        """Cell should have a readable string representation."""
        cell = Cell(top=True, left=False)
        str_repr = str(cell)
        assert "top=True" in str_repr
        assert "left=False" in str_repr
