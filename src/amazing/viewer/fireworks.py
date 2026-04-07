from importlib.resources import files
from pathlib import Path
from time import perf_counter

from arcade.experimental.shadertoy import Shadertoy

import amazing.viewer.resources
from amazing.viewer.constants import constants

ANIMATION_DURATION = 0.9  # seconds


class Firework:
    def __init__(self, position):
        self.shadertoy = Shadertoy(
            (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT),
            main_source=Path(
                str(files(amazing.viewer.resources) / "firework.glsl")
            ).read_text(encoding="utf-8"),
        )
        # uniform vec2 explosionPos;
        self.shadertoy.program["explosionPos"] = position
        self.start_time = perf_counter()

    def render(self):
        self.shadertoy.render(time=perf_counter() - self.start_time)

    def finished(self):
        return perf_counter() - self.start_time > ANIMATION_DURATION
