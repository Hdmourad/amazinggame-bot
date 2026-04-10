"""Viewer orchestration between network and GUI threads."""

import logging
from threading import Thread
from time import sleep

from amazinggame.network.client import Client
from amazinggame.network.data_handler import NetworkError
from amazinggame.viewer.window import gui_thread, input_queue

logger = logging.getLogger(__name__)


def network_thread(server_addr: str, port: int) -> None:
    """Read game updates from server and push them to the GUI queue."""
    client = Client(server_addr, port, spectator=True)
    while True:
        try:
            data = client.read_json(timeout=3600)
            input_queue.put(data)
        except NetworkError:
            logger.exception("End of network communication")
            break
    for _ in range(6):
        sleep(10)
        logger.info("sleeping")


class Viewer:
    """Launch and coordinate network and graphical viewer components."""

    def __init__(self, server_addr: str, port: int) -> None:
        """Start network listener and GUI loop."""
        logger.info("Start network")
        Thread(target=network_thread, daemon=True, args=[server_addr, port]).start()
        logger.info("Start GUI")
        gui_thread(server_addr, port)
