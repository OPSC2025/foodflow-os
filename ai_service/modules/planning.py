"""
Planning AI Module

AI endpoints for planning & supply chain:
- Demand forecasting
- Production planning
- Safety stock recommendations

All endpoints return stub data for now. Real ML models will be integrated later.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter()


# Schemas

class ForecastRequest(BaseModel):
    """Request for demand forecast."""
    tenant_id: UUID
    horizon_weeks: int = Field(..., gt=0, le=52)
    grouping: str = Field(..., description="sku, category, plant")
    sku_ids: Optional[List[str]] = None
    category_ids: Optional[List[str]] = None


class ForecastPoint(BaseModel):
    """Single forecast data point."""
    sku_id: str
    date: datetime
    baseline: float
    p10: float = Field(..., description="10th percentile (pessimistic)")
    p90: float = Field(..., description="90th percentile (optimistic)")


class ForecastResponse(BaseModel):
    """Response for demand forecast."""
    forecast_version_id: UUID
    points: List[ForecastPoint]
    metadata: dict
    model_version: str
    confidence: float


class ProductionPlanRequest(BaseModel):
    """Request for production plan generation."""
    tenant_id: UUID
    forecast_version_id: UUID
    horizon_weeks: int
    plant_ids: List[UUID]
    constraints: Optional[dict] = None


class ProductionScheduleItem(BaseModel):
    """Single production schedule item."""
    plant_id: UUID
    line_id: UUID
    sku_id: str
    date: datetime
    quantity: float
    setup_time_min: int
    runtime_min: int


class ProductionPlanResponse(BaseModel):
    """Response for production plan."""
    plan_id: UUID
    schedule: List[ProductionScheduleItem]
    kpis: dict
    feasibility_score: float
    recommendations: List[str]
    model_version: str
    confidence: float


class SafetyStockRequest(BaseModel):
    """Request for safety stock recommendations."""
    tenant_id: UUID
    sku_ids: List[str]
    location_ids: List[UUID]
    service_level: float = Field(0.95, ge=0.0, le=1.0)


class SafetyStockRecommendation(BaseModel):
    """Safety stock recommendation for SKU-location."""
    sku_id: str
    location_id: UUID
    current_safety_stock: float
    recommended_safety_stock: float
    reasoning: str
    estimated_holding_cost: float


class SafetyStockResponse(BaseModel):
    """Response for safety stock recommendations."""
    recommendations: List[SafetyStockRecommendation]
    total_cost_impact: float
    model_version: str
    confidence: float


# Endpoints

@router.post("/generate-forecast", response_model=ForecastResponse)
async def generate_forecast(request: ForecastRequest) -> ForecastResponse:
    """
    Generate demand forecast.
    
    **Stub Implementation**: Returns realistic mock data.
    
    Future: Will use hierarchical forecasting models (Prophet, LSTM, etc.)
    with demand drivers and seasonality.
    """
    # Generate mock forecast points
    import random
    from datetime import timedelta
    
    base_date = datetime.utcnow()
    points = []
    
    # Generate forecast for 2 SKUs over 12 weeks
    for sku_idx in range(2):
        sku_id = f"SKU-{123 + sku_idx}"
        base_demand = 1000.0 + (sku_idx * 500)
        
        for week in range(min(request.horizon_weeks, 12)):
            date = base_date + timedelta(weeks=week)
            # Add some randomness and trend
            baseline = base_demand + (week * 10) + random.uniform(-50, 50)
            
            points.append(ForecastPoint(
                sku_id=sku_id,
                date=date,
                baseline=round(baseline, 2),
                p10=round(baseline * 0.85, 2),
                p90=round(baseline * 1.15, 2),
            ))
    
    return ForecastResponse(
        forecast_version_id=UUID("12345678-1234-1234-1234-123456789012"),
        points=points,
        metadata={
            "model_type": "hierarchical_prophet",
            "seasonality": "weekly",
            "demand_drivers": ["promotions", "holidays"],
            "generated_at": datetime.utcnow().isoformat(),
        },
        model_version="v1.0-stub",
        confidence=0.78,
    )


@router.post("/generate-production-plan", response_model=ProductionPlanResponse)
async def generate_production_plan(request: ProductionPlanRequest) -> ProductionPlanResponse:
    """
    Generate optimal production plan.
    
    **Stub Implementation**: Returns realistic mock data.
    
    Future: Will use optimization (linear programming, genetic algorithms)
    to create feasible production schedules considering:
    - Demand forecast
    - Capacity constraints
    - Changeover costs
    - Inventory targets
    """
    # Generate mock schedule
    from datetime import timedelta
    import random
    
    base_date = datetime.utcnow()
    schedule = []
    
    # Mock schedule for 1 week
    for day in range(7):
        date = base_date + timedelta(days=day)
        schedule.append(ProductionScheduleItem(
            plant_id=request.plant_ids[0],
            line_id=UUID("11111111-1111-1111-1111-111111111111"),
            sku_id=f"SKU-{123 + (day % 3)}",
            date=date,
            quantity=round(800.0 + random.uniform(-100, 100), 2),
            setup_time_min=45 if day == 0 or day == 3 else 0,
            runtime_min=420,
        ))
    
    return ProductionPlanResponse(
        plan_id=UUID("87654321-4321-4321-4321-210987654321"),
        schedule=schedule,
        kpis={
            "total_production_qty": sum(item.quantity for item in schedule),
            "capacity_utilization": 0.87,
            "changeover_count": 2,
            "total_changeover_time_min": 90,
            "on_time_delivery_score": 0.95,
        },
        feasibility_score=0.92,
        recommendations=[
            "Consider batching SKU-123 on days 0-1 to reduce changeovers",
            "Line 2 has available capacity for overflow if needed",
            "Inventory levels support this plan with 15% safety margin",
        ],
        model_version="v1.0-stub",
        confidence=0.85,
    )


@router.post("/recommend-safety-stocks", response_model=SafetyStockResponse)
async def recommend_safety_stocks(request: SafetyStockRequest) -> SafetyStockResponse:
    """
    Recommend optimal safety stock levels.
    
    **Stub Implementation**: Returns realistic mock data.
    
    Future: Will calculate safety stock using:
    - Demand variability
    - Lead time variability
    - Desired service level
    - Holding costs
    """
    recommendations = []
    
    for sku_id in request.sku_ids[:3]:  # Mock up to 3 SKUs
        for location_id in request.location_ids[:2]:  # Mock up to 2 locations
            current = 500.0
            recommended = 650.0
            
            recommendations.append(SafetyStockRecommendation(
                sku_id=sku_id,
                location_id=location_id,
                current_safety_stock=current,
                recommended_safety_stock=recommended,
                reasoning=f"Demand variability increased 18% vs last quarter. Recommend +{recommended-current:.0f} units to maintain {request.service_level*100:.0f}% service level.",
                estimated_holding_cost=2.50 * (recommended - current),
            ))
    
    total_cost = sum(r.estimated_holding_cost for r in recommendations)
    
    return SafetyStockResponse(
        recommendations=recommendations,
        total_cost_impact=round(total_cost, 2),
        model_version="v1.0-stub",
        confidence=0.81,
    )

