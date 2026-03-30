"""Tests for the game runtime objects."""

from __future__ import annotations

from typing import cast

import pytest

import amazing.game.game as game_module
from amazing.game.constants import (
    MAX_BLOCKED_COUNTER,
    MAX_GAME_DURATION_SECONDS,
    MAX_NB_PLAYERS,
)
from amazing.game.game import Game
from amazing.game.player import BlockedPlayerError, Player


class StubPlayer:
    """Minimal player double for Game tests."""

    def __init__(self) -> None:
        self.updated_with: list[float] = []
        self.commands: list[str] = []

    def manage_command(self, command: str) -> str:
        self.commands.append(command)
        return "OK"

    def update(self, delta_time: float) -> None:
        self.updated_with.append(delta_time)

    @staticmethod
    def state() -> dict[str, str | bool | int | float | tuple[float, float]]:
        return {
            "name": "stub",
            "blocked": False,
            "score": 7,
            "speed": 0.0,
            "orientation": 0,
            "position": (0.5, 0.5),
        }


def test_game_constants_are_stable() -> None:
    """Game constants should keep their published values."""
    assert MAX_GAME_DURATION_SECONDS == 300
    assert MAX_NB_PLAYERS == 20
    assert MAX_BLOCKED_COUNTER == 3


def test_game_initialization_and_start_reset_timers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Game should initialize and restart with perf counter timestamps."""
    times = iter([10.0, 20.0])
    monkeypatch.setattr(game_module, "perf_counter", lambda: next(times))

    game = Game()
    assert game.start_time == pytest.approx(10.0)
    assert game.last_update_time == pytest.approx(10.0)
    assert game.finished is False

    game.start()
    assert game.start_time == pytest.approx(20.0)
    assert game.last_update_time == pytest.approx(20.0)


def test_game_manage_command_returns_blocked_for_unknown_player(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unknown player ids should be rejected and logged."""
    game = Game()

    with caplog.at_level("ERROR"):
        assert game.manage_command(0, "MOVE north") == "BLOCKED"

    assert "Unknown player ID" in caplog.text


def test_game_add_player_respects_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Game should not add more players than the configured limit."""
    monkeypatch.setattr(game_module, "MAX_NB_PLAYERS", 1)

    game = Game()
    game.add_player("alice")
    game.add_player("bob")

    assert [player.name for player in game.players] == ["alice"]


def test_game_update_manage_command_and_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Game should update players and expose a serializable state."""
    game = Game()
    stub_player = cast("Player", StubPlayer())
    game.players = [stub_player]
    game.last_update_time = 1.0
    monkeypatch.setattr(game_module, "perf_counter", lambda: 1.25)

    assert game.manage_command(0, "FIRE 1") == "OK"
    game.update()

    assert game.cumulated_time == pytest.approx(0.25)
    assert game.last_update_time == pytest.approx(1.25)
    assert game.state() == {
        "time": pytest.approx(0.25),
        "players": [
            {
                "name": "stub",
                "blocked": False,
                "score": 7,
                "speed": 0.0,
                "orientation": 0,
                "position": (0.5, 0.5),
            }
        ],
    }


@pytest.mark.parametrize(
    ("command", "method_name", "expected"),
    [
        ("MOVE north", "move", "MOVE_OK"),
        ("FIRE east", "fire", "FIRE_OK"),
        ("RADAR area", "radar", "RADAR_OK"),
    ],
)
def test_player_dispatches_known_commands(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    method_name: str,
    expected: str,
) -> None:
    """Player should dispatch supported commands to the matching method."""
    player = Player("alice", Game())
    monkeypatch.setattr(
        Player,
        method_name,
        lambda self, _args, result=expected: result,
        raising=False,
    )

    assert player.manage_command(command) == expected


def test_player_invalid_commands_increment_block_counter() -> None:
    """Invalid commands should eventually block the player."""
    player = Player("alice", Game())

    assert player.manage_command("INVALID") == "KO"
    assert player.blocked_counter == 1
    assert player.blocked is False

    assert player.manage_command("INVALID") == "KO"
    assert player.manage_command("INVALID") == "KO"
    with pytest.raises(BlockedPlayerError):
        player.manage_command("INVALID")
    assert player.blocked_counter == 4
    assert player.blocked is True


def test_player_blocked_update_and_state() -> None:
    """Blocked state and serialization should reflect the player counters."""
    player = Player("alice", Game())
    player.accelerate()
    player.turn_right()
    player.blocked_counter = MAX_BLOCKED_COUNTER + 1

    with pytest.raises(BlockedPlayerError):
        player.manage_command("MOVE north")
    player.update(0.5)
    assert player.state() == {
        "name": "alice",
        "blocked": True,
        "score": 0,
        "speed": pytest.approx(0.1),
        "orientation": -10,
        "position": (0.5, 0.5),
    }


def test_player_motion_methods_and_update() -> None:
    """Player motion attributes should update from speed and orientation."""
    player = Player("alice", Game())

    assert player.state()["speed"] == pytest.approx(0.0)
    assert player.state()["orientation"] == 0
    assert player.state()["position"] == (0.5, 0.5)

    player.accelerate()
    player.accelerate()
    player.decelerate()
    player.turn_right()
    player.turn_right()
    player.update(2.0)

    state = player.state()
    assert state["speed"] == pytest.approx(0.1)
    assert state["orientation"] == -20
    x_pos, y_pos = state["position"]
    assert x_pos == pytest.approx(0.6879385241571817)
    assert y_pos == pytest.approx(0.43159597133486625)
