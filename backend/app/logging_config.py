from loguru import logger


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sink="stdout",
        level="INFO",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
    )

