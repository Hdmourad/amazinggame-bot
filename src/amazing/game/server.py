"""Network game server that coordinates players and spectators."""

import argparse
import contextlib
import json
import logging
import sys
from time import perf_counter, sleep

from amazing.game.constants import (
    MAX_BLOCKED_COUNTER,
    MAX_GAME_DURATION_SECONDS,
    MAX_NB_PLAYERS,
)
from amazing.game.game import Game
from amazing.game.player import BlockedPlayerError
from amazing.network.data_handler import NetworkError
from amazing.network.server import ClientData, Server

server_connection_timeout = 10
FRAME_WINDOW_SECONDS = 0.033
logger = logging.getLogger(__name__)


class GameServer(Server):
    """Host a maze game and synchronize connected clients."""

    def __init__(self: GameServer, host: str, port: int) -> None:
        """Start the server, wait for players, then initialize the game."""
        super().__init__(host, port)
        self.game = Game()
        self._wait_connections()
        for player in self.players:
            self.game.add_player(player.name)

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
        self.clients.remove(client)
        if not client.spectator:
            for player in self.game.players:
                if player.name == client.name:
                    player.blocked_counter = MAX_BLOCKED_COUNTER + 1

    def _wait_connections(self: GameServer) -> None:
        """Wait for at least one player and then a short join window."""
        while not self.players:
            logger.info("Waiting for player clients")
            sleep(1)

        for second in range(1, server_connection_timeout + 1):
            names = [player.name for player in self.players]
            logger.info(
                "Waiting other players (%s/%s) %s",
                second,
                server_connection_timeout,
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
        except NetworkError, TimeoutError:
            logger.exception("Problem sending state to client")
            self.remove_client(client)

    def run(self: GameServer) -> None:
        """Run the game loop until the game ends or time expires."""
        while True:
            start = perf_counter()
            while perf_counter() - start < FRAME_WINDOW_SECONDS:
                # TODO one command per player at a time, until exhausted or 0.0033s
                for player_id, player in enumerate(self.players):
                    if player.network.input_empty():
                        continue
                    command = self.read(player)
                    logger.info("Command [%s] %s", player.name, command)
                    try:
                        self.write(player, self.game.manage_command(player_id, command))
                    except BlockedPlayerError as e:
                        logger.warning("Blocked player %s attempted a command", e.name)
                        self.remove_client(player)
            self.game.update()
            for spectator in self.spectators:
                self.write(spectator, json.dumps(self.game.state()))

            if self.game.cumulated_time > MAX_GAME_DURATION_SECONDS:
                logger.info("Reached time limit for the game")
                break
            if self.game.finished:
                logger.info("A player won the game")
                break
        sys.exit(0)


if __name__ == "__main__":
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
    server_connection_timeout = args.timeout

    if args.fast:
        logging.basicConfig(handlers=[logging.NullHandler()])
        with contextlib.redirect_stdout(None), contextlib.redirect_stderr(None):
            GameServer(args.address, args.port).run()
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
        GameServer(args.address, args.port).run()
