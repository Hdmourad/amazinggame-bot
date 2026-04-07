from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files

import arcade

from amazing.viewer.constants import constants, team_color


@lru_cache(maxsize=32)
def get_texts(
    text: str, x: int, y: int, color: tuple[int, int, int], size: int
) -> list[arcade.Text]:
    texts: list[arcade.Text] = []
    halo_color = (255, 255, 255, 50)
    for offset_x in (-1, 1):
        for offset_y in (-1, 1):
            texts.append(
                arcade.Text(
                    text,
                    x + offset_x,
                    y + offset_y,
                    halo_color,
                    font_size=size,
                    font_name="Sportrop",
                )
            )
    texts.append(
        arcade.Text(
            text,
            x,
            y,
            color,
            font_size=size,
            font_name="Sportrop",
        )
    )
    return texts


def draw_text(
    text: str, x: int, y: int, color: tuple[int, int, int], size: int
) -> None:
    for predrawn_text in get_texts(text, x, y, color, size):
        predrawn_text.draw()


@dataclass(frozen=True)
class TeamData:
    name: str
    color: tuple[int, int, int]
    blocked: bool
    score: int


class Score:
    def __init__(self, addr: str, port: int):
        self.teams_data: list[TeamData] = []
        self.port = port
        self.addr = addr
        self.time = 0.0

    def setup(self) -> None:
        font_file = files("amazing.viewer.resources.fonts").joinpath("Sportrop.ttf")

        arcade.load_font(str(font_file))

    def draw(self) -> None:
        draw_text(
            f"Time: {int(self.time)}",
            constants.SCORE_MARGIN,
            constants.SCORE_HEIGHT - constants.SCORE_TIME_MARGIN,
            (255, 255, 255),
            size=constants.SCORE_FONT_SIZE,
        )
        draw_text(
            f"{self.addr} : {self.port}",
            constants.SCORE_MARGIN,
            constants.SCORE_HEIGHT
            - constants.SCORE_TIME_MARGIN
            - constants.SCORE_TEAM_SIZE // 4,
            (255, 255, 255),
            size=constants.SCORE_FONT_SIZE - 4,
        )
        for index, team_data in enumerate(
            sorted(self.teams_data, key=lambda td: td.score)
        ):
            team_offset = constants.SCORE_TEAM_SIZE + index * constants.SCORE_TEAM_SIZE

            draw_text(
                team_data.name[:18],
                constants.SCORE_MARGIN,
                team_offset,
                team_data.color,
                size=constants.SCORE_FONT_SIZE,
            )
            if team_data.blocked:
                draw_text(
                    "BLOCKED",
                    constants.SCORE_MARGIN,
                    team_offset - constants.SCORE_TEAM_SIZE // 4,
                    team_data.color,
                    size=constants.SCORE_FONT_SIZE - 5,
                )
            else:
                score = f"{team_data.score:_d}".replace("_", " ")
                draw_text(
                    f"Score: {score}",
                    constants.SCORE_MARGIN,
                    team_offset - constants.SCORE_TEAM_SIZE // 4,
                    team_data.color,
                    size=constants.SCORE_FONT_SIZE - 5,
                )

    def update(self, server_data: dict) -> None:
        self.time = server_data["time"]
        self.teams_data.clear()
        for player_data in server_data["players"]:
            self.teams_data.append(
                TeamData(
                    name=player_data["name"],
                    color=team_color(player_data["id"] * 30 % 360),
                    blocked=player_data["blocked"],
                    score=player_data["score"],
                )
            )
