import logging
import sys
from datetime import datetime
from typing import Dict, Any
import json
import os

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def setup_logging():
    """Configure application logging"""
    
    # Get log level from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Use JSON formatter in production, simple formatter in development
    if os.getenv('ENVIRONMENT') == 'production':
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return root_logger

class LoggerMixin:
    """Mixin class to add logging capabilities"""
    
    @property
    def logger(self):
        if not hasattr(self, '_logger'):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger
    
    def log_request(self, request_id: str, method: str, path: str, user_id: str = None):
        """Log incoming request"""
        extra = {'request_id': request_id}
        if user_id:
            extra['user_id'] = user_id
        
        self.logger.info(f"Request: {method} {path}", extra=extra)
    
    def log_response(self, request_id: str, status_code: int, execution_time: float):
        """Log outgoing response"""
        extra = {
            'request_id': request_id,
            'execution_time': execution_time
        }
        
        if status_code >= 500:
            self.logger.error(f"Response: {status_code}", extra=extra)
        elif status_code >= 400:
            self.logger.warning(f"Response: {status_code}", extra=extra)
        else:
            self.logger.info(f"Response: {status_code}", extra=extra)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        extra = context or {}
        self.logger.error(f"Error: {str(error)}", exc_info=True, extra=extra)
    
    def log_business_event(self, event: str, data: Dict[str, Any] = None):
        """Log business events for analytics"""
        extra = data or {}
        extra['event_type'] = 'business_event'
        self.logger.info(f"Business Event: {event}", extra=extra)

# Performance monitoring decorator
def log_performance(func):
    """Decorator to log function performance"""
    import time
    from functools import wraps
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger(func.__module__)
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"Function {func.__name__} executed successfully",
                extra={'execution_time': execution_time}
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed",
                exc_info=True,
                extra={'execution_time': execution_time}
            )
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger(func.__module__)
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"Function {func.__name__} executed successfully",
                extra={'execution_time': execution_time}
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed",
                exc_info=True,
                extra={'execution_time': execution_time}
            )
            raise
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
