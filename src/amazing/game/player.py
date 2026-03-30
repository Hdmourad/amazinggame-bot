"""Player state and command handling."""

import logging
import math
from typing import TYPE_CHECKING, NoReturn, TypedDict

from amazing.game.constants import MAX_BLOCKED_COUNTER

if TYPE_CHECKING:
    from amazing.game.game import Game

logger = logging.getLogger(__name__)


class BlockedPlayerError(Exception):
    """Exception raised when a blocked player attempts to perform an action."""

    def __init__(self, player_name: str) -> None:
        """Initialize with the name of the blocked player."""
        super().__init__(f"Player {player_name} is blocked.")
        self.name = player_name


# TODO manage a rotation speed


class PlayerState(TypedDict):
    """Serializable player state payload."""

    name: str
    blocked: bool
    score: int
    speed: float
    orientation: int
    position: tuple[float, float]


def _raise_unknown_command(command_str: str) -> NoReturn:
    message = f"Unknown command: {command_str}"
    raise ValueError(message)


class Player:
    """Represents one player connected to the game server."""

    def __init__(self, name: str, game: Game) -> None:
        """Initialize player state for a new game participant."""
        self.name = name
        self.blocked_counter = 0
        self.game = game
        self.score = 0
        self._speed = 0.0
        self._orientation = 0
        self._position = (0.5, 0.5)

    @property
    def blocked(self) -> bool:
        """Return whether the player is blocked after repeated invalid commands."""
        return self.blocked_counter > MAX_BLOCKED_COUNTER

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
            if command[0] in {"ACCELERATE", "DECELERATE", "TURN_RIGHT", "TURN_LEFT"}:
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
        self._position = (self._position[0] + delta_x, self._position[1] + delta_y)

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
        return "OK"

    def turn_left(self) -> str:
        """Rotate orientation by 10 degrees.

        Returns:
            "OK" status string.
        """
        self._orientation += 10
        return "OK"

    def state(self) -> PlayerState:
        """Return a serializable view of the player state.

        Returns:
            A dictionary with the public player fields.
        """
        return {
            "name": self.name,
            "blocked": self.blocked,
            "score": self.score,
            "speed": self._speed,
            "orientation": self._orientation,
            "position": self._position,
        }
