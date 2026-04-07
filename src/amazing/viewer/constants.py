"""Viewer constants and size presets."""

import colorsys

from amazing.game.constants import MAZE_DIMENSION

TEAM_HUES = [
    0,
    20,
    50,
    100,
    170,
    200,
    240,
    280,
]


def team_color(hue: int) -> tuple[int, int, int]:
    """Converts a hue value to an RGB color tuple.

    Returns:
        An RGB color tuple with values from 0 to 255.
    """
    red, green, blue = colorsys.hsv_to_rgb(hue / 360, 1, 1)
    return int(red * 255), int(green * 255), int(blue * 255)


class Constants:
    """Container for viewer layout and color constants."""

    SCREEN_TITLE = "Amazing Viewer"

    def resize(self, *, small_window: bool) -> None:
        """Apply either normal or small-window screen layout values."""
        if not small_window:
            self.SCREEN_WIDTH = 1777
            self.SCREEN_HEIGHT = 1000
            self.SCORE_WIDTH = 500
            self.SCORE_MARGIN = 20
            self.SCORE_FONT_SIZE = 24
        else:
            self.SCREEN_WIDTH = 800
            self.SCREEN_HEIGHT = 600
            self.SCORE_WIDTH = 300
            self.SCORE_MARGIN = 10
            self.SCORE_FONT_SIZE = 20

        self.SCORE_TIME_MARGIN = self.SCORE_MARGIN // 2
        self.SCORE_HEIGHT = self.SCREEN_HEIGHT
        self.MAP_MARGIN = 10
        self.MAP_MIN_X = int(self.SCORE_WIDTH + self.MAP_MARGIN * 1.2)
        self.MAP_MAX_X = int(self.SCREEN_WIDTH - self.MAP_MARGIN * 1.2)
        self.MAP_MIN_Y = self.MAP_MARGIN
        self.MAP_MAX_Y = self.SCREEN_HEIGHT - self.MAP_MARGIN
        self.MAP_WIDTH = self.MAP_MAX_X - self.MAP_MIN_X
        self.MAP_HEIGHT = self.MAP_MAX_Y - self.MAP_MIN_Y
        self.CELL_WIDTH = self.MAP_WIDTH / MAZE_DIMENSION
        self.CELL_HEIGHT = self.MAP_HEIGHT / MAZE_DIMENSION
        self.DOT_RADIUS = int(min(self.CELL_WIDTH, self.CELL_HEIGHT) * 0.15)


constants: Constants = Constants()
