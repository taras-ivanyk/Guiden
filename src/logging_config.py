"""Application-wide logging setup."""
import logging
import sys
from src.config import LOG_LEVEL


def _setup() -> logging.Logger:
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    return logging.getLogger("cycling_coach")


logger: logging.Logger = _setup()
