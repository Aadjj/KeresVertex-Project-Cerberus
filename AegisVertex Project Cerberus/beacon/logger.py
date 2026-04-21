import logging
import sys
from config import settings


def setup_logger():
    logger = logging.getLogger('Keres.Implant')

    level = logging.DEBUG if getattr(settings, 'DEBUG', False) else logging.WARNING
    logger.setLevel(level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


logger = setup_logger()