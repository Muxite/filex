"""
Logging configuration for the FileX module.
"""
import logging
import sys
from typing import Optional, Any


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    :param name: Logger name (typically __name__)
    :returns: Configured logger instance
    """
    return logging.getLogger(name)


def configure_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    stream: Optional[Any] = sys.stdout
) -> None:
    """
    Configure root logging for the application.
    
    :param level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :param format_string: Custom format string for log messages
    :param stream: Output stream for logs (defaults to stdout)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=log_level,
        format=format_string,
        stream=stream,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
