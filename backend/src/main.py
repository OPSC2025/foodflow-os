"""
FoodFlow OS - Main FastAPI Application

Entry point for the FoodFlow OS backend API.
"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.contexts.plant_ops import api as plant_ops_api
from src.contexts.fsq.api import router as fsq_router
from src.contexts.planning.api import router as planning_router
from src.contexts.brand.api import router as brand_router
from src.contexts.retail.api import router as retail_router
from src.contexts.identity.api import auth, tenants
from src.ai_orchestrator.api import router as copilot_router
from src.core.config import settings
from src.core.database import close_db, init_db, get_db_session
from src.core.tenancy import set_tenant_in_context
from src.core.security import decode_token
from src.core.errors import (
    DomainException,
    domain_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from src.core.logging import configure_logging, logger, RequestLogger


# Configure logging on startup
configure_logging(
    level="INFO",
    json_format=True,  # Use JSON format for structured logging
)

request_logger = RequestLogger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Handles database initialization and cleanup.
    """
    # Startup
    logger.info("Starting FoodFlow OS API...")
    await init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down FoodFlow OS API...")
    await close_db()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="FoodFlow OS API",
    description="AI-driven operating system for food manufacturing networks",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Register exception handlers (RFC 7807)
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Correlation ID middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """
    Add correlation ID to each request for distributed tracing.
    """
    # Get or generate correlation ID
    correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    # Process request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["x-correlation-id"] = correlation_id
    
    return response


# Request/Response logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    Log all HTTP requests and responses with timing.
    """
    start_time = time.time()
    
    # Extract context
    correlation_id = request.state.correlation_id if hasattr(request.state, "correlation_id") else None
    tenant_id = request.state.tenant_id if hasattr(request.state, "tenant_id") else None
    
    # Log request
    request_logger.log_request(
        method=request.method,
        path=str(request.url.path),
        correlation_id=correlation_id,
        tenant_id=tenant_id,
        query_params=dict(request.query_params) if request.query_params else None,
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log response
    request_logger.log_response(
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        duration_ms=duration_ms,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
    )
    
    return response


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the status of the application and its dependencies.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "version": "0.1.0",
            "environment": settings.ENVIRONMENT,
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns basic information about the API.
    """
    return JSONResponse(
        content={
            "name": "FoodFlow OS API",
            "version": "0.1.0",
            "docs": "/api/docs",
            "health": "/health",
        }
    )


# Tenant isolation middleware
@app.middleware("http")
async def tenant_isolation_middleware(request, call_next):
    """
    Middleware to enforce tenant isolation at the request level.
    
    Extracts tenant information from JWT token and sets it in ContextVar
    for use by database sessions.
    """
    # Skip middleware for public endpoints
    if request.url.path in ["/health", "/", "/api/docs", "/api/redoc", "/api/openapi.json"]:
        return await call_next(request)
    
    tenant_id = None
    tenant_schema = None
    
    # Extract tenant from Authorization header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            # Decode token to get tenant information
            token_payload = decode_token(token)
            tenant_schema = token_payload.tenant_schema
            tenant_id = token_payload.tenant_id
            
            # Store tenant info in request state for convenience
            request.state.tenant_schema = tenant_schema
            request.state.tenant_id = tenant_id
            
        except Exception:
            # Let the route handler deal with invalid tokens
            logger.debug(f"Failed to decode token in tenant middleware")
            pass
    
    # Set tenant context for this request
    set_tenant_in_context(tenant_id, tenant_schema)
    
    try:
        response = await call_next(request)
        return response
    finally:
        # Clean up context (important for connection pooling)
        set_tenant_in_context(None, None)


# Include routers
# Identity & Tenancy
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(tenants.router, prefix="/api/v1", tags=["tenants"])

# AI Copilot - LLM-powered AI assistant for all workspaces
app.include_router(copilot_router, prefix="/api/v1", tags=["Copilot"])

# PlantOps - consolidated router with all endpoints (overview, lines, batches, trials, downtimes, money_leaks, sensors)
app.include_router(plant_ops_api.router, prefix="/api/v1/plant-ops", tags=["PlantOps"])

# FSQ - Food Safety & Quality (lots, suppliers, deviations, CAPAs, documents)
app.include_router(fsq_router)

# Planning - Demand Forecasting, Production Planning, Safety Stocks, Inventory
app.include_router(planning_router)

# Brand - Brands, Products, SKUs, Co-packers, Contracts, Documents
app.include_router(brand_router)

# Retail - Stores, POS, Waste, OSA, Promos
app.include_router(retail_router)


# Exception handlers are now registered at the app level (see above)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
