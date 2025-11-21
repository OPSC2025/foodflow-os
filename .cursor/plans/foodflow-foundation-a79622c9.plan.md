<!-- a79622c9-5229-4c78-9f58-8bb089c2edc0 c47194e8-44f9-4049-ab28-421fc276dcbf -->
# FoodFlow OS: Foundation Implementation Plan

## Overview

Build the complete infrastructure foundation for FoodFlow OS following the answers to key questions:

- **Foundation First**: Complete all infrastructure before feature work (2-4 weeks)
- **DDD Contexts**: Expand existing `contexts/` structure (not refactor to modules)
- **AI Stubs First**: Implement all AI service endpoints with contracts, defer ML
- **Multi-Tenancy**: Complete schema-per-tenant with dynamic switching
- **Copilot-First UI**: All smart actions go through Copilot, not direct AI service calls

## Phase 1: Core Infrastructure Completion (Week 1)

### 1.1 Multi-Tenancy Foundation

**Files**: `backend/src/core/tenancy.py`, `backend/src/contexts/identity/domain/models.py`

Complete the tenant provisioning and isolation system building on existing security middleware:

- Create `Tenant` model (name, slug, schema_name, settings, is_active)
- Implement tenant provisioning service (create schema, run migrations, seed data)
- Complete tenant middleware to set `search_path` from JWT token
- Add tenant admin endpoints (create, activate, deactivate, configure)
- Create Alembic migration for tenant tables

### 1.2 Authentication & Authorization Context

**Files**: `backend/src/contexts/identity/`, expand existing structure

Complete the Identity bounded context:

- Add `User` model with tenant_id, roles, permissions
- Add `Role` and `Permission` models
- Implement registration, login, logout, refresh token endpoints
- Add password reset and email verification flows
- Create RBAC helper functions for route protection

### 1.3 Database Migrations & Seeding

**Files**: `backend/alembic/versions/`, `backend/scripts/seed_dev_data.py`

- Create initial migration for all base tables (tenants, users, roles, permissions)
- Create migration for PlantOps tables (expand existing models)
- Create migration for AI telemetry tables (CopilotInteraction, AI_Suggestion, AI_Feedback)
- Create seed script for development data:
                                                                - 2 demo tenants with schemas (one for Akron facility)
                                                                - Sample users (admin, operator, fsq_manager)
                                                                - Sample plants, lines, batches for Akron
                                                                - Sample FSQ data (lots, deviations)
- Add `scripts/reset_dev_db.sh` for clean dev environment

### 1.4 Core API Structure & Error Handling

**Files**: `backend/src/core/errors.py`, `backend/src/core/responses.py`

Establish consistent API patterns:

- Create error taxonomy (domain errors, validation, auth, not found, conflict)
- Implement RFC 7807 Problem Details format
- Create standard response wrappers
- Add correlation IDs for distributed tracing
- Implement structured logging with tenant_id context

### 1.5 AI Telemetry Foundation (Early)

**Files**: `backend/src/core/telemetry/`, `backend/src/core/telemetry/models.py`

**CRITICAL**: Implement AI telemetry as part of foundation, not later add-on.

Create telemetry models and service:

- **CopilotInteraction** model:
                                                                - tenant_id, user_id, workspace, question, answer
                                                                - tools_used (JSON array), tokens_used, duration_ms
                                                                - feedback_score, feedback_comment
                                                                - created_at, metadata (JSON)
- **AI_Suggestion** model:
                                                                - tenant_id, user_id, suggestion_type, payload (JSON)
                                                                - applied_flag, applied_at, applied_by
                                                                - before_metrics (JSON), after_metrics (JSON)
                                                                - created_at
- **AI_Feedback** model:
                                                                - interaction_id, thumbs_up/down, comment, created_at
- **TelemetryService** class:
                                                                - `log_interaction()` - log Copilot interactions
                                                                - `log_suggestion()` - log AI suggestions
                                                                - `record_feedback()` - capture user feedback
                                                                - `get_workspace_analytics()` - analytics per workspace
                                                                - `get_acceptance_rate()` - suggestion acceptance metrics

**Why now**: This data is GOLD for tuning prompts, measuring ROI, and convincing investors/auditors.

### 1.6 Testing Framework Setup

**Files**: `backend/tests/`, `backend/pytest.ini`, `backend/.coveragerc`

- Configure pytest with async support
- Create test database setup (use testcontainers or separate DB)
- Add fixtures for:
                                                                - Test client with authentication
                                                                - Sample tenants and users
                                                                - Sample domain data (plants, lines, batches, lots)
                                                                - Mock AI service responses
- Create base test classes for:
                                                                - Unit tests (service layer)
                                                                - Integration tests (API endpoints)
                                                                - Repository tests (database access)
- Set coverage target: 80% for services, 70% overall

## Phase 2: AI Service Architecture (Week 1-2)

### 2.1 AI Service Foundation

**Files**: `ai_service/app.py`, `ai_service/config.py`, `ai_service/core/`

Create the AI service skeleton:

- FastAPI application with CORS, health check, metrics
- Configuration management (LLM provider, model versions, API keys)
- Tenant isolation middleware (verify tenant from API key or JWT)
- Request/response logging and telemetry
- Error handling consistent with backend

### 2.2 AI Contracts - PlantOps Module

**Files**: `ai_service/modules/plantops/`, `ai_service/schemas/plantops.py`

Implement PlantOps AI endpoints as stubs:

- `POST /plantops/analyze-scrap` - analyze line scrap patterns
                                                                - Request: tenant_id, plant_id, line_id, date_range
                                                                - Response: scrap_analysis (top_reasons, trend, recommendations)
- `POST /plantops/suggest-trial` - suggest line trial parameters
                                                                - Request: tenant_id, line_id, sku_id, context
                                                                - Response: trial_suggestion (parameters, expected_outcome, risks)
- `POST /plantops/compare-batch` - compare batch to historical
                                                                - Request: tenant_id, batch_id
                                                                - Response: comparison (similar_batches, deviations, insights)
- `POST /plantops/compute-line-efficiency` - calculate OEE and money leaks
                                                                - Request: tenant_id, line_id, date_range
                                                                - Response: oee_metrics, downtime_breakdown, money_leaks

All return realistic mock data with proper schemas.

### 2.3 AI Contracts - FSQ Module

**Files**: `ai_service/modules/fsq/`, `ai_service/schemas/fsq.py`

Implement FSQ AI endpoints as stubs:

- `POST /fsq/compute-lot-risk` - calculate lot risk score
                                                                - Request: tenant_id, lot_id
                                                                - Response: risk_score, risk_factors, affected_products
- `POST /fsq/compute-supplier-risk` - calculate supplier risk
                                                                - Request: tenant_id, supplier_id
                                                                - Response: risk_score, risk_factors, history
- `POST /fsq/ccp-drift-summary` - summarize CCP drift
                                                                - Request: tenant_id, plant_id, date_range
                                                                - Response: ccp_drifts (sensor, deviation_count, severity)
- `POST /fsq/run-mock-recall` - simulate recall scenario
                                                                - Request: tenant_id, scope (lot_id, ingredient_id, supplier_id)
                                                                - Response: affected_products, affected_locations, estimated_impact
- `POST /fsq/answer-compliance-question` - answer FSQ/compliance questions
                                                                - Request: tenant_id, question, context (doc_ids, lot_ids)
                                                                - Response: answer, confidence, sources (doc references)
                                                                - **Note**: Designed for RAG - stub returns generic answer now

### 2.4 AI Contracts - Planning Module

**Files**: `ai_service/modules/planning/`, `ai_service/schemas/planning.py`

Implement Planning AI endpoints as stubs:

- `POST /planning/generate-forecast` - generate demand forecast
                                                                - Request: tenant_id, horizon_weeks, grouping (sku, category, plant)
                                                                - Response: forecast_version_id, points (sku, date, baseline, p10, p90)
- `POST /planning/generate-production-plan` - generate production plan
                                                                - Request: tenant_id, forecast_version_id, horizon, plants, constraints
                                                                - Response: plan_id, schedule (plant, line, sku, date, quantity)
- `POST /planning/recommend-safety-stocks` - recommend safety stock levels
                                                                - Request: tenant_id, sku_ids, location_ids
                                                                - Response: recommendations (sku, location, safety_stock, reasoning)

### 2.5 AI Contracts - Brand & Retail Modules

**Files**: `ai_service/modules/brand/`, `ai_service/modules/retail/`

Implement Brand AI endpoints:

- `POST /brand/compute-margin-bridge` - margin waterfall analysis
- `POST /brand/compute-copacker-risk` - co-packer risk assessment
- `POST /brand/optimize-allocation` - optimize volume allocation
- `POST /brand/rank-npi-sites` - rank sites for new product intro
- `POST /brand/answer-brand-question` - answer brand/product questions
                                                                - **Note**: Designed for RAG over brand docs, contracts

Implement Retail AI endpoints:

- `POST /retail/forecast-retail-demand` - store-level demand forecast
- `POST /retail/recommend-replenishment` - replenishment recommendations
- `POST /retail/detect-osa-issues` - detect out-of-stock/availability issues
- `POST /retail/evaluate-promo` - evaluate promotion effectiveness

### 2.6 AI Contracts Documentation

**Files**: `docs/ai_contracts.md`

**CRITICAL**: Document all AI contracts explicitly.

For each AI endpoint, document:

- Endpoint path and HTTP method
- Request schema (with example JSON)
- Response schema (with example JSON)
- Current stub behavior (what mock data is returned)
- Future real behavior (what ML model/logic will power it)
- Workspace(s) that use it
- Related Copilot tools

This ensures consistency and serves as contract for frontend/backend integration.

### 2.7 AI Service Client Library

**Files**: `backend/src/core/ai_client.py`

Create HTTP client for backend to call AI service:

- Async httpx client with connection pooling
- Automatic tenant context injection
- Retry logic with exponential backoff
- Circuit breaker pattern for resilience
- Request/response logging
- Type-safe wrappers for each AI endpoint
- **Telemetry integration**: log all AI service calls to telemetry DB

## Phase 3: Domain Contexts Implementation (Week 2)

### 3.0 PlantOps Context (EXPLICIT - First Priority)

**Files**: `backend/src/contexts/plant_ops/`

**CRITICAL**: PlantOps is THE most immediate value for Akron facility.

Complete the PlantOps bounded context (expand existing work):

- **Models**: Plant, Line, Batch, ScrapLog, Trial, Downtime, MoneyLeak
- **Schemas**: Pydantic models for all entities
- **Services**: 
                                                                - Plant & line management
                                                                - Batch lifecycle (create, start, complete)
                                                                - Scrap logging and analysis
                                                                - Trial execution and tracking
                                                                - Money leak calculation (scrap cost, downtime cost, yield loss)
                                                                - Line efficiency metrics (OEE, availability, performance, quality)
- **API**: REST endpoints for PlantOps operations
- **Events**: BatchStartedEvent, BatchCompletedEvent, ScrapDetectedEvent, TrialCompletedEvent

Key endpoints:

- `GET /api/v1/plant-ops/overview` - workspace overview (KPIs, money leaks, alerts)
- `GET /api/v1/plant-ops/plants` - list plants
- `POST /api/v1/plant-ops/plants` - create plant
- `GET /api/v1/plant-ops/lines` - list lines (with current status)
- `POST /api/v1/plant-ops/lines` - create line
- `GET /api/v1/plant-ops/lines/{id}` - get line details with real-time metrics
- `POST /api/v1/plant-ops/batches` - create batch
- `GET /api/v1/plant-ops/batches` - list batches (with filters)
- `GET /api/v1/plant-ops/batches/{id}` - get batch details
- `PUT /api/v1/plant-ops/batches/{id}/start` - start batch
- `PUT /api/v1/plant-ops/batches/{id}/complete` - complete batch
- `POST /api/v1/plant-ops/scrap` - log scrap event
- `GET /api/v1/plant-ops/scrap` - list scrap events (with analytics)
- `POST /api/v1/plant-ops/trials` - create trial
- `GET /api/v1/plant-ops/trials` - list trials
- `PUT /api/v1/plant-ops/trials/{id}/complete` - complete trial with results
- `GET /api/v1/plant-ops/money-leaks` - get money leaks by category

**Integration with AI**:

- Line overview should call `compute-line-efficiency` for AI-enhanced metrics
- Scrap analytics should integrate with `analyze-scrap` AI endpoint

### 3.1 FSQ & Traceability Context

**Files**: `backend/src/contexts/fsq/`

Implement the FSQ bounded context:

- **Models**: Lot, Deviation, CAPA, HACCP_Plan, CCP_Log, Supplier, Ingredient, Document
- **Schemas**: Pydantic models for requests/responses
- **Services**: 
                                                                - Lot management and traceability
                                                                - Deviation reporting and CAPA lifecycle
                                                                - CCP monitoring
                                                                - Supplier management
                                                                - **Document ingestion pipeline** (prepare for RAG)
- **API**: REST endpoints for FSQ operations
- **Events**: DeviationCreatedEvent, CAPACompletedEvent, CCPViolationEvent, DocumentUploadedEvent

Key endpoints:

- `POST /api/v1/fsq/lots` - create lot
- `GET /api/v1/fsq/lots/{id}/trace/forward` - forward trace
- `GET /api/v1/fsq/lots/{id}/trace/backward` - backward trace
- `POST /api/v1/fsq/deviations` - report deviation
- `GET /api/v1/fsq/deviations` - list deviations with filters
- `POST /api/v1/fsq/capa` - create CAPA
- `PUT /api/v1/fsq/capa/{id}/close` - close CAPA
- `POST /api/v1/fsq/suppliers` - create supplier
- `GET /api/v1/fsq/suppliers` - list suppliers
- **`POST /api/v1/fsq/documents/upload`** - upload FSQ document (QAI/QMS/SQF)
                                                                - Stores document metadata in DB
                                                                - Uploads file to object storage (S3/MinIO)
                                                                - Queues for future RAG indexing (stub for now)
- `GET /api/v1/fsq/documents` - list documents

**RAG Hook Points**:

- Document upload endpoint ready for future embedding generation
- FSQ Copilot prompts assume RAG will be available but gracefully degrade
- Document model has fields: title, type, content_hash, indexed_at (nullable)

### 3.2 Planning & Supply Context

**Files**: `backend/src/contexts/planning/`

Implement the Planning bounded context:

- **Models**: Forecast, ForecastVersion, ProductionPlan, SafetyStock, InventoryLevel
- **Schemas**: Pydantic models for forecasts and plans
- **Services**: Forecast versioning, plan approval workflow, safety stock recommendations
- **API**: REST endpoints for planning operations
- **Events**: ForecastGeneratedEvent, PlanApprovedEvent, PlanExecutedEvent

Key endpoints:

- `POST /api/v1/planning/forecasts` - generate forecast (calls AI service)
- `GET /api/v1/planning/forecasts` - list forecast versions
- `GET /api/v1/planning/forecasts/{id}` - get forecast details
- `POST /api/v1/planning/plans` - generate production plan (calls AI service)
- `GET /api/v1/planning/plans` - list plans
- `PUT /api/v1/planning/plans/{id}/approve` - approve plan
- `GET /api/v1/planning/safety-stocks` - get safety stock recommendations

### 3.3 Brand & Co-packer Context

**Files**: `backend/src/contexts/brand/`

Implement the Brand bounded context:

- **Models**: Brand, Product, SKU, Copacker, CopackerContract, BrandPerformance, BrandDocument
- **Schemas**: Pydantic models for brand data
- **Services**: 
                                                                - Brand and product management
                                                                - Co-packer evaluation
                                                                - Margin analysis
                                                                - **Document ingestion for brand contracts** (prepare for RAG)
- **API**: REST endpoints for brand operations
- **Events**: ProductLaunchedEvent, CopackerRatedEvent, ContractUploadedEvent

Key endpoints:

- `POST /api/v1/brand/brands` - create brand
- `GET /api/v1/brand/brands` - list brands
- `POST /api/v1/brand/copackers` - create co-packer
- `GET /api/v1/brand/copackers/{id}/performance` - co-packer performance
- `POST /api/v1/brand/margin-bridge` - margin analysis (calls AI service)
- **`POST /api/v1/brand/documents/upload`** - upload brand document (contracts, specs)
                                                                - Similar to FSQ document upload
                                                                - Queued for future RAG indexing
- `GET /api/v1/brand/documents` - list brand documents

**RAG Hook Points**:

- Brand Copilot prompts designed for contract/spec lookup via RAG
- Graceful degradation if RAG not yet indexed

### 3.4 Retail Context

**Files**: `backend/src/contexts/retail/`

Implement the Retail bounded context:

- **Models**: Store, Banner, Category, POSTransaction, Waste, OSAEvent, Promo
- **Schemas**: Pydantic models for retail data
- **Services**: Store performance, waste tracking, OSA monitoring, promo evaluation
- **API**: REST endpoints for retail operations
- **Events**: WasteRecordedEvent, OSAIssueDetectedEvent, PromoStartedEvent

Key endpoints:

- `POST /api/v1/retail/stores` - create store
- `GET /api/v1/retail/stores` - list stores
- `POST /api/v1/retail/pos-transactions` - record POS data (bulk)
- `POST /api/v1/retail/waste` - record waste
- `GET /api/v1/retail/osa-issues` - get OSA issues (calls AI service)
- `POST /api/v1/retail/promos` - create promo
- `GET /api/v1/retail/promos/{id}/evaluate` - evaluate promo (calls AI service)

## Phase 4: AI Copilot Orchestration (Week 2-3)

### 4.1 Copilot Endpoint & Tool Registry

**Files**: `backend/src/ai_orchestrator/api.py`, `backend/src/ai_orchestrator/tools/`

Implement the Copilot orchestration layer:

- `POST /api/v1/copilot` endpoint accepting workspace, message, context
- Tool registry mapping AI contracts to callable functions
- System prompt builder per workspace (with RAG assumptions)
- LLM integration (OpenAI GPT-4) with tool calling
- Conversation history storage (PostgreSQL)
- **Telemetry integration**: every Copilot call logged to telemetry DB
- Feedback collection endpoint: `POST /api/v1/copilot/feedback`

**Copilot-First UI Rule** (document in code comments and developer docs):

> **RULE**: Any UI "smart button" (Diagnose, Analyze, Optimize, Recommend, Explain)

> MUST call `/api/v1/copilot`, NOT the AI service directly.

>

> Examples:

> - "Diagnose scrap on this line" → Copilot with workspace="plantops", message="Diagnose scrap spike", context={line_id, date_range}

> - "Generate production plan" → Copilot with workspace="planning", message="Generate plan", context={forecast_version_id, plants}

> - "Trace this lot" → Copilot with workspace="fsq", message="Trace lot", context={lot_id, direction="backward"}

>

> The Copilot orchestrator will:

> 1. Understand the intent

> 2. Call appropriate tools (domain APIs, AI service)

> 3. Synthesize results into natural language

> 4. Log everything for telemetry

> 5. Return actionable response with links

### 4.2 Workspace-Specific Tools

**Files**: `backend/src/ai_orchestrator/tools/{plantops,fsq,planning,brand,retail}_tools.py`

Create tool definitions for each workspace:

**PlantOps tools**:

- `get_line_status(line_id)` - get current line status and metrics
- `get_batch_details(batch_id)` - get batch details
- `analyze_scrap(plant_id, line_id, date_range)` - calls AI service
- `suggest_trial(line_id, sku_id, context)` - calls AI service
- `compare_batch(batch_id)` - calls AI service
- `get_money_leaks(plant_id, date_range)` - get money leaks breakdown

**FSQ tools**:

- `get_lot_details(lot_id)` - get lot information
- `trace_lot_forward(lot_id)` - forward traceability
- `trace_lot_backward(lot_id)` - backward traceability
- `compute_lot_risk(lot_id)` - calls AI service
- `compute_supplier_risk(supplier_id)` - calls AI service
- `check_ccp_status(plant_id)` - get CCP monitoring status
- `answer_compliance_question(question, context)` - calls AI service (RAG-ready)

**Planning tools**:

- `get_forecast(forecast_version_id)` - get forecast data
- `get_production_plans()` - list production plans
- `generate_forecast(horizon_weeks, grouping)` - calls AI service
- `generate_production_plan(forecast_id, horizon, plants, constraints)` - calls AI service
- `recommend_safety_stocks(sku_ids, location_ids)` - calls AI service

**Brand tools**:

- `get_brand_performance(brand_id, period)` - get brand metrics
- `get_copacker_performance(copacker_id)` - get co-packer metrics
- `compute_margin_bridge(brand_id, period1, period2)` - calls AI service
- `evaluate_copacker(copacker_id)` - calls AI service
- `answer_brand_question(question, context)` - calls AI service (RAG-ready)

**Retail tools**:

- `get_store_performance(store_id, period)` - get store metrics
- `forecast_retail_demand(banner_id, store_ids, sku_ids, horizon)` - calls AI service
- `recommend_replenishment(banner_id, store_ids, sku_ids)` - calls AI service
- `detect_osa_issues(category_id, filters)` - calls AI service
- `evaluate_promo(promo_id)` - calls AI service

Each tool:

- Has JSON schema for parameters
- Validates inputs
- Calls appropriate domain service or AI service
- Logs call to telemetry
- Returns structured results for LLM

### 4.3 RAG Foundation (Stub with Hook Points)

**Files**: `backend/src/ai_orchestrator/rag/`

Create RAG infrastructure (initially stubbed, designed for future activation):

- **Document ingestion service**:
                                                                - Endpoint: `POST /api/v1/rag/ingest` (internal, called by document upload handlers)
                                                                - Receives: document_id, tenant_id, content, metadata
                                                                - Stub behavior: logs document, returns success
                                                                - Future: chunk document, generate embeddings, store in pgvector
- **Semantic search service**:
                                                                - Endpoint: `POST /api/v1/rag/search` (internal, called by Copilot tools)
                                                                - Receives: tenant_id, query, context, top_k
                                                                - Stub behavior: returns empty results
                                                                - Future: embed query, vector search, return relevant chunks with sources
- **pgvector schema**:
                                                                - Table: `document_embeddings` (tenant_id, document_id, chunk_index, embedding, content, metadata)
                                                                - Indexes created but not populated
- **Document chunking logic** (commented, not executed):
                                                                - Chunk size, overlap, splitting strategy documented
                                                                - Embedding model specified (text-embedding-3-small)

**FSQ & Brand RAG Integration**:

- FSQ document upload → queues for RAG ingestion (stub)
- Brand document upload → queues for RAG ingestion (stub)
- FSQ Copilot prompts include: "Use RAG to search FSQ documents if available"
- Brand Copilot prompts include: "Use RAG to search contracts if available"
- Graceful degradation: if search returns empty, Copilot says "I don't have direct access to that document yet"

### 4.4 AI Telemetry Service (Full Implementation)

**Files**: `backend/src/core/telemetry/service.py`

**CRITICAL**: Full implementation, not stub.

Implement telemetry service with rich APIs:

- `log_copilot_interaction(tenant_id, user_id, workspace, question, answer, tools_used, tokens, duration)` - log every Copilot call
- `log_ai_suggestion(tenant_id, user_id, suggestion_type, payload)` - log AI suggestions
- `record_suggestion_outcome(suggestion_id, applied_flag, applied_by, before_metrics, after_metrics)` - record if suggestion was applied and results
- `record_feedback(interaction_id, thumbs_up_down, comment)` - capture user feedback
- `get_workspace_analytics(tenant_id, workspace, date_range)` - get analytics per workspace
                                                                - Total interactions, avg response time, tools usage distribution
- `get_suggestion_acceptance_rate(tenant_id, suggestion_type, date_range)` - acceptance rate metrics
- `get_tool_usage_stats(tenant_id, date_range)` - which tools are most used
- `get_user_engagement(tenant_id, date_range)` - which users engage with Copilot most

**Why this matters**:

- Show investors: "Copilot suggested 47 actions, 38 were accepted, saved $XX,XXX"
- Tune prompts based on real usage patterns
- Identify which tools are valuable vs. ignored
- Build training datasets for future fine-tuning

## Phase 5: CI/CD & DevOps (Week 3)

### 5.1 GitHub Actions Workflows

**Files**: `.github/workflows/`

Create CI/CD pipelines:

- `ci-backend.yml` - Backend linting, type checking, tests
                                                                - Run on PR to main
                                                                - Ruff linting, mypy type checking
                                                                - pytest with coverage report (fail if <70%)
                                                                - Build Docker image
- `ci-ai-service.yml` - AI service linting and tests
                                                                - Same pattern as backend
- `cd-staging.yml` - Deploy to staging on merge to main
                                                                - Build and push Docker images
                                                                - Deploy to K8s staging namespace
                                                                - Run smoke tests
- `cd-production.yml` - Deploy to production on tag
                                                                - Manual approval step
                                                                - Deploy to K8s production namespace

### 5.2 Pre-commit Hooks

**Files**: `.pre-commit-config.yaml`, `backend/.pre-commit-config.yaml`

Configure pre-commit hooks:

- Ruff for Python linting and formatting
- mypy for type checking
- trailing whitespace removal
- YAML validation
- Prevent commits to main branch

### 5.3 Docker & Docker Compose

**Files**: `backend/Dockerfile`, `ai_service/Dockerfile`, `docker-compose.yml` (update)

Create production-ready Dockerfiles:

- Multi-stage builds for smaller images
- Non-root user for security
- Health checks
- Environment variable configuration
- Update docker-compose.yml with backend and ai_service

### 5.4 Kubernetes Manifests (Basic)

**Files**: `infra/k8s/`

Create basic Kubernetes manifests:

- Namespace: foodflow-os
- Deployments: backend, ai-service
- Services: backend-service, ai-service-service
- ConfigMaps: app-config
- Secrets: app-secrets (template)
- Ingress: api-gateway (Kong or NGINX)

## Phase 6: Documentation & Standards (Week 3-4)

### 6.1 Architecture Decision Records

**Files**: `docs/adr/`

Document key decisions:

- ADR-001: Schema-per-tenant multi-tenancy
- ADR-002: DDD bounded contexts structure
- ADR-003: AI service stub-first approach
- ADR-004: Copilot-first UI pattern (all smart actions through Copilot)
- ADR-005: Transactional outbox for events
- ADR-006: JWT-based authentication
- ADR-007: AI telemetry as foundation requirement
- ADR-008: RAG hook points for FSQ & Brand documents

### 6.2 Developer Documentation

**Files**: `docs/developers/`

Create developer guides:

- `SETUP.md` - Local development setup
- `TESTING.md` - Testing strategy and guidelines
- `CONTRIBUTING.md` - How to contribute code
- `API_CONVENTIONS.md` - API design standards
- `CONTEXT_GUIDE.md` - Guide to bounded contexts (PlantOps, FSQ, Planning, Brand, Retail)
- **`COPILOT_FIRST_PATTERN.md`** - Explains Copilot-first UI rule with examples

### 6.3 AI Contracts Documentation

**Files**: `docs/ai_contracts.md`

Complete AI contracts documentation (as specified in Phase 2.6):

- All AI endpoints documented with request/response schemas
- Examples for each endpoint
- Current stub behavior vs. future real behavior
- Workspace mappings

### 6.4 API Documentation

**Files**: `docs/api/`, OpenAPI specs in code

Generate OpenAPI documentation:

- Use FastAPI's automatic OpenAPI generation
- Add detailed descriptions and examples to endpoints
- Create Postman collection from OpenAPI spec
- Host docs at `/api/docs` (Swagger UI)

### 6.5 README Updates

**Files**: `README.md`, `backend/README.md`, `ai_service/README.md`

Update root README with:

- Project overview and architecture decisions
- **Copilot-first value proposition**
- Quick start guide
- Links to detailed documentation
- Technology stack summary
- License and contribution guidelines

### 6.6 Implementation Guide

**Files**: `IMPLEMENTATION_GUIDE.md`

Create prioritized execution guide:

- **P0 (Critical Path)**: Multi-tenancy, Auth, PlantOps context, AI stubs, Copilot endpoint, Telemetry
- **P1 (Important)**: FSQ context, Testing framework, CI/CD, Documentation
- **P2 (Nice to Have)**: Planning/Brand/Retail contexts, K8s manifests, Advanced RAG prep

This helps developers know what to focus on first.

## Implementation Notes

### Priorities

1. **Week 1**: Multi-tenancy, auth, AI telemetry, database migrations, testing framework, AI service foundation
2. **Week 2**: PlantOps context (PRIORITY), FSQ context, AI client, Copilot orchestration
3. **Week 3**: Planning/Brand/Retail contexts, CI/CD, RAG hook points
4. **Week 4**: Documentation, polish, end-to-end testing, telemetry dashboards

### PlantOps as Day 1 Priority

**PlantOps + FSQ + AI is your immediate competitive advantage for Akron:**

- Real-time line monitoring with AI-enhanced metrics
- Scrap analysis and money leak tracking
- Lot traceability and deviation management
- Copilot as the intelligent interface

Make sure PlantOps is complete and polished before spreading effort to Planning/Brand/Retail.

### Copilot-First UI Pattern

**Document this rule everywhere**:

- In developer docs
- In ADR-004
- In code comments at Copilot endpoint
- In frontend integration guide

**The pattern**:

```
User clicks "Diagnose scrap spike" button
  ↓
Frontend calls: POST /api/v1/copilot
  {
    workspace: "plantops",
    message: "Diagnose the scrap spike on Line 3",
    context: {line_id: 123, date_range: "last_7_days"}
  }
  ↓
Copilot orchestrator:
  1. Parses intent
  2. Calls tools: analyze_scrap(123, last_7_days)
  3. Tool calls AI service: POST /plantops/analyze-scrap
  4. Synthesizes response with explanation
  5. Logs to telemetry
  ↓
Returns: {
  answer: "The scrap spike is primarily due to...",
  actions: [{label: "View details", link: "/plant-ops/scrap?line=123"}],
  metadata: {tools_used: ["analyze_scrap"], tokens: 850}
}
```

### AI Telemetry as Success Metric

Track these metrics from day 1:

- Total Copilot interactions per workspace
- Tool usage distribution (which tools are valuable?)
- Suggestion acceptance rate (how often users apply AI suggestions?)
- User engagement (which users use Copilot most?)
- Response quality (thumbs up/down feedback)

Use this data to:

- Tune prompts and system messages
- Decide which AI endpoints to prioritize for real ML
- Demonstrate ROI to investors ("saved $X via AI suggestions")
- Build training datasets for future fine-tuning

### RAG Graceful Degradation

FSQ and Brand Copilot prompts should be written like:

```
You are the FSQ Copilot. You help answer food safety and quality questions.

If the user asks about specific procedures, policies, or specifications:
1. Try to search the document database using the RAG search tool
2. If RAG returns results, cite the source document and quote relevant sections
3. If RAG returns no results, respond: "I don't have direct access to that document yet. 
   I recommend checking [document location] or uploading it to the system."
```

This way:

- Current stubs work gracefully
- Future RAG integration requires no prompt redesign
- Users understand what the system can and can't do

### Testing Strategy

- Write tests alongside implementation (not after)
- Aim for 80% coverage on services, 70% overall
- Integration tests for all API endpoints
- Repository tests for complex queries
- Mock AI service responses in backend tests
- Test telemetry logging (verify interactions are recorded)

### Database Strategy

- Use Alembic for all schema changes
- Never modify existing migrations
- Test migrations with sample data
- Document migration dependencies
- Support rollback for all migrations

### Error Handling Pattern

- Domain errors raise custom exceptions
- Middleware catches and converts to HTTP responses
- All errors logged with correlation ID
- Client receives RFC 7807 Problem Details
- Sensitive data never exposed in errors

### Logging Pattern

- Structured JSON logging in production
- Include: timestamp, level, logger, message, tenant_id, user_id, correlation_id
- Log at appropriate levels: DEBUG (dev only), INFO (key events), WARN (recoverable), ERROR (needs attention)
- No PII in logs (redact email, phone, etc.)

## Success Criteria

Foundation is complete when:

- ✅ Multi-tenancy fully working (tenant provisioning, schema isolation, JWT)
- ✅ AI telemetry operational (all interactions logged, analytics queryable)
- ✅ PlantOps context complete with full CRUD APIs and AI integration
- ✅ FSQ context complete with traceability and document upload hooks
- ✅ All AI service contracts implemented as stubs with realistic responses
- ✅ Copilot endpoint operational with tool calling to domain and AI services
- ✅ Copilot-first UI pattern documented and enforced
- ✅ RAG hook points in place for FSQ & Brand (ready for future activation)
- ✅ CI/CD pipeline running (linting, tests, Docker builds)
- ✅ Test coverage ≥70% overall, ≥80% for services
- ✅ Documentation complete (README, API docs, developer guides, AI contracts, ADRs)
- ✅ End-to-end flow works: Create tenant → Register user → PlantOps API → AI stub → Copilot → Telemetry logged

**Demo-ready milestone**:

- Akron facility tenant with real plant/line data
- Operator can log in, view lines, record scrap
- FSQ manager can create lots, trace backward/forward
- Both can ask Copilot questions and get intelligent responses
- All interactions visible in telemetry dashboard

At this point, the foundation is "locked" and feature development can proceed at velocity.

### To-dos

- [ ] Implement tenant provisioning with schema-per-tenant isolation
- [ ] Complete Identity context with User, Role, Permission models and RBAC
- [ ] PRIORITY: Create AI telemetry models and service as foundation requirement
- [ ] Create Alembic migrations for tenants, users, PlantOps, AI telemetry tables
- [ ] Create seed script with Akron facility demo tenant and sample data
- [ ] Implement RFC 7807 error handling and structured logging
- [ ] Set up pytest with fixtures, test DB, coverage targets, and mock AI responses
- [ ] Create AI service FastAPI skeleton with tenant isolation
- [ ] Implement PlantOps AI endpoints as stubs (analyze-scrap, suggest-trial, compare-batch, compute-efficiency)
- [ ] Implement FSQ AI endpoints as stubs (lot-risk, supplier-risk, ccp-drift, mock-recall, compliance-qa)
- [ ] Implement Planning AI endpoints as stubs with schemas
- [ ] Implement Brand and Retail AI endpoints as stubs
- [ ] CRITICAL: Document all AI contracts with request/response schemas in docs/ai_contracts.md
- [ ] Create backend AI service client with retry, circuit breaker, and telemetry
- [ ] PRIORITY: Complete PlantOps context with full CRUD APIs (plants, lines, batches, scrap, trials, money leaks)
- [ ] Integrate PlantOps endpoints with AI service stubs
- [ ] Implement FSQ context (Lots, Deviations, CAPA, Suppliers, tracing, documents)
- [ ] Create FSQ document upload endpoint with RAG hook point
- [ ] Implement Planning context (Forecasts, Plans, Safety Stocks)
- [ ] Implement Brand context (Brands, Products, Copackers, documents)
- [ ] Create Brand document upload endpoint with RAG hook point
- [ ] Implement Retail context (Stores, POS, Waste, OSA, Promos)
- [ ] Implement Copilot endpoint with tool registry and LLM integration
- [ ] Integrate Copilot with telemetry service (log all interactions)
- [ ] Create workspace-specific tools for all 5 contexts (PlantOps, FSQ, Planning, Brand, Retail)
- [ ] CRITICAL: Document Copilot-first UI pattern in code, ADR, and developer docs
- [ ] Create RAG infrastructure stubs with hook points (ingestion, search, pgvector schema)
- [ ] Design FSQ & Brand Copilot prompts for RAG with graceful degradation
- [ ] Implement telemetry analytics APIs (workspace stats, tool usage, acceptance rate)
- [ ] Create Copilot feedback collection endpoint
- [ ] Create CI workflows for linting, testing, and Docker builds
- [ ] Configure pre-commit hooks for code quality
- [ ] Create production Dockerfiles and update docker-compose
- [ ] Create basic K8s manifests for backend and AI service
- [ ] Document all architecture decisions in ADRs (8 ADRs including Copilot-first, telemetry)
- [ ] Create all developer guides (setup, testing, contributing, conventions, context guide)
- [ ] Create COPILOT_FIRST_PATTERN.md with detailed examples
- [ ] Create bounded contexts guide explaining DDD structure and workspace mapping
- [ ] Generate OpenAPI docs and create Postman collection
- [ ] Update root and service READMEs with Copilot-first value prop and architecture
- [ ] Create IMPLEMENTATION_GUIDE.md with P0/P1/P2 priorities
- [ ] Create full end-to-end test: tenant → auth → PlantOps API → AI stub → Copilot → telemetry
- [ ] Create basic telemetry dashboard showing Copilot usage and metrics