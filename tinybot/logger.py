import logging
import logging.handlers
import os

from colorlog import ColoredFormatter, StreamHandler as ColoredStreamHandler


def init_logging():
    file_formatter = logging.Formatter(
        fmt="[{asctime}] [{levelname}] [{name}] {message}",
        style="{",
    )
    info_file_handler = logging.handlers.RotatingFileHandler(
        "info.log", maxBytes=5_242_880, encoding="utf-8"
    )
    info_file_handler.setFormatter(file_formatter)
    debug_file_handler = logging.handlers.RotatingFileHandler(
        "debug.log", maxBytes=5_242_880, encoding="utf-8"
    )
    debug_file_handler.setFormatter(file_formatter)

    stdout_formatter = ColoredFormatter(
        fmt="[{asctime}] [{log_color}{levelname}{reset}] [{name}] {message}",
        style="{",
    )
    stdout_handler = ColoredStreamHandler()
    stdout_handler.setFormatter(stdout_formatter)
    info_file_handler.setLevel(logging.INFO)
    if os.getenv("DEBUG_MODE", False) is False:
        stdout_handler.setLevel(logging.INFO)

    logging.basicConfig(
        level=logging.DEBUG,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[stdout_handler, info_file_handler, debug_file_handler],
    )
