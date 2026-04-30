"""Network game server that coordinates players and spectators."""
from __future__ import annotations
import argparse
import contextlib
import json
import logging
import sys
from time import perf_counter, sleep

from amazinggame.game.constants import (
    MAX_BLOCKED_COUNTER,
    MAX_EXPLORATION_DURATION_SECONDS,
    MAX_NB_PLAYERS,
    MAX_RACE_DURATION_SECONDS,
)
from amazinggame.game.game import Game
from amazinggame.game.player import BlockedPlayerError
from amazinggame.network.data_handler import NetworkError
from amazinggame.network.server import ClientData, Server

FRAME_WINDOW_SECONDS = 0.033
logger = logging.getLogger(__name__)


class GameServer(Server):
    """Host a maze game and synchronize connected clients."""

    def __init__(
        self: GameServer, host: str, port: int, connection_timeout: int
    ) -> None:
        """Start the server, wait for players, then initialize the game."""
        super().__init__(host, port)
        self.connection_timeout = connection_timeout
        self.game = Game()
        self._wait_connections()
        for player in self.players:
            player.player_id = self.game.add_player(player.name)

    @property
    def players(self) -> list[ClientData]:
        """Return non-spectator clients."""
        return [client for client in list(self.clients) if not client.spectator]

    @property
    def spectators(self) -> list[ClientData]:
        """Return spectator clients."""
        return [client for client in list(self.clients) if client.spectator]

    def remove_client(self: GameServer, client: ClientData) -> None:
        """Remove a client and mark its player as blocked when relevant."""
        if client in self.clients:
            self.clients.remove(client)
        if (
            not client.spectator
            and client.player_id is not None
            and client.player_id < len(self.game.players)
        ):
            self.game.players[client.player_id].blocked_counter = (
                MAX_BLOCKED_COUNTER + 1
            )

    def _wait_connections(self: GameServer) -> None:
        """Wait for at least one player and then a short join window."""
        while not self.players:
            logger.info("Waiting for player clients")
            sleep(1)

        for second in range(1, self.connection_timeout + 1):
            names = [player.name for player in self.players]
            logger.info(
                "Waiting other players (%s/%s) %s",
                second,
                self.connection_timeout,
                names,
            )
            if len(self.players) == MAX_NB_PLAYERS:
                break
            sleep(1)

        logger.info("Players ready: START!!!")
        self.game.start()
        for player in self.players:
            self.write(player, "START")

    def read(self, client: ClientData) -> str:
        """Read one command line from a client.

        Returns:
            The text command received from the client, or an empty string on timeout.
        """
        try:
            text = client.network.readline()
        except NetworkError:
            logger.exception("timeout for client %s", client.name)
            self.remove_client(client)
            return ""

        logger.debug(text)
        return text

    def write(self, client: ClientData, text: str) -> None:
        """Send one line of text to a client."""
        if not text.endswith("\n"):
            text += "\n"
        logger.debug("sending to %s", client.name)
        try:
            client.network.write(text)
        except (NetworkError, TimeoutError):
            logger.exception("Problem sending state to client")
            self.remove_client(client)

    def _handle_player_command(self, player: ClientData, command: str) -> None:
        """Execute one player command and return result to the player."""
        logger.debug("Command [%s] %s", player.name, command)
        if player.player_id is None:
            logger.warning("Client %s has no player id", player.name)
            self.remove_client(player)
            return
        try:
            self.write(
                player,
                self.game.manage_command(player.player_id, command),
            )
        except BlockedPlayerError as error:
            logger.warning("Blocked player %s", error.name)
            self.remove_client(player)

    def _process_player_inputs(self, start: float) -> None:
        """Process player inputs for one frame window."""
        while perf_counter() - start < FRAME_WINDOW_SECONDS:
            for player in self.players:
                if player.network.input_empty():
                    continue
                command = self.read(player)
                self._handle_player_command(player, command)

    def _should_stop(self) -> bool:
        """Return True when race should stop and log the reason."""
        if (
            self.game.cumulated_time
            > MAX_EXPLORATION_DURATION_SECONDS + MAX_RACE_DURATION_SECONDS
        ):
            logger.info("Reached time limit for the race")
            return True

        if self.game.finished and not self.game.exploration_phase:
            logger.info("A player won the game")
            return True

        return False

    def _update_spectators(self) -> None:
        """Send current game state to spectators."""
        for spectator in self.spectators:
            self.write(spectator, json.dumps(self.game.state()))

    def run(self: GameServer) -> None:
        """Run the game loop until the game ends or time expires."""
        while True:
            start = perf_counter()
            self._process_player_inputs(start)
            self.game.update()
            self._update_spectators()

            if (
                self.game.cumulated_time > MAX_EXPLORATION_DURATION_SECONDS
                and self.game.exploration_phase
            ):
                logger.info("Reached time limit for the exploration")
                self.game.start_race()

            if self._should_stop():
                break
        sys.exit(0)


def main() -> None:
    """Main entrypoint for launching the server."""
    parser = argparse.ArgumentParser(description="Game server.")
    parser.add_argument(
        "-a",
        "--address",
        type=str,
        help="name of server on the network",
        default="localhost",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="location where server listens",
        default=16210,
    )
    parser.add_argument("-f", "--fast", help="fast simulation", action="store_true")
    parser.add_argument(
        "-t",
        "--timeout",
        help="timeout in seconds while waiting other players",
        type=int,
        default=10,
    )

    args = parser.parse_args()

    if args.fast:
        logging.basicConfig(handlers=[logging.NullHandler()])
        with contextlib.redirect_stdout(None), contextlib.redirect_stderr(None):
            GameServer(args.address, args.port, args.timeout).run()
    else:
        log_format = (
            "%(asctime)s [%(levelname)-8s] %(filename)20s(%(lineno)3s):"
            "%(funcName)-20s :: %(message)s"
        )
        formatter = logging.Formatter(
            log_format,
            datefmt="%m/%d/%Y %H:%M:%S",
        )

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(
            "server.log",
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        logger.info("Launching server")
        GameServer(args.address, args.port, args.timeout).run()


if __name__ == "__main__":
    main()
