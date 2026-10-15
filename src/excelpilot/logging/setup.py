"""Logging configuration for ExcelPilot."""

import logging
import sys
from typing import Final

DEFAULT_LOG_FORMAT: Final[str] = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def configure_logging(verbose: bool = False) -> logging.Logger:
    """Configure structured logging for technical diagnostics without polluting CLI output.

    Technical logs go to stderr while human-facing Rich CLI output goes to stdout.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logger = logging.getLogger("excelpilot")
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
