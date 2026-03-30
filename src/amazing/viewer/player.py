"""Player rendering helpers for the Arcade viewer."""

from importlib.resources import files
from typing import Any

import arcade

from amazing.viewer.constants import constants


class Player:
    """Renderable player sprite built from server state."""

    def __init__(self, texture: arcade.Texture) -> None:
        """Initialize a player sprite from a texture."""
        self.sprite = arcade.Sprite()
        self.sprite.texture = texture

    def update_from_state(
        self,
        state: dict[str, Any],
        *,
        cell_width: float,
        cell_height: float,
    ) -> None:
        """Apply server-side player state to the render sprite."""
        position = state.get("position", (0.5, 0.5))
        x_pos, y_pos = position
        orientation = state.get("orientation", 0)

        self.sprite.width = 0.5 * cell_width
        self.sprite.height = 0.25 * cell_height
        self.sprite.center_x = constants.MAP_MIN_X + x_pos * cell_width
        self.sprite.center_y = constants.MAP_MAX_Y - y_pos * cell_height
        self.sprite.angle = -float(orientation)


class PlayerLayer:
    """Container that builds and draws all player sprites."""

    def __init__(self, maze_width: int, maze_height: int) -> None:
        """Initialize layer dimensions and texture resources."""
        self.maze_width = maze_width
        self.maze_height = maze_height
        self.texture = arcade.load_texture(
            str(files("amazing.viewer.resources.images").joinpath("car.png"))
        )
        self.sprites = arcade.SpriteList()

    def update(self, players: list[dict[str, Any]]) -> None:
        """Rebuild sprites from the latest server player list."""
        cell_width = constants.MAP_WIDTH / self.maze_width
        cell_height = constants.MAP_HEIGHT / self.maze_height

        self.sprites = arcade.SpriteList()
        for state in players:
            player = Player(self.texture)
            player.update_from_state(
                state,
                cell_width=cell_width,
                cell_height=cell_height,
            )
            self.sprites.append(player.sprite)

    def draw(self) -> None:
        """Draw all player sprites."""
        self.sprites.draw()
