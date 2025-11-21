"""
RFC 7807 Problem Details for HTTP APIs error handling.

This module provides standardized error responses following RFC 7807
for consistent API error handling across all endpoints.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ProblemDetail(BaseModel):
    """
    RFC 7807 Problem Detail model.
    
    See: https://tools.ietf.org/html/rfc7807
    """
    
    type: str = "about:blank"
    title: str
    status: int
    detail: Optional[str] = None
    instance: Optional[str] = None
    correlation_id: Optional[str] = None
    errors: Optional[Dict[str, Any]] = None


# Domain Exception Classes

class DomainException(Exception):
    """Base class for domain exceptions."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize domain exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_code: Machine-readable error code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(DomainException):
    """Validation error (400 Bad Request)."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(DomainException):
    """Authentication error (401 Unauthorized)."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationError(DomainException):
    """Authorization error (403 Forbidden)."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
        )


class NotFoundError(DomainException):
    """Resource not found (404 Not Found)."""
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class ConflictError(DomainException):
    """Resource conflict (409 Conflict)."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details,
        )


class BusinessRuleError(DomainException):
    """Business rule violation (422 Unprocessable Entity)."""
    
    def __init__(self, message: str, rule: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="BUSINESS_RULE_VIOLATION",
            details={"rule": rule},
        )


class ExternalServiceError(DomainException):
    """External service error (502 Bad Gateway)."""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"External service '{service}' error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )


class TenantInactiveError(DomainException):
    """Tenant is not active (403 Forbidden)."""
    
    def __init__(self, tenant_id: str):
        super().__init__(
            message="Tenant is not active",
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="TENANT_INACTIVE",
            details={"tenant_id": tenant_id},
        )


# Error Response Builders

def create_problem_detail(
    request: Request,
    status_code: int,
    title: str,
    detail: Optional[str] = None,
    error_type: str = "about:blank",
    errors: Optional[Dict[str, Any]] = None,
) -> ProblemDetail:
    """
    Create an RFC 7807 Problem Detail response.
    
    Args:
        request: FastAPI request object
        status_code: HTTP status code
        title: Short summary of the problem
        detail: Detailed explanation
        error_type: URI reference identifying the problem type
        errors: Additional error details
        
    Returns:
        ProblemDetail instance
    """
    correlation_id = request.state.correlation_id if hasattr(request.state, "correlation_id") else None
    
    return ProblemDetail(
        type=error_type,
        title=title,
        status=status_code,
        detail=detail,
        instance=str(request.url),
        correlation_id=correlation_id,
        errors=errors,
    )


async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    """
    Exception handler for domain exceptions.
    
    Converts domain exceptions to RFC 7807 Problem Detail responses.
    """
    problem = create_problem_detail(
        request=request,
        status_code=exc.status_code,
        title=exc.error_code.replace("_", " ").title(),
        detail=exc.message,
        error_type=f"/errors/{exc.error_code.lower()}",
        errors=exc.details if exc.details else None,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.dict(exclude_none=True),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Exception handler for FastAPI HTTPException.
    
    Converts HTTPException to RFC 7807 Problem Detail responses.
    """
    problem = create_problem_detail(
        request=request,
        status_code=exc.status_code,
        title=HTTPException.__name__,
        detail=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.dict(exclude_none=True),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Exception handler for unexpected exceptions.
    
    Logs the error and returns a generic 500 response without exposing internals.
    """
    import traceback
    from .logging import logger
    
    correlation_id = request.state.correlation_id if hasattr(request.state, "correlation_id") else None
    
    # Log the full error
    logger.error(
        "Unhandled exception",
        extra={
            "correlation_id": correlation_id,
            "path": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        }
    )
    
    # Return generic error to client (don't expose internals)
    problem = create_problem_detail(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error occurred. Please try again later.",
        error_type="/errors/internal_error",
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=problem.dict(exclude_none=True),
    )


# Utility functions for raising common errors

def raise_not_found(resource: str, identifier: Any) -> None:
    """Raise a NotFoundError."""
    raise NotFoundError(resource, identifier)


def raise_validation_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Raise a ValidationError."""
    raise ValidationError(message, details)


def raise_unauthorized(message: str = "Authentication required") -> None:
    """Raise an AuthenticationError."""
    raise AuthenticationError(message)


def raise_forbidden(message: str = "Insufficient permissions") -> None:
    """Raise an AuthorizationError."""
    raise AuthorizationError(message)


def raise_conflict(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Raise a ConflictError."""
    raise ConflictError(message, details)


def raise_business_rule_error(message: str, rule: str) -> None:
    """Raise a BusinessRuleError."""
    raise BusinessRuleError(message, rule)

