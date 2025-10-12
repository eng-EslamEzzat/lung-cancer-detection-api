"""
Logging configuration for the FastAPI application
"""

import logging
import sys
from typing import Dict, Any
from app.core.config import settings


def setup_logging() -> None:
    """Configure logging for the application"""
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.addHandler(console_handler)
    
    # Configure uvicorn loggers
    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn.access").handlers = []
    
    # Add our handler to uvicorn
    logging.getLogger("uvicorn").addHandler(console_handler)
    logging.getLogger("uvicorn.access").addHandler(console_handler)
    
    # Set levels for specific loggers
    logging.getLogger("uvicorn").setLevel(settings.LOG_LEVEL)
    logging.getLogger("uvicorn.access").setLevel(settings.LOG_LEVEL)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)