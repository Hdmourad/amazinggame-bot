"""Window and GUI thread for the Arcade viewer."""

import logging
from importlib.resources import files
from queue import Queue

import arcade

from amazing.viewer.animation import set_date
from amazing.viewer.constants import constants
from amazing.viewer.maze import Maze
from amazing.viewer.player import PlayerLayer

input_queue: Queue = Queue()
logger = logging.getLogger(__name__)


class Window(arcade.Window):
    """Main Arcade window for rendering the maze viewer."""

    def __init__(self, _addr: str, _port: int) -> None:
        """Initialize the window and background assets."""
        super().__init__(
            constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT, constants.SCREEN_TITLE
        )
        arcade.set_background_color(arcade.csscolor.BLACK)
        self.background_texture = arcade.Sprite(
            str(files("amazing.viewer.resources.images").joinpath("concrete.jpg"))
        )
        self.background_sprites = arcade.SpriteList()
        self.maze = Maze()
        self.player_layer = PlayerLayer(self.maze.maze.width, self.maze.maze.height)

    def setup(self) -> None:
        """Build the tiled background sprite list once at startup."""
        base_texture = self.background_texture.texture
        tile_width = int(self.background_texture.width)
        tile_height = int(self.background_texture.height)

        if tile_width <= 0 or tile_height <= 0:
            return

        self.background_sprites = arcade.SpriteList()
        y = tile_height // 2
        while y < self.height + tile_height:
            x = tile_width // 2
            while x < self.width + tile_width:
                tile_sprite = arcade.Sprite()
                tile_sprite.texture = base_texture
                tile_sprite.width = tile_width
                tile_sprite.height = tile_height
                tile_sprite.center_x = x
                tile_sprite.center_y = y
                self.background_sprites.append(tile_sprite)
                x += tile_width
            y += tile_height

        self.maze.setup()

    def on_draw(self) -> None:
        """Render one frame of the viewer."""
        if not input_queue.empty():
            data = input_queue.get()
            date_server = data["time"]
            set_date(date_server)
            self.player_layer.update(data["players"])
            logger.info("Received state update with players: %s", data["players"])

        self.clear()
        self.background_sprites.draw()
        self.maze.draw()
        self.player_layer.draw()


def gui_thread(addr: str, port: int) -> None:
    """Run the viewer event loop in a dedicated GUI thread."""
    window = Window(addr, port)
    try:
        window.setup()
        arcade.run()
    except Exception:
        logger.exception("uncaught exception")
