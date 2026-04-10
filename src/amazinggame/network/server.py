"""TCP server for handling game client connections."""

import argparse
import logging
from contextlib import suppress
from dataclasses import dataclass
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
from typing import NoReturn

from .data_handler import DataHandler

logger = logging.getLogger(__name__)


@dataclass
class ClientData:
    """Runtime information for a connected client."""

    spectator: bool
    name: str
    network: DataHandler
    player_id: int | None = None

    def __eq__(self: ClientData, other: object) -> bool:
        """Compare two clients by their underlying network handler identity.

        Returns:
            True when both instances wrap the same network handler.
        """
        if isinstance(other, ClientData):
            return self.network is other.network
        raise NotImplementedError

    def __hash__(self: ClientData) -> int:
        """Hash client data from the underlying network handler identity.

        Returns:
            Stable hash derived from the network handler object identity.
        """
        return id(self.network)


class Server:
    """Accept and track incoming clients for the game server."""

    def __init__(self: Server, host: str, port: int) -> None:
        """Start server accept loop in a background thread."""
        self.clients: list[ClientData] = []
        logger.info("Waiting for connection...")
        accept_thread = Thread(
            target=self.accept_incoming_connections, args=(host, port), daemon=True
        )
        accept_thread.start()

    def accept_incoming_connections(self: Server, host: str, port: int) -> NoReturn:
        """Set up handling for incoming clients.

        Args:
            host (str): server host name
            port (int): server port
        """
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind((host, port))
        sock.listen(5)

        while True:
            with suppress(OSError):
                client_socket, _ = sock.accept()
                Thread(
                    target=self.handle_client_connection, args=(client_socket,)
                ).start()

        sock.close()

    def handle_client_connection(self, client_socket: socket) -> None:
        """Handle a single client socket connection.

        Args:
            client_socket (socket): socket of the client to handle
        """
        logger.info("Connection of a new client")
        data_handler = DataHandler(client_socket)
        spectator = data_handler.readline().strip() == "1"
        logger.info(" - Spectator %s", spectator)
        name = data_handler.readline().strip()
        logger.info(" - Name %s", name)
        client = ClientData(spectator=spectator, name=name, network=data_handler)
        self.clients.append(client)
        client.network.write("OK\n")
        logger.info("Current clients: %s", self.clients)
        logger.info(" - New client connected %s", client)


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
        "-p", "--port", type=int, help="location where server listens", default=16210
    )
    args = parser.parse_args()

    Server(args.address, args.port)
