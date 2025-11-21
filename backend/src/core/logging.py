"""
Structured logging configuration.

Provides JSON-formatted logging with context enrichment (tenant_id, user_id, correlation_id).
"""

import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs logs as JSON with standard fields:
    - timestamp
    - level
    - logger
    - message
    - correlation_id (if available)
    - tenant_id (if available)
    - user_id (if available)
    - additional fields from extra dict
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation_id if available
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        # Add tenant_id if available
        if hasattr(record, "tenant_id"):
            log_data["tenant_id"] = record.tenant_id
        
        # Add user_id if available
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        # Add any extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def configure_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure application logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, use JSON formatter; otherwise use human-readable
        log_file: Optional file path to write logs to
    """
    # Configure standard library logging
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Configure loguru (if using)
    loguru_logger.remove()  # Remove default handler
    
    if json_format:
        loguru_logger.add(
            sys.stdout,
            format="{message}",
            level=level,
            serialize=True,  # JSON serialization
        )
    else:
        loguru_logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level,
        )


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context (tenant_id, user_id, correlation_id) to logs.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log messages."""
        extra = kwargs.get("extra", {})
        
        # Add context from adapter
        if self.extra:
            extra.update(self.extra)
        
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(
    name: str,
    correlation_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> LoggerAdapter:
    """
    Get a logger with optional context.
    
    Args:
        name: Logger name (typically __name__)
        correlation_id: Request correlation ID
        tenant_id: Tenant ID
        user_id: User ID
        
    Returns:
        LoggerAdapter with context
    """
    base_logger = logging.getLogger(name)
    
    extra = {}
    if correlation_id:
        extra["correlation_id"] = correlation_id
    if tenant_id:
        extra["tenant_id"] = tenant_id
    if user_id:
        extra["user_id"] = user_id
    
    return LoggerAdapter(base_logger, extra)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return str(uuid.uuid4())


# Default logger instance
logger = loguru_logger


# Sensitive fields to redact from logs
SENSITIVE_FIELDS = {
    "password",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "secret",
    "authorization",
    "cookie",
    "ssn",
    "credit_card",
    "cvv",
}


def redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact sensitive fields from data before logging.
    
    Args:
        data: Dictionary potentially containing sensitive data
        
    Returns:
        Dictionary with sensitive fields redacted
    """
    redacted = {}
    
    for key, value in data.items():
        lower_key = key.lower()
        
        # Check if field is sensitive
        if any(sensitive in lower_key for sensitive in SENSITIVE_FIELDS):
            redacted[key] = "***REDACTED***"
        elif isinstance(value, dict):
            # Recursively redact nested dictionaries
            redacted[key] = redact_sensitive_data(value)
        elif isinstance(value, list):
            # Redact items in lists
            redacted[key] = [
                redact_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value
    
    return redacted


class RequestLogger:
    """Logger for HTTP requests with automatic context extraction."""
    
    def __init__(self, logger_name: str = "api"):
        """
        Initialize request logger.
        
        Args:
            logger_name: Name for the logger
        """
        self.logger = logging.getLogger(logger_name)
    
    def log_request(
        self,
        method: str,
        path: str,
        correlation_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log incoming HTTP request.
        
        Args:
            method: HTTP method
            path: Request path
            correlation_id: Correlation ID
            tenant_id: Tenant ID (if available)
            user_id: User ID (if available)
            query_params: Query parameters
        """
        self.logger.info(
            f"Request: {method} {path}",
            extra={
                "event_type": "http_request",
                "method": method,
                "path": path,
                "correlation_id": correlation_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "query_params": redact_sensitive_data(query_params) if query_params else None,
            }
        )
    
    def log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        correlation_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Log HTTP response.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            correlation_id: Correlation ID
            tenant_id: Tenant ID (if available)
            user_id: User ID (if available)
        """
        level = "INFO" if status_code < 400 else "WARNING" if status_code < 500 else "ERROR"
        
        log_method = getattr(self.logger, level.lower())
        log_method(
            f"Response: {method} {path} - {status_code} ({duration_ms:.2f}ms)",
            extra={
                "event_type": "http_response",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "correlation_id": correlation_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
            }
        )

