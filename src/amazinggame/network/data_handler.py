"""Socket-based line and JSON I/O helpers for network communication."""

from __future__ import annotations

import json
import logging
from contextlib import suppress
from threading import Lock, Thread
from time import perf_counter, sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from socket import socket as socket_type

DEFAULT_TIMEOUT = 20  # seconds
logger = logging.getLogger(__name__)


class NetworkError(Exception):
    """Raised when network I/O times out or connection is broken."""


class DataHandler:
    """Asynchronous buffered socket reader/writer with line and JSON helpers."""

    BUFSIZ = 1024

    def _receive_data(self) -> None:
        while True:
            try:
                data = self.socket.recv(self.BUFSIZ)
            except TimeoutError:
                continue  # same player try again
            except OSError:
                return
            with self._input_lock:
                self._inputbytes += data
                try:
                    self._input += self._inputbytes.decode("utf-8")
                    self._inputbytes = b""
                except UnicodeDecodeError:
                    pass

    def __init__(self, socket_: socket_type) -> None:
        """Initialize handler and start background receive thread."""
        self._inputbytes = b""
        self._input = ""
        self._input_lock = Lock()
        self.socket = socket_
        self.socket.settimeout(0.01)

        receive_thread = Thread(target=self._receive_data, args=(), daemon=True)
        receive_thread.start()

    def input_empty(self) -> bool:
        """Return True when no complete line is currently buffered."""
        return "\n" not in self._input

    def readline(self: DataHandler, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Read one line from the socket within the timeout window.

        Returns:
            The next complete line without trailing newline.

        Raises:
            NetworkError: If no complete line is received before timeout.
        """
        start = perf_counter()
        while "\n" not in self._input:
            if perf_counter() - start > timeout:
                logger.debug("timeout")
                raise NetworkError
            sleep(0.005)
        with self._input_lock:
            index = self._input.index("\n")
            line = self._input[:index]
            self._input = self._input[index + 1 :]
            return line

    def read_json(self: DataHandler, timeout: int = DEFAULT_TIMEOUT) -> object:
        """Read and decode one JSON object within the timeout window.

        Returns:
            Decoded JSON-compatible Python object.

        Raises:
            NetworkError: If no valid JSON payload is received before timeout.
        """
        start = perf_counter()
        logger.debug("read_json")
        json_text = ""
        while True:
            json_text += "\n" + self.readline(timeout)
            with suppress(json.JSONDecodeError):
                return json.loads(json_text)
            if perf_counter() - start > timeout:
                logger.debug("timeout")
                raise NetworkError

    def write(self: DataHandler, message: str) -> None:
        """Send a text message to the socket.

        Raises:
            NetworkError: If the remote side has closed the connection.
        """
        logger.debug("write %s", message[:100])
        try:
            self.socket.send(bytes(message, "utf8"))
        except BrokenPipeError as exc:
            raise NetworkError from exc

    def write_json(self, data: object) -> None:
        """Serialize and send JSON data followed by a newline."""
        self.write(json.dumps(data) + "\n")
