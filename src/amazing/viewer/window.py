import logging
from importlib.resources import files
from queue import Queue

import arcade

from amazing.viewer.animation import set_date
from amazing.viewer.constants import constants

input_queue: Queue = Queue()


class Window(arcade.Window):
    def __init__(self, addr: str, port: int) -> None:
        super().__init__(
            constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT, constants.SCREEN_TITLE
        )
        arcade.set_background_color(arcade.csscolor.BLACK)
        self.background_texture = arcade.Sprite(
            str(files("amazing.viewer.resources.images").joinpath("concrete.jpg"))
        )
        self.background_sprites = arcade.SpriteList()

    def setup(self) -> None:
        tile_width = int(self.background_texture.width)
        tile_height = int(self.background_texture.height)

        if tile_width <= 0 or tile_height <= 0:
            return

        self.background_sprites = arcade.SpriteList()
        y = tile_height // 2
        while y < self.height + tile_height:
            x = tile_width // 2
            while x < self.width + tile_width:
                tile_sprite = arcade.Sprite(
                    str(
                        files("amazing.viewer.resources.images").joinpath(
                            "concrete.jpg"
                        )
                    )
                )
                tile_sprite.center_x = x
                tile_sprite.center_y = y
                self.background_sprites.append(tile_sprite)
                x += tile_width
            y += tile_height

    def on_draw(self) -> None:
        if not input_queue.empty():
            data = input_queue.get()
            date_server = data["time"]
            set_date(date_server)

        self.clear()
        self.background_sprites.draw()


def gui_thread(addr: str, port: int) -> None:
    window = Window(addr, port)
    try:
        window.setup()
        arcade.run()
    except Exception:
        logging.exception("uncaught exception")
