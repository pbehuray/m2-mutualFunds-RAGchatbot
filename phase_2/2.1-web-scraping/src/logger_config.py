"""
Logger Configuration Module
Configures logging for the web scraping infrastructure.
"""

import logging
import os
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """Logger configuration for web scraping operations."""
    
    def __init__(
        self,
        log_level: str = 'INFO',
        log_dir: Optional[str] = None,
        log_to_file: bool = True,
        log_to_console: bool = True
    ):
        """
        Initialize logger configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (default: current directory)
            log_to_file: Whether to log to file
            log_to_console: Whether to log to console
        """
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = log_dir or os.path.join(os.getcwd(), 'logs')
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        
        # Create log directory if it doesn't exist
        if self.log_to_file and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def get_logger(
        self,
        name: str,
        log_file: Optional[str] = None
    ) -> logging.Logger:
        """
        Get configured logger.
        
        Args:
            name: Logger name
            log_file: Specific log file name (default: auto-generated)
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add file handler
        if self.log_to_file:
            if log_file is None:
                log_file = f"scraping_{datetime.now().strftime('%Y%m%d')}.log"
            
            log_path = os.path.join(self.log_dir, log_file)
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Add console handler
        if self.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def setup_scraping_logger(self) -> logging.Logger:
        """
        Set up logger specifically for scraping operations.
        
        Returns:
            Configured logger for scraping
        """
        return self.get_logger('scraping', log_file='scraping.log')
    
    def setup_error_logger(self) -> logging.Logger:
        """
        Set up logger specifically for errors.
        
        Returns:
            Configured logger for errors
        """
        return self.get_logger('scraping_errors', log_file='errors.log')


# Singleton instance
_default_config = None


def get_logger(
    name: str = 'scraping',
    log_level: str = 'INFO',
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    Get logger with default configuration.
    
    Args:
        name: Logger name
        log_level: Logging level
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    global _default_config
    
    if _default_config is None:
        _default_config = LoggerConfig(log_level=log_level, log_dir=log_dir)
    
    return _default_config.get_logger(name)


if __name__ == "__main__":
    # Test the logger configuration
    logger_config = LoggerConfig(log_level='INFO')
    
    # Get loggers
    scraping_logger = logger_config.setup_scraping_logger()
    error_logger = logger_config.setup_error_logger()
    
    # Test logging
    scraping_logger.info("This is an info message")
    scraping_logger.warning("This is a warning message")
    scraping_logger.error("This is an error message")
    
    error_logger.error("This is an error in the error log")
    
    print("Logger configuration test completed")
    print(f"Logs directory: {logger_config.log_dir}")
