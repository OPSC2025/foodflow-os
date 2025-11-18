"""
FoodFlow OS - Main FastAPI Application

Entry point for the FoodFlow OS backend API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.contexts.plant_ops.api import batches, lines, sensors
from src.core.config import settings
from src.core.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Handles database initialization and cleanup.
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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


# Include PlantOps routers
app.include_router(lines.router, prefix="/api/v1/plant-ops")
app.include_router(batches.router, prefix="/api/v1/plant-ops")
app.include_router(sensors.router, prefix="/api/v1/plant-ops")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    
    Logs the error and returns a generic error response.
    """
    import traceback
    
    # Log the error (in production, use proper logging)
    print(f"Unhandled exception: {exc}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error",
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
