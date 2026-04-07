"""Player rendering helpers for the Arcade viewer."""

from importlib.resources import files
from typing import Any

import arcade

from amazing.viewer.constants import TEAM_HUES, constants, team_color
from amazing.viewer.utils import hue_changed_texture

POSITION_TRACE_DURATION = 10.0  # seconds of history to display
POSITION_TRACE_PERIOD = 0.2  # seconds between recorded positions


class Player:
    """Renderable player sprite built from server state."""

    def __init__(self) -> None:
        """Initialize a player sprite from a texture."""
        self.sprite = arcade.Sprite()
        self.sprite.texture = hue_changed_texture(
            str(files("amazing.viewer.resources.images").joinpath("car.png")),
            target_hue=50,
        )
        self.sprite.width = 0.8 * constants.CELL_WIDTH
        self.sprite.height = 0.4 * constants.CELL_HEIGHT
        self.position_history: list[tuple[float, float, float]] = []  # (time, x, y)
        self.shape_list = arcade.shape_list.ShapeElementList()
        self.id: int | None = None
        self.hue = 0
        self.color: tuple[int, int, int] = (255, 255, 255)
        self.exploring = True

    def dot_color(self) -> tuple[int, int, int, int]:
        """Return the RGBA color for the position trace dots."""
        return (*self.color, 100)

    def update_from_state(
        self,
        state: dict[str, Any],
        current_time: float,
        nb_players: int,
        *,
        exploration: bool,
    ) -> None:
        """Apply server-side player state to the render sprite.

        Args:
            state: Player state dict from server.
            current_time: Current server time in seconds.
            nb_players: Total number of players in the game.
            exploration: Whether the game is in the exploration phase.
        """
        if exploration != self.exploring:
            self.exploring = exploration
            self.shape_list.clear()
            self.position_history.clear()
        if self.id is None:
            self.id = int(state["id"])
            self.hue = TEAM_HUES[self.id % len(TEAM_HUES)]
            self.color = team_color(self.hue)
            self.sprite.texture = hue_changed_texture(
                str(files("amazing.viewer.resources.images").joinpath("car.png")),
                target_hue=self.hue,
            )
        position = state.get("position", (0.5, 0.5))
        x_pos, y_pos = position
        orientation = state.get("orientation", 0)

        self.sprite.center_x = constants.MAP_MIN_X + x_pos * constants.CELL_WIDTH
        self.sprite.center_y = constants.MAP_MAX_Y - y_pos * constants.CELL_HEIGHT
        self.sprite.angle = -float(orientation)

        # Record position history with timestamp
        screen_x = self.sprite.center_x
        screen_y = self.sprite.center_y
        if (
            not self.position_history
            or current_time - self.position_history[-1][0] >= POSITION_TRACE_PERIOD
        ):
            self.position_history.append((current_time, screen_x, screen_y))
            circle = arcade.shape_list.create_ellipse_filled(
                int(screen_x),
                int(screen_y),
                constants.DOT_RADIUS,
                constants.DOT_RADIUS,
                self.dot_color(),
            )
            self.shape_list.append(circle)

    def draw_trace(self) -> None:
        """Draw the shape list containing trace circles."""
        self.shape_list.draw()
