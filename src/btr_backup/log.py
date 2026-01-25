import logging

logger = logging.getLogger("btr-backup")


def setup_logger(logger: logging.Logger, *, verbosity: int) -> None:
    logger.setLevel(max(logging.WARNING - 10 * verbosity, logging.DEBUG))

    handler = logging.StreamHandler()

    formatter = logging.Formatter(fmt="[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
