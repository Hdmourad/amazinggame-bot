"""CLI entrypoint for launching the Amazinggame viewer."""

import argparse
import logging

from amazinggame.viewer.constants import constants
from amazinggame.viewer.viewer import Viewer

logger = logging.getLogger(__name__)

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
    "-s",
    "--small-window",
    help="reduce the size of the window for small screens",
    action="store_true",
)
args = parser.parse_args()
logging.basicConfig(
    filename="viewer_small.log" if args.small_window else "viewer.log",
    encoding="utf-8",
    level=logging.INFO,
    format=(
        "%(asctime)s [%(levelname)-8s] %(filename)20s(%(lineno)3s):%(funcName)-20s :: "
        "%(message)s"
    ),
    datefmt="%m/%d/%Y %H:%M:%S",
)
logger.info("Launching viewer")


try:
    constants.resize(small_window=args.small_window)
    Viewer(args.address, args.port)
except Exception:
    logger.exception("uncaught exception")
