"""
FoodFlow OS AI Service - Main Application

Provides AI capabilities for all workspaces:
- PlantOps: Scrap analysis, trial suggestions, batch comparison
- FSQ: Lot risk, supplier risk, CCP monitoring, compliance Q&A
- Planning: Demand forecasting, production planning, safety stock
- Brand: Margin analysis, co-packer evaluation
- Retail: Demand forecasting, replenishment, OSA detection

All endpoints return stub/mock data initially. Real ML models will be
swapped in later without changing the API contracts.
"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import AI module routers
from modules.plantops import router as plantops_router
from modules.fsq import router as fsq_router
from modules.planning import router as planning_router
from modules.brand import router as brand_router
from modules.retail import router as retail_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🤖 Starting FoodFlow AI Service...")
    yield
    # Shutdown
    print("👋 Shutting down FoodFlow AI Service...")


# Create FastAPI application
app = FastAPI(
    title="FoodFlow AI Service",
    description="AI/ML endpoints for FoodFlow OS",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# Tenant isolation middleware
@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    """
    Extract tenant information from requests.
    
    Tenant ID can come from:
    - x-tenant-id header
    - JWT token (decoded by caller)
    """
    tenant_id = request.headers.get("x-tenant-id")
    if tenant_id:
        request.state.tenant_id = tenant_id
    
    response = await call_next(request)
    return response


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests with timing."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000
    print(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)")
    
    return response


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "FoodFlow AI Service",
        "version": "0.1.0",
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information."""
    return {
        "name": "FoodFlow AI Service",
        "version": "0.1.0",
        "description": "AI/ML endpoints for FoodFlow OS",
        "docs_url": "/api/docs",
        "modules": ["plantops", "fsq", "planning", "brand", "retail"],
        "note": "All endpoints return stub data. Real ML models will be integrated later.",
    }


# Include module routers
app.include_router(plantops_router, prefix="/api/v1/plantops", tags=["PlantOps AI"])
app.include_router(fsq_router, prefix="/api/v1/fsq", tags=["FSQ AI"])
app.include_router(planning_router, prefix="/api/v1/planning", tags=["Planning AI"])
app.include_router(brand_router, prefix="/api/v1/brand", tags=["Brand AI"])
app.include_router(retail_router, prefix="/api/v1/retail", tags=["Retail AI"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )

