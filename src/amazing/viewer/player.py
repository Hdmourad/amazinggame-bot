"""Player rendering helpers for the Arcade viewer."""

from importlib.resources import files
from typing import Any

import arcade

from amazing.viewer.constants import constants

texture = arcade.load_texture(
    str(files("amazing.viewer.resources.images").joinpath("car.png"))
)


class Player:
    """Renderable player sprite built from server state."""

    def __init__(self) -> None:
        """Initialize a player sprite from a texture."""
        self.sprite = arcade.Sprite()
        self.sprite.texture = texture

    def update_from_state(
        self,
        state: dict[str, Any],
    ) -> None:
        """Apply server-side player state to the render sprite."""
        position = state.get("position", (0.5, 0.5))
        x_pos, y_pos = position
        orientation = state.get("orientation", 0)

        self.sprite.width = 0.5 * constants.CELL_WIDTH
        self.sprite.height = 0.25 * constants.CELL_HEIGHT
        self.sprite.center_x = constants.MAP_MIN_X + x_pos * constants.CELL_WIDTH
        self.sprite.center_y = constants.MAP_MAX_Y - y_pos * constants.CELL_HEIGHT
        self.sprite.angle = -float(orientation)
