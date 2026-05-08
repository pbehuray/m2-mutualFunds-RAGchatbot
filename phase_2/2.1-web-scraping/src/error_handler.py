"""
Error Handler Module
Provides error handling and retry logic for web scraping operations.
"""

import time
import logging
from typing import Callable, Any, Optional, Type
from functools import wraps


class ScrapingError(Exception):
    """Base exception for scraping errors."""
    pass


class HTTPError(ScrapingError):
    """Exception for HTTP-related errors."""
    pass


class ParseError(ScrapingError):
    """Exception for parsing errors."""
    pass


class ValidationError(ScrapingError):
    """Exception for validation errors."""
    pass


class ErrorHandler:
    """Error handler with retry logic and logging."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize error handler.
        
        Args:
            logger: Logger instance (creates default if not provided)
        """
        self.logger = logger or self._get_default_logger()
    
    def _get_default_logger(self) -> logging.Logger:
        """Get default logger."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def retry(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,),
        on_retry: Optional[Callable] = None
    ):
        """
        Decorator for retry logic with exponential backoff.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for backoff delay
            exceptions: Tuple of exceptions to catch
            on_retry: Optional callback function called on retry
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < max_retries:
                            wait_time = backoff_factor ** attempt
                            self.logger.warning(
                                f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                                f"Retrying in {wait_time:.2f} seconds..."
                            )
                            
                            if on_retry:
                                on_retry(attempt + 1, e)
                            
                            time.sleep(wait_time)
                        else:
                            self.logger.error(
                                f"All {max_retries + 1} attempts failed for {func.__name__}: {str(e)}"
                            )
                
                raise last_exception
            
            return wrapper
        return decorator
    
    def handle_scraping_error(
        self,
        error: Exception,
        context: Optional[dict] = None,
        raise_exception: bool = True
    ) -> Optional[ScrapingError]:
        """
        Handle scraping errors with logging.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            raise_exception: Whether to raise the exception after handling
            
        Returns:
            ScrapingError if raise_exception is False, None otherwise
            
        Raises:
            ScrapingError: If raise_exception is True
        """
        context = context or {}
        
        # Log the error
        self.logger.error(
            f"Scraping error occurred: {type(error).__name__}: {str(error)}",
            extra={'context': context}
        )
        
        # Create appropriate scraping error
        if isinstance(error, ScrapingError):
            scraping_error = error
        else:
            scraping_error = ScrapingError(f"Scraping failed: {str(error)}")
        
        if raise_exception:
            raise scraping_error
        
        return scraping_error
    
    def log_success(
        self,
        operation: str,
        context: Optional[dict] = None
    ):
        """
        Log successful operation.
        
        Args:
            operation: Description of the operation
            context: Additional context information
        """
        context = context or {}
        self.logger.info(
            f"Operation successful: {operation}",
            extra={'context': context}
        )


def safe_execute(
    func: Callable,
    error_handler: ErrorHandler,
    default_return: Any = None,
    context: Optional[dict] = None
) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        error_handler: Error handler instance
        default_return: Default return value on error
        context: Additional context information
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func()
    except Exception as e:
        error_handler.handle_scraping_error(e, context, raise_exception=False)
        return default_return


if __name__ == "__main__":
    # Test the error handler
    error_handler = ErrorHandler()
    
    # Test retry decorator
    @error_handler.retry(max_retries=3, backoff_factor=1.0)
    def flaky_function(fail_times: int = 2):
        """Function that fails a specified number of times."""
        flaky_function.attempt_count = getattr(flaky_function, 'attempt_count', 0) + 1
        
        if flaky_function.attempt_count <= fail_times:
            raise ValueError("Intentional failure")
        
        return "Success"
    
    print("Testing retry decorator:")
    result = flaky_function(fail_times=2)
    print(f"Result: {result}")
    
    # Test error handling
    print("\nTesting error handling:")
    try:
        error_handler.handle_scraping_error(
            ValueError("Test error"),
            context={'url': 'https://example.com'},
            raise_exception=True
        )
    except ScrapingError as e:
        print(f"Handled error: {e}")
