"""Player state and command handling."""

import logging
import math
from typing import TYPE_CHECKING, NoReturn, TypedDict

from amazing.game.constants import (
    MAX_BLOCKED_COUNTER,
    MAX_EXPLORATION_DURATION_SECONDS,
    MAX_RACE_DURATION_SECONDS,
)

if TYPE_CHECKING:
    from amazing.game.game import Game

logger = logging.getLogger(__name__)


class BlockedPlayerError(Exception):
    """Exception raised when a blocked player attempts to perform an action."""

    def __init__(self, player_name: str) -> None:
        """Initialize with the name of the blocked player."""
        super().__init__(f"Player {player_name} is blocked.")
        self.name = player_name


class PlayerState(TypedDict):
    """Serializable player state payload."""

    id: int
    name: str
    blocked: bool
    nb_visited_cells: int
    score: int
    speed: float
    orientation: int
    position: tuple[float, float]
    finished: bool
    race_time: float


def _raise_unknown_command(command_str: str) -> NoReturn:
    message = f"Unknown command: {command_str}"
    raise ValueError(message)


_ANGLE_EPS = 1e-9  # threshold below which a direction component is treated as zero


class Player:
    """Represents one player connected to the game server."""

    def __init__(self, name: str, game: Game) -> None:
        """Initialize player state for a new game participant."""
        self.name = name
        self.blocked_counter = 0
        self.game = game
        self._speed = 0.0
        self._orientation = 0
        self.position = (0.5, 0.5)
        self.id = 0
        self.visited_cells: set[tuple[int, int]] = set()
        self.finished = False
        self.race_time: float = 0.0

    def reset(self) -> None:
        """Reset player state for the start of a race."""
        self.blocked_counter = 0
        self._speed = 0.0
        self._orientation = 0
        self.position = (0.5, 0.5)
        self.finished = False

    @property
    def blocked(self) -> bool:
        """Return whether the player is blocked after repeated invalid commands."""
        return self.blocked_counter > MAX_BLOCKED_COUNTER

    @property
    def score(self) -> int:
        """Return the player's score based on visited cells."""
        race_score = 0
        if self.race_time and self.game:
            race_score = int(
                self.game.maze.width
                * self.game.maze.height
                * (MAX_RACE_DURATION_SECONDS - self.race_time)
                / MAX_RACE_DURATION_SECONDS
            )
        return (
            self.nb_visited_cells
            + race_score
            + 10 * int(self.finished and not self.game.exploration_phase)
        )

    @property
    def nb_visited_cells(self) -> int:
        """Return the number of visited cells."""
        return len(self.visited_cells)

    def manage_command(self, command_str: str) -> str:
        """Validate and dispatch a player command.

        Returns:
            The command result returned to the client.

        Raises:
            BlockedPlayerError: If the player is currently blocked.
        """
        if self.blocked:
            raise BlockedPlayerError(self.name)
        command = command_str.split()
        try:
            if command[0] in {
                "ACCELERATE",
                "DECELERATE",
                "TURN_RIGHT",
                "TURN_LEFT",
                "GET_SENSORS",
            }:
                return getattr(self, command[0].lower())()
            _raise_unknown_command(command_str)
        except ValueError as e:
            logger.warning("Problem for %s: %s", self.name, e)
            self.blocked_counter += 1
            if self.blocked:
                raise BlockedPlayerError(self.name) from e
            return "KO"

    def update(self, delta_time: float) -> None:
        """Update runtime player state for one frame."""
        if self.blocked:
            return

        orientation_radians = math.radians(-self._orientation)
        delta_x = math.cos(orientation_radians) * self._speed * delta_time
        delta_y = math.sin(orientation_radians) * self._speed * delta_time
        self.position = (self.position[0] + delta_x, self.position[1] + delta_y)
        self.visited_cells.add((int(self.position[0]), int(self.position[1])))
        if not self.finished:
            self.race_time = max(
                0, self.game.cumulated_time - MAX_EXPLORATION_DURATION_SECONDS
            )
        if (
            self.game.maze is not None
            and int(self.position[0]) == self.game.maze.width - 1
            and int(self.position[1]) == self.game.maze.height - 1
        ):
            self.finished = True

    def accelerate(self) -> str:
        """Increase player speed by 0.1 cell/s.

        Returns:
            "OK" status string.
        """
        self._speed += 0.1
        return "OK"

    def decelerate(self) -> str:
        """Decrease player speed by 0.1 cell/s.

        Returns:
            "OK" status string.
        """
        self._speed -= 0.1
        self._speed = max(self._speed, 0)
        return "OK"

    def turn_right(self) -> str:
        """Rotate orientation by -10 degrees.

        Returns:
            "OK" status string.
        """
        self._orientation -= 10
        self._orientation = ((self._orientation % 360) + 360) % 360
        return "OK"

    def turn_left(self) -> str:
        """Rotate orientation by 10 degrees.

        Returns:
            "OK" status string.
        """
        self._orientation += 10
        self._orientation = ((self._orientation % 360) + 360) % 360
        return "OK"

    def _ray_distance(self, sensor_orientation: int) -> float:
        """Return distance from player center to the nearest wall along a ray.

        Uses a DDA algorithm on the cell grid.  The angle convention matches
        ``update``: ``math.radians(-sensor_orientation)`` gives the direction
        vector angle.

        Args:
            sensor_orientation: Ray direction in degrees.

        Returns:
            Distance in cell units to the nearest wall.
        """
        dx = math.cos(math.radians(-sensor_orientation))
        dy = math.sin(math.radians(-sensor_orientation))

        px, py = self.position
        maze = self.game.maze

        cx = max(0, min(maze.width - 1, math.floor(px)))
        cy = max(0, min(maze.height - 1, math.floor(py)))

        if abs(dx) < _ANGLE_EPS:
            t_max_x = math.inf
            t_delta_x = math.inf
        else:
            t_max_x = (
                (math.floor(px + _ANGLE_EPS) + 1 - px) / dx
                if dx > 0
                else (math.ceil(px - _ANGLE_EPS) - 1 - px) / dx
            )
            t_delta_x = 1.0 / abs(dx)

        if abs(dy) < _ANGLE_EPS:
            t_max_y = math.inf
            t_delta_y = math.inf
        else:
            t_max_y = (
                (math.floor(py + _ANGLE_EPS) + 1 - py) / dy
                if dy > 0
                else (math.ceil(py - _ANGLE_EPS) - 1 - py) / dy
            )
            t_delta_y = 1.0 / abs(dy)

        for _ in range(2 * (maze.width + maze.height)):
            if t_max_x <= t_max_y:
                wall_x = cx + (1 if dx >= 0 else 0)
                if maze.walls[wall_x][cy].left:
                    return t_max_x
                cx += 1 if dx >= 0 else -1
                t_max_x += t_delta_x
            else:
                wall_y = cy + (1 if dy >= 0 else 0)
                if maze.walls[cx][wall_y].top:
                    return t_max_y
                cy += 1 if dy >= 0 else -1
                t_max_y += t_delta_y

        return float(maze.width + maze.height)  # pragma: no cover

    def get_sensors(self) -> str:
        """Return sensor data for the current player state.

        Returns:
            Space-separated string: time, exploration_phase, x, y, orientation, speed,
            front distance, right distance, rear distance, left distance.
        """
        front = self._ray_distance(self._orientation)
        right = self._ray_distance(self._orientation - 90)
        rear = self._ray_distance(self._orientation + 180)
        left = self._ray_distance(self._orientation + 90)
        return (
            f"{self.game.cumulated_time:.2f} {int(self.game.exploration_phase)} "
            f"{self.position[0]:.2f} {self.position[1]:.2f} "
            f"{self._orientation} {self._speed:.2f} "
            f"{front:.2f} {right:.2f} {rear:.2f} {left:.2f}"
        )

    def state(self) -> PlayerState:
        """Return a serializable view of the player state.

        Returns:
            A dictionary with the public player fields.
        """
        return {
            "id": self.id,
            "name": self.name,
            "blocked": self.blocked,
            "score": self.score,
            "nb_visited_cells": self.nb_visited_cells,
            "speed": self._speed,
            "orientation": self._orientation,
            "position": self.position,
            "finished": self.finished,
            "race_time": self.race_time,
        }
