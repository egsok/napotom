"""Logging configuration with rotating file handler.

Provides centralized logging setup for the application.
Log files are stored in the AppData directory and rotate at 5MB.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import get_app_data_dir


# Module-level variable to store the log file path
_log_file_path: Optional[Path] = None


def get_log_file_path() -> Optional[Path]:
    """Get the current log file path.
    
    Returns:
        Path to the log file if logging has been set up, None otherwise.
    """
    return _log_file_path


def setup_logging(level: int = logging.DEBUG) -> Path:
    """Set up application logging with rotating file handler.
    
    Creates a log directory in the application data folder and configures
    a rotating file handler that creates new log files when the current
    one exceeds 5MB, keeping up to 3 backup files.
    
    Args:
        level: The logging level to use (default: DEBUG).
        
    Returns:
        Path to the log file.
    """
    global _log_file_path
    
    # Create logs directory in app data folder
    log_dir = get_app_data_dir() / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up log file path
    log_file = log_dir / 'app.log'
    _log_file_path = log_file
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create rotating file handler
    # Rotates at 5MB, keeps 3 backup files
    handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    
    return log_file
