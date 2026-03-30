"""Viewer constants and size presets."""

import colorsys
import math
from typing import ClassVar

from amazing.game.constants import MAZE_DIMENSION


def _team_color(hue: int) -> tuple[int, int, int]:
    red, green, blue = colorsys.hsv_to_rgb(((hue * math.pi / 2) % 360) / 360, 1, 1)
    return int(red * 255), int(green * 255), int(blue * 255)


class Constants:
    """Container for viewer layout and color constants."""

    SCREEN_TITLE = "Amazing Viewer"
    TEAM_HUES: ClassVar[dict[int, int]] = {0: 0, 1: 30, 2: 65, 3: 120}
    TEAM_COLORS: ClassVar[dict[int, tuple[int, int, int]]] = {
        team: _team_color(hue) for team, hue in TEAM_HUES.items()
    }

    def resize(self, *, small_window: bool) -> None:
        """Apply either normal or small-window screen layout values."""
        if not small_window:
            self.SCREEN_WIDTH = 1777
            self.SCREEN_HEIGHT = 1000
            self.SCORE_WIDTH = 500
            self.SCORE_MARGIN = 100
            self.SCORE_FONT_SIZE = 24
            self.SCORE_TEAM_SIZE = 190
            self.MAP_MARGIN = 30
        else:
            self.SCREEN_WIDTH = 800
            self.SCREEN_HEIGHT = 600
            self.SCORE_WIDTH = 300
            self.SCORE_MARGIN = 50
            self.SCORE_FONT_SIZE = 20
            self.SCORE_TEAM_SIZE = 105
            self.MAP_MARGIN = 50

        self.SCORE_TIME_MARGIN = 100
        self.SCORE_HEIGHT = self.SCREEN_HEIGHT
        self.MAP_MIN_X = int(self.SCORE_WIDTH + self.MAP_MARGIN * 1.2)
        self.MAP_MAX_X = int(self.SCREEN_WIDTH - self.MAP_MARGIN * 1.2)
        self.MAP_MIN_Y = self.MAP_MARGIN
        self.MAP_MAX_Y = self.SCREEN_HEIGHT - self.MAP_MARGIN
        self.MAP_WIDTH = self.MAP_MAX_X - self.MAP_MIN_X
        self.MAP_HEIGHT = self.MAP_MAX_Y - self.MAP_MIN_Y
        self.CELL_WIDTH = self.MAP_WIDTH / MAZE_DIMENSION
        self.CELL_HEIGHT = self.MAP_HEIGHT / MAZE_DIMENSION


constants: Constants = Constants()
