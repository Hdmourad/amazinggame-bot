from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files

import arcade

from amazing.game.constants import MAX_EXPLORATION_DURATION_SECONDS
from amazing.viewer.constants import TEAM_HUES, constants, team_color


@lru_cache(maxsize=128)
def get_texts(
    text: str, x: int, y: int, color: tuple[int, int, int], size: int
) -> list[arcade.Text]:
    texts: list[arcade.Text] = []
    for offset_x in (-1, 1):
        for offset_y in (-1, 1):
            texts.append(
                arcade.Text(
                    text,
                    x + offset_x,
                    y + offset_y,
                    color,
                    font_size=size,
                    font_name="Fira Code",
                )
            )
    texts.append(
        arcade.Text(
            text,
            x,
            y,
            color,
            font_size=size,
            font_name="Fira Code",
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
    nb_visited_cells: int
    race_time: float = 0.0


class Score:
    def __init__(self, addr: str, port: int):
        self.teams_data: list[TeamData] = []
        self.port = port
        self.addr = addr
        self.time = 0.0
        self.shape_list = arcade.shape_list.ShapeElementList()

    def setup(self) -> None:
        font_file = files("amazing.viewer.resources.fonts").joinpath(
            "FiraCode-Bold.ttf"
        )

        arcade.load_font(str(font_file))
        self.shape_list.clear()
        self.shape_list.append(
            arcade.shape_list.create_rectangle_filled(
                constants.SCORE_WIDTH // 2,
                constants.SCORE_HEIGHT // 2,
                constants.SCORE_WIDTH,
                constants.SCORE_HEIGHT,
                (220, 220, 220, 150),
            )
        )

    @staticmethod
    def time_str(seconds: float) -> str:
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes)}:{int(seconds):02d}.{int((seconds - int(seconds)) * 100):02d}"

    def draw(self) -> None:
        self.shape_list.draw()
        draw_text(
            f"Time: {self.time_str(self.time)}",
            constants.SCORE_MARGIN,
            constants.SCORE_HEIGHT
            - constants.SCORE_TIME_MARGIN
            - constants.SCORE_FONT_SIZE,
            (255, 255, 255),
            size=constants.SCORE_FONT_SIZE,
        )
        draw_text(
            f"{self.addr} : {self.port}",
            constants.SCORE_MARGIN,
            constants.SCORE_HEIGHT
            - constants.SCORE_TIME_MARGIN
            - 2 * constants.SCORE_FONT_SIZE,
            (255, 255, 255),
            size=constants.SCORE_FONT_SIZE - 4,
        )
        for index, team_data in enumerate(
            sorted(self.teams_data, key=lambda td: td.score)
        ):
            team_size = constants.SCORE_HEIGHT // (len(self.teams_data) + 1)
            team_offset = team_size + index * team_size

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
                    team_offset - team_size // 4,
                    team_data.color,
                    size=constants.SCORE_FONT_SIZE - 5,
                )
            else:
                score = f"{team_data.score:_d}".replace("_", " ")
                draw_text(
                    f"Score: {score}",
                    constants.SCORE_MARGIN,
                    team_offset - team_size // 4,
                    team_data.color,
                    size=constants.SCORE_FONT_SIZE - 5,
                )
                draw_text(
                    f"Visited Cells: {team_data.nb_visited_cells:3d}     "
                    f"Time: {self.time_str(team_data.race_time)}",
                    constants.SCORE_MARGIN,
                    team_offset - 2 * team_size // 4,
                    team_data.color,
                    size=constants.SCORE_FONT_SIZE - 8,
                )

    def update(self, server_data: dict) -> None:
        if server_data["time"] < MAX_EXPLORATION_DURATION_SECONDS:
            self.time = MAX_EXPLORATION_DURATION_SECONDS - server_data["time"]
        else:
            self.time = server_data["time"] - MAX_EXPLORATION_DURATION_SECONDS
        self.teams_data.clear()
        for player_data in server_data["players"]:
            self.teams_data.append(
                TeamData(
                    name=player_data["name"],
                    color=team_color(TEAM_HUES[player_data["id"] % len(TEAM_HUES)]),
                    blocked=player_data["blocked"],
                    score=player_data["score"],
                    nb_visited_cells=player_data["nb_visited_cells"],
                    race_time=player_data["race_time"]
                    if player_data["finished"]
                    else 0.0,
                )
            )
