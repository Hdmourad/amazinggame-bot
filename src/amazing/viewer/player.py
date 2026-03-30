"""Player rendering helpers for the Arcade viewer."""

from importlib.resources import files
from typing import Any

import arcade

from amazing.viewer.constants import constants

POSITION_TRACE_DURATION = 10.0  # seconds of history to display
DOT_RADIUS = 3  # pixels
DOT_COLOR = (200, 200, 200, 200)  # light gray with transparency

texture = arcade.load_texture(
    str(files("amazing.viewer.resources.images").joinpath("car.png"))
)


class Player:
    """Renderable player sprite built from server state."""

    def __init__(self) -> None:
        """Initialize a player sprite from a texture."""
        self.sprite = arcade.Sprite()
        self.sprite.texture = texture
        self.position_history: list[tuple[float, float, float]] = []  # (time, x, y)

    def update_from_state(
        self,
        state: dict[str, Any],
        current_time: float,
    ) -> None:
        """Apply server-side player state to the render sprite.

        Args:
            state: Player state dict from server.
            current_time: Current server time in seconds.
        """
        position = state.get("position", (0.5, 0.5))
        x_pos, y_pos = position
        orientation = state.get("orientation", 0)

        self.sprite.width = 0.5 * constants.CELL_WIDTH
        self.sprite.height = 0.25 * constants.CELL_HEIGHT
        self.sprite.center_x = constants.MAP_MIN_X + x_pos * constants.CELL_WIDTH
        self.sprite.center_y = constants.MAP_MAX_Y - y_pos * constants.CELL_HEIGHT
        self.sprite.angle = -float(orientation)

        # Record position history with timestamp
        screen_x = self.sprite.center_x
        screen_y = self.sprite.center_y
        self.position_history.append((current_time, screen_x, screen_y))

        # Prune history older than POSITION_TRACE_DURATION
        cutoff_time = current_time - POSITION_TRACE_DURATION
        self.position_history = [
            (t, x, y) for t, x, y in self.position_history if t >= cutoff_time
        ]

    def draw_trace(self) -> None:
        """Draw dots for the position history."""
        for _time, x, y in self.position_history:
            arcade.draw_circle_filled(int(x), int(y), DOT_RADIUS, DOT_COLOR)
