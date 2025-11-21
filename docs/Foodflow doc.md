/*
------------------------------------------------------------------------------
FoodFlow OS – Master Functional & System Specification (Version 1.0)
------------------------------------------------------------------------------

0. DOCUMENT PURPOSE

This spec defines the full FoodFlow OS system for food product companies,
emphasizing LLM/AI-native workflows throughout every module.

------------------------------------------------------------------------------

1. PRODUCT GOALS & SCOPE

**Core Goal:**
Build an AI-native OS for food companies (manufacturers, co-packers, brands, retailers) to:
  - Reduce margin leakage (waste, scrap, rework, overstock/stockout)
  - Lower FSQ & recall risk, simplify audits
  - Align demand, production, deployment
  - Provide each persona an AI Copilot (data visibility, forecasting, optimization, suggestions)

**Workspaces:**
  1. PlantOps – plant & line operations (batches, scrap, yield)
  2. FSQ & Traceability – HACCP, CCP, deviations, recalls, lots
  3. Planning & Supply – forecasting, planning, deployment
  4. Brand & Co-packer – brand performance, co-packers, allocation
  5. Retail – store POS, waste, OSA, replenishment

------------------------------------------------------------------------------

2. SYSTEM ARCHITECTURE

**Services:**
  - backend/api-server (Python FastAPI; modular monolith, domain APIs, `/api/copilot`)
  - ai_service (Python FastAPI or BentoML; forecasting, anomaly, optimization, FSQ, retail, vision)
  - edge_gateway (Python async; connects to PLCs/sensors, normalizes data)
  - frontend (React SPA; workspace UIs, Copilot panel)

**Data Stores:**
  - PostgreSQL (schema-per-tenant)
  - TimescaleDB (timeseries in Postgres)
  - pgvector (embedding search for RAG)
  - Object Store (S3/MinIO for docs/images)
  - Optionals: GraphDB, Analytical Warehouse, Model Registry

**Multi-tenancy:**
  - `tenant_id` resolved per request (JWT/header), DB search path set per request

------------------------------------------------------------------------------

3. LLM/COPILOT ("BRAIN")

**Copilot Entry API:**
  POST `/api/copilot`
  Request: {
    workspace, message, context (tenant_id, user_id, role, plant_id, etc.)
  }
  Response: {
    answer (markdown), links, actions, usage_metadata (tokens)
  }

**Key Flow:**
  1. Build system prompt per workspace
  2. Pass user/tenant metadata
  3. Register available Copilot tools
  4. Use LangChain (or equiv) for LLM tool-calling
  5. Log all interactions/feedback

**RAG:**
  - pgvector-empowered doc retrieval for contracts/audit/FSQ/brand

------------------------------------------------------------------------------

4. AI CONTRACTS (KEY PYTHON INTERFACES)

[Wrapped in ai_service, called via Copilot & domain modules]

**Forecasting & Optimization:**
  - forecast_demand(tenant_id, horizon_weeks, grouping)
  - forecast_line_behavior(tenant_id, plant_id, line_id, sku_id, horizon_hours)
  - optimize_production_plan(tenant_id, forecast_version_id, horizon, constraints)
  - recommend_safety_stocks(tenant_id, sku_ids, location_ids)
  - optimize_allocation(tenant_id, skus, periods, entities, constraints)

**Anomaly Detection:**
  - detect_line_anomalies(tenant_id, plant_id, line_id, date_range)
  - detect_ccp_drift(tenant_id, plant_id, date_range)

**FSQ Risk & Trace:**
  - compute_lot_risk(tenant_id, lot_id)
  - compute_supplier_risk(tenant_id, supplier_id)
  - ccp_drift_summary(tenant_id, plant_id, date_range)
  - run_mock_recall(tenant_id, scope)

**PlantOps:**
  - analyze_line_scrap(tenant_id, plant_id, line_id, date_range)
  - suggest_line_trial(tenant_id, plant_id, line_id, sku_id, context)
  - compare_batch(tenant_id, batch_id)

**Planning & Supply:**
  - generate_forecast(tenant_id, horizon_weeks, grouping)
  - generate_production_plan(tenant_id, forecast_version_id, horizon_buckets, plants, options)
  - recommend_safety_stocks(tenant_id, sku_ids, location_ids)

**Brand & Copacker:**
  - compute_copacker_risk(tenant_id, copacker_id)
  - compute_margin_bridge(tenant_id, brand_id, period1, period2)
  - optimize_volume_allocation(tenant_id, skus, periods, entities, constraints)
  - rank_npi_sites(tenant_id, project_id)

**Retail:**
  - forecast_retail_demand(tenant_id, banner_id, skus, store_ids, horizon_days)
  - recommend_retail_replenishment(tenant_id, banner_id, store_ids, sku_ids, horizon_days)
  - detect_osa_issues(tenant_id, category_id, filters)
  - evaluate_promo(tenant_id, promo_id)

------------------------------------------------------------------------------

5. AI TELEMETRY & FEEDBACK

All Copilot/AI suggestions logged to:
  - copilot_interactions (tenant_id, user_id, workspace, question, answer, tools_used, timestamp)
  - ai_suggestions (suggestion_id, type, payload, created_at)
  - ai_suggestion_outcomes (suggestion_id, applied_flag, applied_by, applied_at, before/after metrics)
  - ai_feedback (thumbs, comments)
Purpose: Model quality tracking, ROI justification, future training set.

------------------------------------------------------------------------------

6. WORKSPACE BEHAVIOR SUMMARIES

**PlantOps:**
  - KPIs (output, scrap %, OEE), money leaks, anomaly highlighting, trials/experiments
  - Copilot: analyze_line_scrap, suggest_line_trial, compare_batch

**FSQ & Trace:**
  - Deviations, CAPA lifecycle, HACCP CRUD, CCP logging, lot genealogy, recall wizard
  - Copilot: compute_lot_risk, compute_supplier_risk, ccp_drift_summary, run_mock_recall

**Planning & Supply:**
  - Forecast grid/versioning, production plan vs. capacity, safety stock, plans
  - Copilot: generate_forecast, generate_production_plan, recommend_safety_stocks

**Brand & Co-packer:**
  - Margin/sales, co-packer SLAs, margin bridge, allocation, NPI site ranking
  - Copilot: compute_margin_bridge, compute_copacker_risk, optimize_volume_allocation, rank_npi_sites

**Retail:**
  - Category/store/SKU KPIs, waste, OSA issues, promo calendar, replenishments
  - Copilot: recommend_replenishment, detect_osa_issues, evaluate_promo

------------------------------------------------------------------------------

7. INTEGRATIONS

Stub connectors for MVP:
  - ERP (SKUs, BOMs, work orders, inventory)
  - MES/SCADA (via edge or API/file for batches, production, sensors)
  - WMS/TMS (DC inventory, shipments)
  - LIMS/QMS (FSQ results, incidents)
  - POS (store-level sales, waste)

Provide admin UI and field mapping for each.

------------------------------------------------------------------------------

8. IMPLEMENTATION PHASING

**Phase 1:** Core infra, PlantOps & FSQ, Copilot API, stub AI
**Phase 2:** Real AI (forecast/scenario), Planning module, expand Copilot tools
**Phase 3:** Brand & Retail, co-packer models, POS & replenishment, more Copilot flows
**Phase 4:** OR-Tools optimization, Graph DB, feedback loops

------------------------------------------------------------------------------

HAND THIS SPEC TO THE DEV TEAM OR CURSOR – IT PROVIDES THE FULL SYSTEM BLUEPRINT.
For detailed contracts/fields/examples, see above per module & interface.
------------------------------------------------------------------------------
*/
