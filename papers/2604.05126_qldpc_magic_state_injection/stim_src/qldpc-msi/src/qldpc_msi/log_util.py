# import logging
import sys

from loguru import logger


def get_logger(log_level="DEBUG", log_file: str | bool | None = None):
    # Remove any existing handlers
    logger.remove()

    # Define the log format
    # log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    # log_format = "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    # log_format = "<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    # log_format = "{name}:{line} - {message}"
    log_format = "{message}"

    # Configure based on the parameters
    if log_file is False:
        # Log to null (disable logging)
        logger.add(lambda _: None)
    elif isinstance(log_file, str):
        # Log to file
        logger.add(log_file, level=log_level, format=log_format, rotation="10 MB")
    elif log_file is None:
        # Log to console (stdout)
        logger.add(sys.stdout, level=log_level, format=log_format, colorize=True)
    else:
        raise ValueError(f"Invalid log_file: {log_file}")

    return logger


# def get_logger(name):
#     return logging.getLogger(name)


# Initialize with default settings (console logging)
# logger = configure_logging()
# logger = get_logger("DEBUG", "logs/debug.log")
logger = get_logger("DEBUG", False)
