"""Window and GUI thread for the Arcade viewer."""

import logging
from importlib.resources import files
from queue import Queue

import arcade

from amazinggame.game.maze import Maze as GameMaze
from amazinggame.viewer.animation import set_date
from amazinggame.viewer.constants import constants
from amazinggame.viewer.maze import Maze
from amazinggame.viewer.player import Player
from amazinggame.viewer.score import Score

input_queue: Queue = Queue()
logger = logging.getLogger(__name__)


class Window(arcade.Window):
    """Main Arcade window for rendering the maze viewer."""

    def __init__(self, addr: str, port: int) -> None:
        """Initialize the window and background assets."""
        super().__init__(
            constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT, constants.SCREEN_TITLE
        )
        arcade.set_background_color(arcade.csscolor.BLACK)
        self.background_texture = arcade.Sprite(
            str(files("amazinggame.viewer.resources.images").joinpath("concrete.jpg"))
        )
        self.background_sprites = arcade.SpriteList()
        self.maze = Maze()
        self._maze_loaded_from_server = False
        self.players: dict[int, Player] = {}
        self.players_sprite_list = arcade.SpriteList()
        self.score = Score(addr, port)
        self.dot_list = arcade.shape_list.ShapeElementList()

    def setup(self) -> None:
        """Build the tiled background sprite list once at startup."""
        self.score.setup()
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
            self.score.update(data)

            if not self._maze_loaded_from_server and data.get("maze") is not None:
                self.maze.maze = GameMaze.deserialize(data["maze"])
                self.maze.setup()
                self._maze_loaded_from_server = True

            for state in data["players"]:
                player_id = int(state["id"])
                if player_id not in self.players:
                    self.players[player_id] = Player(self.dot_list)
                    self.players_sprite_list.append(self.players[player_id].sprite)

                self.players[player_id].update_from_state(
                    state,
                    date_server,
                    exploration=data["exploration"],
                )
            # logger.info("Received state update with players: %s", data["players"]) # noqa: ERA001

        self.clear()
        self.background_sprites.draw()
        self.maze.draw()
        for player in self.players.values():
            player.draw_trace()
        self.dot_list.draw()
        self.players_sprite_list.draw()
        self.score.draw()

        self.ctx.enable_only(self.ctx.BLEND)
        for player in self.players.values():
            player.draw_explosion()


def gui_thread(addr: str, port: int) -> None:
    """Run the viewer event loop in a dedicated GUI thread."""
    window = Window(addr, port)
    try:
        window.setup()
        arcade.run()
    except Exception:
        logger.exception("uncaught exception")
