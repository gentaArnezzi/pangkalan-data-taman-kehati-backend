import logging
from logging import Logger

_DEFAULT_FORMAT = "[%(asctime)s] %(levelname)s %(name)s | %(message)s"

def get_logger(name: str = "app", level: int = logging.INFO) -> Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(_DEFAULT_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger
