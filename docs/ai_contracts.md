# FoodFlow OS - AI Contracts Documentation

## Overview

This document defines all AI service endpoints, their request/response schemas, current stub behavior, and future real implementation plans.

**Current Status**: All endpoints return realistic mock data (stubs).  
**Goal**: Establish stable API contracts so backend, frontend, and Copilot can integrate while ML models are developed in parallel.

---

## PlantOps AI Endpoints

Base URL: `/api/v1/plantops`

### 1. Analyze Scrap

**Endpoint**: `POST /analyze-scrap`  
**Purpose**: Analyze scrap patterns and identify root causes

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "plant_id": "uuid",
  "line_id": "uuid",
  "start_date": "datetime",
  "end_date": "datetime"
}
```

**Response Schema**:
```json
{
  "scrap_analysis": {
    "total_scrap_qty": float,
    "scrap_rate": float,
    "avg_cost_per_unit": float
  },
  "top_reasons": [
    {
      "reason": str,
      "percentage": float,
      "estimated_cost": float
    }
  ],
  "trend": "increasing|decreasing|stable",
  "recommendations": [str],
  "confidence": float (0.0-1.0),
  "model_version": str
}
```

**Current Stub Behavior**: Returns fixed top 3 scrap reasons (temperature, material, equipment) with realistic percentages and costs.

**Future Implementation**: ML model analyzing historical scrap data with pattern recognition, statistical trend analysis, and NLP-based recommendation generation.

**Used By**: 
- PlantOps workspace: Line overview, Scrap analytics page
- Copilot: `analyze_scrap` tool

---

### 2. Suggest Trial

**Endpoint**: `POST /suggest-trial`  
**Purpose**: Suggest optimal production trial parameters

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "line_id": "uuid",
  "sku_id": str,
  "current_parameters": object,
  "optimization_goal": str
}
```

**Response Schema**:
```json
{
  "trial_suggestion": {
    "trial_name": str,
    "duration_minutes": int
  },
  "parameters": {
    "line_speed": float,
    "temperature": float,
    "pressure": float,
    "additional_params": object
  },
  "expected_outcome": str,
  "estimated_impact": object,
  "risks": [str],
  "confidence": float,
  "model_version": str
}
```

**Current Stub Behavior**: Returns fixed parameter suggestions with 12-15% scrap reduction estimate.

**Future Implementation**: Reinforcement learning model trained on historical trial results, using contextual bandits or actor-critic methods to optimize parameters.

**Used By**:
- PlantOps workspace: Line trials feature
- Copilot: `suggest_trial` tool

---

### 3. Compare Batch

**Endpoint**: `POST /compare-batch`  
**Purpose**: Compare batch to similar historical batches

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "batch_id": "uuid"
}
```

**Response Schema**:
```json
{
  "comparison": object,
  "similar_batches": [
    {
      "batch_id": "uuid",
      "batch_number": str,
      "similarity_score": float,
      "key_metrics": object
    }
  ],
  "deviations": [object],
  "insights": [str],
  "confidence": float,
  "model_version": str
}
```

**Current Stub Behavior**: Returns 2 similar batches with mock similarity scores and deviations.

**Future Implementation**: Embedding-based similarity search using batch features (parameters, environment, outcomes). Possible models: autoencoders, transformer embeddings.

**Used By**:
- PlantOps workspace: Batch details page
- Copilot: `compare_batch` tool

---

### 4. Compute Line Efficiency

**Endpoint**: `POST /compute-line-efficiency`  
**Purpose**: Calculate OEE and identify money leaks

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "line_id": "uuid",
  "start_date": "datetime",
  "end_date": "datetime"
}
```

**Response Schema**:
```json
{
  "oee_metrics": object,
  "availability": float,
  "performance": float,
  "quality": float,
  "oee": float,
  "downtime_breakdown": object,
  "money_leaks": [
    {
      "category": str,
      "amount": float,
      "percentage": float,
      "root_causes": [str]
    }
  ],
  "total_cost": float,
  "recommendations": [str],
  "confidence": float,
  "model_version": str
}
```

**Current Stub Behavior**: Returns 79% OEE with breakdown of money leaks across scrap, downtime, speed loss, and startup.

**Future Implementation**: Real-time calculation from sensor data with root cause analysis using decision trees or gradient boosting.

**Used By**:
- PlantOps workspace: Line overview, Money leaks dashboard
- Copilot: `get_line_efficiency` tool

---

## FSQ (Food Safety & Quality) AI Endpoints

Base URL: `/api/v1/fsq`

### 1. Compute Lot Risk

**Endpoint**: `POST /compute-lot-risk`  
**Purpose**: Calculate risk score for production lot

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "lot_id": "uuid"
}
```

**Response Schema**:
```json
{
  "risk_score": float (0.0-1.0),
  "risk_level": "low|medium|high|critical",
  "risk_factors": [
    {
      "factor": str,
      "impact": float,
      "details": str
    }
  ],
  "affected_products": [str],
  "recommended_actions": [str],
  "confidence": float,
  "model_version": str
}
```

**Current Stub Behavior**: Returns 0.35 risk score (medium) with supplier and process deviation factors.

**Future Implementation**: Ensemble model combining supplier history, process deviations, test results, and similar lot outcomes. Possible models: XGBoost, random forest.

**Used By**:
- FSQ workspace: Lot details, Risk dashboard
- Copilot: `compute_lot_risk` tool

---

### 2. Compute Supplier Risk

**Endpoint**: `POST /compute-supplier-risk`  
**Purpose**: Assess supplier risk level

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "supplier_id": "uuid"
}
```

**Response Schema**:
```json
{
  "risk_score": float,
  "risk_level": str,
  "risk_factors": [object],
  "historical_issues": [object],
  "certification_status": object,
  "recommended_actions": [str],
  "confidence": float,
  "model_version": str
}
```

**Current Stub Behavior**: Returns 0.28 risk score with certification and deviation history.

**Future Implementation**: Time-series analysis of supplier performance with certification status, industry benchmarks, and predictive models for future risk.

**Used By**:
- FSQ workspace: Supplier management
- Copilot: `compute_supplier_risk` tool

---

### 3. CCP Drift Summary

**Endpoint**: `POST /ccp-drift-summary`  
**Purpose**: Analyze Critical Control Point drift

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "plant_id": "uuid",
  "start_date": "datetime",
  "end_date": "datetime"
}
```

**Response Schema**:
```json
{
  "ccp_drifts": [
    {
      "ccp_name": str,
      "sensor_id": str,
      "deviation_count": int,
      "severity": str,
      "avg_deviation": float,
      "max_deviation": float,
      "trend": str
    }
  ],
  "total_violations": int,
  "critical_ccps": [str],
  "recommendations": [str],
  "confidence": float,
  "model_version": str
}
```

**Current Stub Behavior**: Returns 3 CCPs with varying drift levels.

**Future Implementation**: Time-series anomaly detection on sensor data using statistical process control or LSTM-based anomaly detection.

**Used By**:
- FSQ workspace: HACCP monitoring
- Copilot: `check_ccp_status` tool

---

### 4. Run Mock Recall

**Endpoint**: `POST /run-mock-recall`  
**Purpose**: Simulate recall scenario for traceability testing

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "scope_type": "lot|ingredient|supplier",
  "scope_id": "uuid"
}
```

**Response Schema**:
```json
{
  "affected_lots": [object],
  "affected_products": [object],
  "affected_locations": [object],
  "estimated_impact": object,
  "recall_path": [object],
  "recommended_steps": [str],
  "confidence": float,
  "model_version": str
}
```

**Current Stub Behavior**: Returns mock recall impacting ~4300 cases across 145 stores with $129K estimated cost.

**Future Implementation**: Graph database traversal (forward/backward tracing) using Neo4j or similar, with impact estimation based on historical data.

**Used By**:
- FSQ workspace: Mock recall simulation
- Copilot: `run_mock_recall` tool

---

### 5. Answer Compliance Question

**Endpoint**: `POST /answer-compliance-question`  
**Purpose**: Answer FSQ/compliance questions using RAG

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "question": str,
  "context": object,
  "doc_ids": [uuid],
  "lot_ids": [uuid]
}
```

**Response Schema**:
```json
{
  "answer": str,
  "confidence": float,
  "sources": [
    {
      "doc_id": "uuid",
      "doc_title": str,
      "section": str,
      "relevance_score": float
    }
  ],
  "rag_available": bool,
  "model_version": str
}
```

**Current Stub Behavior**: Returns message indicating RAG not available. If doc_ids provided, returns mock answer with sources.

**Future Implementation**: RAG (Retrieval-Augmented Generation) using:
- Document chunking and embedding (OpenAI embeddings, sentence-transformers)
- Vector search (pgvector)
- LLM synthesis (GPT-4, Claude)
- Citation tracking

**Used By**:
- FSQ workspace: Document search, Q&A
- Copilot: `answer_compliance_question` tool

---

## Planning AI Endpoints

Base URL: `/api/v1/planning`

### 1. Generate Forecast

**Endpoint**: `POST /generate-forecast`  
**Purpose**: Generate demand forecast

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "horizon_weeks": int,
  "grouping": "sku|category|plant",
  "sku_ids": [str],
  "category_ids": [str]
}
```

**Response Schema**:
```json
{
  "forecast_version_id": "uuid",
  "points": [
    {
      "sku_id": str,
      "date": "datetime",
      "baseline": float,
      "p10": float,
      "p90": float
    }
  ],
  "metadata": object,
  "model_version": str,
  "confidence": float
}
```

**Current Stub Behavior**: Returns 12 weeks of forecast for 2 SKUs with P10/P90 confidence intervals.

**Future Implementation**: Hierarchical forecasting using Prophet, LSTM, or transformer models with seasonality, promotions, and external factors.

**Used By**:
- Planning workspace: Forecast generation
- Copilot: `generate_forecast` tool

---

### 2. Generate Production Plan

**Endpoint**: `POST /generate-production-plan`  
**Purpose**: Generate optimal production schedule

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "forecast_version_id": "uuid",
  "horizon_weeks": int,
  "plant_ids": [uuid],
  "constraints": object
}
```

**Response Schema**:
```json
{
  "plan_id": "uuid",
  "schedule": [
    {
      "plant_id": "uuid",
      "line_id": "uuid",
      "sku_id": str,
      "date": "datetime",
      "quantity": float,
      "setup_time_min": int,
      "runtime_min": int
    }
  ],
  "kpis": object,
  "feasibility_score": float,
  "recommendations": [str],
  "model_version": str,
  "confidence": float
}
```

**Current Stub Behavior**: Returns 1 week schedule with 87% capacity utilization.

**Future Implementation**: Mixed-integer linear programming (MILP) or genetic algorithms for production scheduling optimization.

**Used By**:
- Planning workspace: Production planning
- Copilot: `generate_production_plan` tool

---

### 3. Recommend Safety Stocks

**Endpoint**: `POST /recommend-safety-stocks`  
**Purpose**: Recommend optimal safety stock levels

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "sku_ids": [str],
  "location_ids": [uuid],
  "service_level": float
}
```

**Response Schema**:
```json
{
  "recommendations": [
    {
      "sku_id": str,
      "location_id": "uuid",
      "current_safety_stock": float,
      "recommended_safety_stock": float,
      "reasoning": str,
      "estimated_holding_cost": float
    }
  ],
  "total_cost_impact": float,
  "model_version": str,
  "confidence": float
}
```

**Current Stub Behavior**: Returns recommendations with +30% safety stock increase for higher service level.

**Future Implementation**: Statistical safety stock calculation using demand/lead time variability with inventory optimization.

**Used By**:
- Planning workspace: Inventory optimization
- Copilot: `recommend_safety_stocks` tool

---

## Brand AI Endpoints

Base URL: `/api/v1/brand`

### 1. Compute Margin Bridge

**Endpoint**: `POST /compute-margin-bridge`  
**Purpose**: Analyze margin changes (waterfall analysis)

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "brand_id": "uuid",
  "period1_start": "datetime",
  "period1_end": "datetime",
  "period2_start": "datetime",
  "period2_end": "datetime"
}
```

**Response Schema**:
```json
{
  "period1_margin": float,
  "period2_margin": float,
  "margin_change": float,
  "components": [
    {
      "component": str,
      "change": float,
      "percentage": float,
      "details": str
    }
  ],
  "recommendations": [str],
  "model_version": str,
  "confidence": float
}
```

**Current Stub Behavior**: Returns margin decline of -2.3% driven by raw materials (65%) and labor (22%).

**Future Implementation**: Decomposition analysis of cost components with variance analysis and driver identification.

**Used By**:
- Brand workspace: Margin analysis
- Copilot: `compute_margin_bridge` tool

---

### 2. Compute Co-packer Risk

**Endpoint**: `POST /compute-copacker-risk`  
**Purpose**: Evaluate co-packer risk

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "copacker_id": "uuid"
}
```

**Response Schema**:
```json
{
  "risk_score": float,
  "risk_level": str,
  "risk_factors": [object],
  "performance_metrics": object,
  "recommendations": [str],
  "model_version": str,
  "confidence": float
}
```

**Current Stub Behavior**: Returns 0.32 risk score with quality and capacity concerns.

**Future Implementation**: Multi-factor risk model analyzing quality, capacity, financial stability, and market conditions.

**Used By**:
- Brand workspace: Co-packer management
- Copilot: `evaluate_copacker` tool

---

### 3. Answer Brand Question

**Endpoint**: `POST /answer-brand-question`  
**Purpose**: Answer brand/product questions using RAG

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "brand_id": "uuid",
  "question": str,
  "context": object
}
```

**Response Schema**:
```json
{
  "answer": str,
  "confidence": float,
  "sources": [object],
  "rag_available": bool,
  "model_version": str
}
```

**Current Stub Behavior**: Returns message indicating RAG not available.

**Future Implementation**: RAG over brand documents (contracts, specs, marketing materials) similar to FSQ compliance Q&A.

**Used By**:
- Brand workspace: Document search
- Copilot: `answer_brand_question` tool

---

## Retail AI Endpoints

Base URL: `/api/v1/retail`

### 1. Forecast Retail Demand

**Endpoint**: `POST /forecast-retail-demand`  
**Purpose**: Store-level demand forecast

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "banner_id": "uuid",
  "store_ids": [uuid],
  "sku_ids": [str],
  "horizon_weeks": int
}
```

**Response Schema**:
```json
{
  "points": [
    {
      "store_id": "uuid",
      "sku_id": str,
      "date": "datetime",
      "forecast": float,
      "confidence_interval": [float, float]
    }
  ],
  "model_version": str,
  "confidence": float
}
```

**Current Stub Behavior**: Returns 4 weeks of forecasts for 2 stores × 2 SKUs.

**Future Implementation**: Store-level models with local factors (traffic, weather, promotions, events).

**Used By**:
- Retail workspace: Demand planning
- Copilot: `forecast_retail_demand` tool

---

### 2. Recommend Replenishment

**Endpoint**: `POST /recommend-replenishment`  
**Purpose**: Generate replenishment orders

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "banner_id": "uuid",
  "store_ids": [uuid],
  "sku_ids": [str]
}
```

**Response Schema**:
```json
{
  "recommendations": [
    {
      "store_id": "uuid",
      "sku_id": str,
      "current_inventory": float,
      "recommended_order_qty": float,
      "urgency": str,
      "reasoning": str
    }
  ],
  "total_order_value": float,
  "model_version": str,
  "confidence": float
}
```

**Current Stub Behavior**: Returns 2 replenishment recommendations with urgency levels.

**Future Implementation**: Inventory optimization considering forecast, current stock, lead times, and order constraints.

**Used By**:
- Retail workspace: Replenishment
- Copilot: `recommend_replenishment` tool

---

### 3. Detect OSA Issues

**Endpoint**: `POST /detect-osa-issues`  
**Purpose**: Detect on-shelf availability issues

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "category_id": str,
  "banner_id": "uuid",
  "min_severity": str
}
```

**Response Schema**:
```json
{
  "issues": [
    {
      "store_id": "uuid",
      "sku_id": str,
      "issue_type": str,
      "severity": str,
      "estimated_lost_sales": float,
      "recommended_action": str
    }
  ],
  "total_estimated_lost_sales": float,
  "model_version": str,
  "confidence": float
}
```

**Current Stub Behavior**: Returns 2 OSA issues (stockout and low shelf presence) with $630 total lost sales.

**Future Implementation**: Anomaly detection on POS/inventory data with lost sales estimation and action recommendations.

**Used By**:
- Retail workspace: OSA monitoring
- Copilot: `detect_osa_issues` tool

---

### 4. Evaluate Promo

**Endpoint**: `POST /evaluate-promo`  
**Purpose**: Evaluate promotion effectiveness

**Request Schema**:
```json
{
  "tenant_id": "uuid",
  "promo_id": "uuid"
}
```

**Response Schema**:
```json
{
  "promo_id": "uuid",
  "lift": float,
  "roi": float,
  "cannibalization": object,
  "halo_effect": object,
  "recommendations": [str],
  "model_version": str,
  "confidence": float
}
```

**Current Stub Behavior**: Returns 1.42x lift with 2.85 ROI.

**Future Implementation**: Causal inference models (difference-in-differences, synthetic control) to measure true incremental impact.

**Used By**:
- Retail workspace: Promotion analysis
- Copilot: `evaluate_promo` tool

---

## Implementation Notes

### Current Status (All Endpoints)
- **Status**: Stub implementations returning realistic mock data
- **Purpose**: Establish stable API contracts for integration
- **Timeline**: Stubs active immediately; real ML models phased in over next 3-6 months

### RAG-Ready Endpoints
The following endpoints are designed for RAG (Retrieval-Augmented Generation) but gracefully degrade when RAG is not available:
- `POST /fsq/answer-compliance-question`
- `POST /brand/answer-brand-question`

These endpoints will be activated once document indexing pipeline is implemented.

### Testing
All endpoints have:
- OpenAPI documentation auto-generated
- Request/response validation via Pydantic
- Mock responses in test fixtures (`backend/tests/conftest.py`)

### Monitoring
Once real ML models are deployed:
- Track confidence scores over time
- Monitor response latencies
- Log all predictions for A/B testing and model retraining
- Integrate with AI telemetry service for ROI tracking

---

## Integration Examples

### Backend Integration
```python
from src.core.ai_client import AIServiceClient

client = AIServiceClient()
result = await client.analyze_scrap(
    tenant_id=tenant_id,
    plant_id=plant_id,
    line_id=line_id,
    start_date=start_date,
    end_date=end_date,
)
```

### Copilot Integration
```python
@tool("analyze_scrap")
async def analyze_scrap_tool(line_id: str, date_range: str):
    """Analyze scrap patterns for a production line."""
    result = await ai_client.analyze_scrap(...)
    return result
```

### Frontend Integration (via Copilot)
```typescript
// Don't call AI service directly from UI
// Instead, use Copilot with specific prompt:
await copilotService.ask({
  workspace: "plantops",
  message: "Diagnose the scrap spike on Line 3",
  context: { line_id: "123", date_range: "last_7_days" }
});
```

---

**Last Updated**: 2024-11-21  
**Version**: v1.0 (Stub Phase)  
**Next Review**: When first real ML model is deployed

