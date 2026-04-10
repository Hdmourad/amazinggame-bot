"""TCP client for Amazinggame server communication."""

import argparse
from socket import AF_INET, SOCK_STREAM, socket

from .data_handler import DEFAULT_TIMEOUT, DataHandler


class Client:
    """Game client wrapper around a socket data handler."""

    def __init__(
        self,
        server_addr: str,
        port: int,
        username: str = "",
        *,
        spectator: bool = True,
    ) -> None:
        """Connect to the server and perform the client handshake.

        Raises:
            ConnectionRefusedError: If server does not acknowledge the handshake.
        """
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((server_addr, port))
        self._data_handler = DataHandler(sock)

        self.username = username
        if spectator:
            self.username = "spectator"

        self.send(f"{int(spectator)}\n")
        self.send(f"{self.username}\n")

        line = self._data_handler.readline()
        if line != "OK":
            message = f"Connection refused by server: {line}"
            raise ConnectionRefusedError(message)

    def send(self, message: str) -> None:
        """Send a text message to the server."""
        self._data_handler.write(message)

    def send_json(self, data: object) -> None:
        """Send a JSON payload to the server."""
        self._data_handler.write_json(data)

    def read_json(self, timeout: int = DEFAULT_TIMEOUT) -> object:
        """Read a JSON payload from the server.

        Returns:
            Decoded JSON payload from the server.
        """
        return self._data_handler.read_json(timeout)

    def readline(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Read one newline-terminated line from the server.

        Returns:
            Received text line without the trailing newline.
        """
        return self._data_handler.readline(timeout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Game client.")
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
    parser.add_argument(
        "-u",
        "--user",
        type=str,
        help="name of the user",
        default="unknown",
        required=True,
    )
    args = parser.parse_args()

    client = Client(args.address, args.port, args.user, spectator=False)
