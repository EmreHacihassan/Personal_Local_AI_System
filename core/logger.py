"""
Enterprise AI Assistant - Logging Module
Merkezi loglama sistemi

Endüstri standardı logging implementasyonu.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from core.config import settings


class LoggerSetup:
    """Logger kurulum ve yönetim sınıfı."""
    
    _initialized = False
    _loggers: dict = {}
    
    @classmethod
    def setup(cls, name: str = "enterprise_ai") -> logging.Logger:
        """
        Logger oluştur ve yapılandır.
        
        Args:
            name: Logger adı
            
        Returns:
            Yapılandırılmış logger
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = settings.LOGS_DIR / f"{name}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Error file handler
        error_file = settings.LOGS_DIR / f"{name}_error.log"
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        cls._loggers[name] = logger
        cls._initialized = True
        
        return logger
    
    @classmethod
    def get_logger(cls, name: str = "enterprise_ai") -> logging.Logger:
        """
        Logger al veya oluştur.
        
        Args:
            name: Logger adı
            
        Returns:
            Logger instance
        """
        if name not in cls._loggers:
            return cls.setup(name)
        return cls._loggers[name]


def get_logger(name: str = "enterprise_ai") -> logging.Logger:
    """
    Logger al - kısayol fonksiyon.
    
    Args:
        name: Logger adı
        
    Returns:
        Logger instance
    """
    return LoggerSetup.get_logger(name)


# Ana logger instance
logger = get_logger()


# Convenience functions
def log_info(message: str, logger_name: str = "enterprise_ai") -> None:
    """INFO seviyesinde log."""
    get_logger(logger_name).info(message)


def log_error(message: str, logger_name: str = "enterprise_ai", exc_info: bool = False) -> None:
    """ERROR seviyesinde log."""
    get_logger(logger_name).error(message, exc_info=exc_info)


def log_warning(message: str, logger_name: str = "enterprise_ai") -> None:
    """WARNING seviyesinde log."""
    get_logger(logger_name).warning(message)


def log_debug(message: str, logger_name: str = "enterprise_ai") -> None:
    """DEBUG seviyesinde log."""
    get_logger(logger_name).debug(message)


def log_agent_action(agent_name: str, action: str, details: str = "") -> None:
    """Agent eylemini logla."""
    message = f"[{agent_name}] {action}"
    if details:
        message += f" | {details}"
    log_info(message, "agents")


def log_rag_operation(operation: str, query: str = "", results: int = 0) -> None:
    """RAG işlemini logla."""
    message = f"[RAG] {operation}"
    if query:
        message += f" | Query: {query[:50]}..."
    if results:
        message += f" | Results: {results}"
    log_info(message, "rag")


def log_api_request(method: str, endpoint: str, status: int, duration_ms: float) -> None:
    """API isteğini logla."""
    message = f"[API] {method} {endpoint} | Status: {status} | Duration: {duration_ms:.2f}ms"
    log_info(message, "api")
