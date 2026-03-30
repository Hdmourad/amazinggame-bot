"""Maze rendering for the Arcade viewer."""

from importlib.resources import files

import arcade

from amazing.game.constants import MAZE_DIMENSION
from amazing.game.generator import generate_maze
from amazing.viewer.constants import constants


class Maze:
    """Maze sprite builder and renderer."""

    def __init__(self) -> None:
        """Initialize maze data and rendering resources."""
        self.maze = generate_maze(MAZE_DIMENSION, MAZE_DIMENSION)
        self.wall_texture = arcade.Sprite(
            str(files("amazing.viewer.resources.images").joinpath("brick.png"))
        )
        self.wall_sprites = arcade.SpriteList()

    def setup(self) -> None:
        """Build textured wall sprites once at startup."""
        base_texture = self.wall_texture.texture
        maze_width = self.maze.width
        maze_height = self.maze.height

        wall_thickness = max(
            6, int(min(constants.CELL_WIDTH, constants.CELL_HEIGHT) * 0.18)
        )

        self.wall_sprites = arcade.SpriteList()

        def _append_horizontal_wall(
            self: Maze,
            *,
            x: int,
            y: int,
        ) -> None:
            wall = arcade.Sprite()
            wall.texture = base_texture
            wall.width = int(constants.CELL_WIDTH) + wall_thickness
            wall.height = wall_thickness
            wall.center_x = constants.MAP_MIN_X + (x + 0.5) * constants.CELL_WIDTH
            wall.center_y = constants.MAP_MAX_Y - y * constants.CELL_HEIGHT
            self.wall_sprites.append(wall)

        def _append_vertical_wall(
            self: Maze,
            *,
            x: int,
            y: int,
        ) -> None:
            wall = arcade.Sprite()
            wall.texture = base_texture
            wall.width = wall_thickness
            wall.height = int(constants.CELL_HEIGHT) + wall_thickness
            wall.center_x = constants.MAP_MIN_X + x * constants.CELL_WIDTH
            wall.center_y = constants.MAP_MAX_Y - (y + 0.5) * constants.CELL_HEIGHT
            self.wall_sprites.append(wall)

        for x in range(maze_width + 1):
            for y in range(maze_height + 1):
                cell = self.maze.walls[x][y]

                if x < maze_width and cell.top:
                    _append_horizontal_wall(
                        self,
                        x=x,
                        y=y,
                    )

                if y < maze_height and cell.left:
                    _append_vertical_wall(
                        self,
                        x=x,
                        y=y,
                    )

    def draw(self) -> None:
        """Draw maze wall sprites."""
        arcade.draw_lbwh_rectangle_filled(
            constants.MAP_MIN_X,
            constants.MAP_MIN_Y,
            constants.MAP_WIDTH,
            constants.MAP_HEIGHT,
            (255, 255, 255, 120),
        )
        self.wall_sprites.draw()
