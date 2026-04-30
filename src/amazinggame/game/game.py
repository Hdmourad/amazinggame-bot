"""Core game state and command orchestration."""
from __future__ import annotations
from __future__ import annotations

import logging
from time import perf_counter
from typing import TYPE_CHECKING, TypedDict

from amazinggame.game import Maze, generate_maze
from amazinggame.game.constants import (
    MAX_EXPLORATION_DURATION_SECONDS,
    MAX_NB_PLAYERS,
    MAX_RACE_DURATION_SECONDS,
    MAZE_DIMENSION,
)
from amazinggame.game.player import Player, PlayerState

if TYPE_CHECKING:
    from amazinggame.game.maze import MazeState

logger = logging.getLogger(__name__)


class GameState(TypedDict):
    """Serializable game state sent to clients."""

    time: float
    players: list[PlayerState]
    exploration: bool
    maze: MazeState | None
    finished: bool


class Game:
    """Runtime container for players, timers, and commands."""

    def __init__(self) -> None:
        """Initialize game timers and player storage."""
        self.start_time = perf_counter()
        self.last_update_time = self.start_time
        self.cumulated_time = 0.0
        self.players: list[Player] = []
        self.maze: Maze = None  # ty: ignore[invalid-assignment]
        self.exploration_phase = True

    @property
    def finished(self) -> bool:
        """Return whether the game has a winner."""
        return (
            (
                all(player.finished for player in self.players)
                and not self.exploration_phase
            )
            or self.cumulated_time
            >= MAX_EXPLORATION_DURATION_SECONDS + MAX_RACE_DURATION_SECONDS
        )

    def start(self) -> None:
        """Reset timers when a game starts."""
        self.maze = generate_maze(MAZE_DIMENSION, MAZE_DIMENSION)
        self.start_time = perf_counter()
        self.last_update_time = self.start_time

    def start_race(self) -> None:
        """Transition from exploration to race."""
        self.exploration_phase = False
        for player in self.players:
            player.reset()

    def manage_command(self, player_id: int, command: str) -> str:
        """Dispatch a command to the matching player.

        Returns:
            The status returned by the player command handler.
        """
        if player_id >= len(self.players):
            logger.error("Unknown player ID: %d", player_id)
            return "BLOCKED"
        return self.players[player_id].manage_command(command)

    def add_player(self, player_name: str) -> int | None:
        """Add a player when the server still has room.

        Returns:
            Assigned player id, or None when the game is full.
        """
        if len(self.players) >= MAX_NB_PLAYERS:
            return None
        player = Player(player_name, self)
        player.id = len(self.players)
        self.players.append(player)
        return player.id

    def update(self) -> None:
        """Advance timers and update every active player."""
        delta_time = perf_counter() - self.last_update_time
        for player in self.players:
            player.update(delta_time)
        self.last_update_time += delta_time
        self.cumulated_time += delta_time
        logger.debug("Cumulated time: %.3f", self.cumulated_time)

    def state(self) -> GameState:
        """Return a serializable snapshot of the game state.

        Returns:
            A dictionary containing elapsed time and serialized players.
        """
        players: list[PlayerState] = [player.state() for player in self.players]
        data: GameState = {
            "time": self.cumulated_time,
            "finished": self.finished,
            "players": players,
            "exploration": self.exploration_phase,
            "maze": self.maze.serialize() if self.maze is not None else None,
        }
        return data
