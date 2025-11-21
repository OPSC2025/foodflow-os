# FoodFlow OS - Foundation Implementation Plan

**Status**: Phase 1 Complete ✅ | **Next**: Phase 2 - Domain Models  
**Last Updated**: November 21, 2024

---

## 🎯 **CURRENT OBJECTIVE**
Complete the foundation infrastructure (Core Truth) that all features will be built upon.

**Timeline**: 2-4 weeks foundation sprint, then iterative feature development

---

## ✅ **PHASE 1: CORE INFRASTRUCTURE** (COMPLETED)

### Completed Items:
- ✅ Project structure with DDD contexts
- ✅ FastAPI application setup
- ✅ SQLAlchemy async database layer
- ✅ Multi-tenancy with schema-per-tenant (ContextVar-based isolation)
- ✅ JWT authentication & authorization (User, Role, Permission models)
- ✅ RFC 7807 error handling
- ✅ Structured logging (JSON format)
- ✅ Alembic migrations
- ✅ Pydantic settings management
- ✅ AI service client with retry & circuit breaker
- ✅ Telemetry models (CopilotInteraction, AISuggestion, AIFeedback)
- ✅ Identity context (User, Tenant, Role, Permission models + API)
- ✅ PlantOps context (initial models and API stubs)
- ✅ AI service stubs (PlantOps, FSQ, Planning, Brand, Retail modules)
- ✅ **CRITICAL FIXES**: Tenant isolation security, Alembic config, logging conflicts

### Known Gaps to Address:
- ⚠️ Password reset flow incomplete (tokens not persisted)
- ⚠️ Permission checking not implemented (TODO comments everywhere)
- ⚠️ Token refresh endpoint missing
- ⚠️ Duplicate services files in PlantOps (`services.py` and `services_updated.py`)

---

## 🔄 **PHASE 2: DOMAIN MODELS** (IN PROGRESS)

**Objective**: Complete all domain models for each context with proper relationships, validation, and business logic.

### 2.1 Identity Context ✅ (COMPLETE)
- ✅ User model with tenant association
- ✅ Role & Permission models with RBAC
- ✅ Tenant model with schema management
- ✅ RefreshToken model
- ✅ ApiKey model  
- ✅ AuditLog model

### 2.2 PlantOps Context 🔄 (NEEDS REVIEW & EXPANSION)
**Status**: Basic models exist but need enhancement

**Current Models** (need review):
- ProductionLine
- ProductionBatch
- Sensor
- SensorReading
- LineEvent
- ScrapEvent

**TODO - Add Missing Models**:
- [ ] **Equipment** - Individual equipment/machines on lines
- [ ] **MaintenanceSchedule** - Planned maintenance
- [ ] **MaintenanceEvent** - Actual maintenance performed
- [ ] **QualityCheck** - In-line quality checks
- [ ] **ProductionSchedule** - Planned production runs
- [ ] **Downtime** - Downtime events with categorization
- [ ] **ShiftReport** - End-of-shift summaries
- [ ] **TrialRun** - Experimental production trials
- [ ] **OEEMetric** - Calculated OEE metrics (availability, performance, quality)

**TODO - Enhance Existing Models**:
- [ ] Add relationships between models
- [ ] Add validation rules (Pydantic validators)
- [ ] Add business logic methods
- [ ] Add proper indexing for time-series queries

### 2.3 FSQ Context ⏳ (TODO)
**Status**: Not started

**Models to Create**:
- [ ] **Lot** - Production lot/batch for traceability
- [ ] **Supplier** - Supplier master data
- [ ] **SupplierAudit** - Supplier audit records
- [ ] **IngredientSpec** - Ingredient specifications
- [ ] **CCP** (Critical Control Point) - HACCP CCPs
- [ ] **CCPMonitoring** - CCP monitoring logs
- [ ] **DeviationEvent** - Process deviations
- [ ] **CorrectiveAction** - CAPA records
- [ ] **DocumentVersion** - Version control for FSQ documents
- [ ] **ComplianceCheck** - Regulatory compliance checks
- [ ] **Recall** - Product recall records
- [ ] **TraceabilityLink** - Forward/backward traceability
- [ ] **Certificate** - Supplier certificates (organic, kosher, etc.)

### 2.4 Planning Context ⏳ (TODO)
**Status**: Not started

**Models to Create**:
- [ ] **DemandForecast** - Demand predictions
- [ ] **ProductionPlan** - Master production schedule
- [ ] **InventoryLevel** - Current inventory
- [ ] **InventoryTransaction** - Inventory movements
- [ ] **SafetyStock** - Safety stock levels
- [ ] **PurchaseOrder** - Purchase orders
- [ ] **WorkOrder** - Production work orders
- [ ] **ShipmentPlan** - Outbound shipments
- [ ] **CapacityPlan** - Production capacity planning
- [ ] **MaterialRequirement** - MRP calculations
- [ ] **BOM** (Bill of Materials) - Product recipes

### 2.5 Brand Context ⏳ (TODO)
**Status**: Not started

**Models to Create**:
- [ ] **Product** - Finished goods master data
- [ ] **SKU** - Stock keeping units
- [ ] **Brand** - Brand information
- [ ] **Category** - Product categories
- [ ] **CoPacker** - Co-packer information
- [ ] **CoPackerAudit** - Co-packer audit records
- [ ] **MarginAnalysis** - Margin bridge calculations
- [ ] **PricingStrategy** - Pricing models
- [ ] **PromotionPlan** - Marketing promotions
- [ ] **ProductLaunch** - New product launches

### 2.6 Retail Context ⏳ (TODO)
**Status**: Not started

**Models to Create**:
- [ ] **Store** - Retail store information
- [ ] **RetailSKU** - SKUs specific to retail
- [ ] **POSTransaction** - Point of sale data
- [ ] **InventorySnapshot** - Store inventory levels
- [ ] **OSAEvent** - Out-of-stock alerts
- [ ] **PlanogramCompliance** - Shelf placement compliance
- [ ] **PromoPerformance** - Promotion effectiveness
- [ ] **ReplenishmentOrder** - Store replenishment

### 2.7 Core/Shared Models ⏳ (TODO)
**Status**: Not started

**Models to Create**:
- [ ] **Plant** - Manufacturing plant/facility
- [ ] **Location** - Generic location (warehouse, store, etc.)
- [ ] **Contact** - Contact information
- [ ] **Address** - Address information
- [ ] **Attachment** - File attachments
- [ ] **Note** - User notes/comments
- [ ] **Tag** - Tagging system
- [ ] **Notification** - User notifications
- [ ] **SystemConfig** - System-wide configuration

---

## 🌐 **PHASE 3: API ENDPOINTS** (TODO)

**Objective**: Build RESTful API endpoints for all domain models with proper validation, authentication, and authorization.

### 3.1 Identity API ✅ (MOSTLY COMPLETE)
- ✅ `/auth/register` - User registration
- ✅ `/auth/login` - Login with JWT
- ✅ `/auth/me` - Get current user
- ✅ `/auth/logout` - Logout (stub)
- ✅ `/auth/password-reset/initiate` - Start password reset
- ✅ `/auth/password-reset/confirm` - Complete password reset
- ✅ `/auth/password-change` - Change password (authenticated)
- ✅ `/users` - List users
- ✅ `/users/{id}` - Get user by ID
- ✅ `/tenants` - Create/list tenants
- ✅ `/tenants/{id}` - Get tenant by ID

**TODO**:
- [ ] `/auth/refresh` - Refresh JWT token
- [ ] `/roles` - CRUD for roles
- [ ] `/permissions` - CRUD for permissions
- [ ] Implement actual permission checking middleware
- [ ] Add proper RBAC decorators

### 3.2 PlantOps API 🔄 (PARTIAL)
**Status**: Basic CRUD endpoints exist but incomplete

**Existing**:
- ✅ Basic CRUD for lines, batches, sensors

**TODO**:
- [ ] Complete all CRUD operations
- [ ] Add filtering, sorting, pagination
- [ ] Add batch operations (bulk create/update)
- [ ] Add time-series queries for sensor data
- [ ] Add aggregation endpoints (OEE calculations, etc.)
- [ ] Add export endpoints (CSV, Excel)
- [ ] Add real-time endpoints (WebSocket for sensor streams)

### 3.3 FSQ API ⏳ (TODO)
- [ ] Lot traceability endpoints
- [ ] Supplier management endpoints
- [ ] CCP monitoring endpoints
- [ ] Deviation & CAPA endpoints
- [ ] Document management endpoints
- [ ] Compliance reporting endpoints
- [ ] Mock recall simulation endpoint

### 3.4 Planning API ⏳ (TODO)
- [ ] Demand forecast endpoints
- [ ] Production planning endpoints
- [ ] Inventory management endpoints
- [ ] Purchase order endpoints
- [ ] MRP calculation endpoints
- [ ] Capacity planning endpoints

### 3.5 Brand API ⏳ (TODO)
- [ ] Product/SKU management endpoints
- [ ] Co-packer management endpoints
- [ ] Margin analysis endpoints
- [ ] Pricing strategy endpoints
- [ ] Promotion planning endpoints

### 3.6 Retail API ⏳ (TODO)
- [ ] Store management endpoints
- [ ] POS data ingestion endpoints
- [ ] Inventory snapshot endpoints
- [ ] OSA detection endpoints
- [ ] Replenishment recommendation endpoints
- [ ] Planogram compliance endpoints

---

## 🤖 **PHASE 4: COPILOT INTEGRATION** (TODO)

**Objective**: Wire up the Copilot-First pattern with LangChain/LangGraph orchestration and RAG.

### 4.1 Copilot Orchestrator
- [ ] Create `/api/v1/copilot` endpoint
- [ ] Implement LangGraph workflow
- [ ] Create supervisor node for routing
- [ ] Define tool schemas for each context

### 4.2 Workspace-Specific Tools
- [ ] **PlantOps Tools**:
  - [ ] `analyze_scrap_spike` → calls AI service `/plant-ops/analyze-scrap`
  - [ ] `suggest_line_trial` → calls AI service `/plant-ops/suggest-line-trial`
  - [ ] `compute_oee` → calls AI service `/plant-ops/compute-efficiency`
  - [ ] `compare_batches` → calls AI service `/plant-ops/compare-batches`

- [ ] **FSQ Tools**:
  - [ ] `compute_lot_risk` → calls AI service `/fsq/compute-lot-risk`
  - [ ] `analyze_supplier_risk` → calls AI service `/fsq/analyze-supplier-risk`
  - [ ] `detect_ccp_drift` → calls AI service `/fsq/detect-ccp-drift`
  - [ ] `simulate_recall` → calls AI service `/fsq/simulate-mock-recall`
  - [ ] `compliance_qa` → calls AI service `/fsq/compliance-qa` (RAG)

- [ ] **Planning Tools**:
  - [ ] `generate_forecast` → calls AI service `/planning/generate-demand-forecast`
  - [ ] `optimize_production` → calls AI service `/planning/optimize-production-plan`
  - [ ] `recommend_safety_stock` → calls AI service `/planning/recommend-safety-stock`

- [ ] **Brand Tools**:
  - [ ] `analyze_margin_bridge` → calls AI service `/brand/analyze-margin-bridge`
  - [ ] `assess_copacker_risk` → calls AI service `/brand/assess-copacker-risk`

- [ ] **Retail Tools**:
  - [ ] `detect_osa_event` → calls AI service `/retail/detect-osa-event`
  - [ ] `recommend_replenishment` → calls AI service `/retail/recommend-replenishment`

### 4.3 RAG Implementation
- [ ] Set up pgvector extension in PostgreSQL
- [ ] Create embeddings table
- [ ] Implement document ingestion pipeline
- [ ] Create semantic search endpoint
- [ ] Wire RAG into Copilot tools (especially compliance_qa)

### 4.4 System Prompts & Context
- [ ] Create workspace-specific system prompts
- [ ] Implement context gathering from current UI state
- [ ] Add conversation history management
- [ ] Implement human-in-the-loop approval gates

### 4.5 Smart Buttons (Frontend Integration)
- [ ] Document pattern: Smart buttons call `/copilot` with specific prompts
- [ ] Create example smart button implementations
- [ ] Add context injection (entity IDs, time ranges, etc.)

---

## 🧪 **PHASE 5: TESTING & CI/CD** (TODO)

### 5.1 Testing
- [ ] Increase test coverage to 80%+
- [ ] Add integration tests for all API endpoints
- [ ] Add repository tests
- [ ] Add tenant isolation tests (critical!)
- [ ] Add AI service client tests (mock responses)
- [ ] Add end-to-end tests

### 5.2 CI/CD
- [ ] Create GitHub Actions workflow for:
  - [ ] Linting (Ruff)
  - [ ] Type checking (MyPy)
  - [ ] Tests (pytest)
  - [ ] Coverage reporting
  - [ ] Docker build
  - [ ] Deploy to staging (on merge to main)
  - [ ] Deploy to production (on release tag)

### 5.3 Documentation
- [ ] Complete API documentation (OpenAPI/Swagger)
- [ ] Update README with setup instructions
- [ ] Document deployment process
- [ ] Create developer guide
- [ ] Document Copilot-First pattern

---

## 📋 **IMMEDIATE NEXT STEPS** (Priority Order)

1. **Review & Clean Up PlantOps Models** (1-2 hours)
   - Review existing models
   - Remove duplicate `services.py` vs `services_updated.py`
   - Add missing models (Equipment, Maintenance, etc.)
   - Add proper relationships and validation

2. **Implement FSQ Domain Models** (4-6 hours)
   - Lot, Supplier, CCP, Deviation, CAPA, etc.
   - Focus on traceability and compliance

3. **Implement Planning Domain Models** (4-6 hours)
   - Forecast, ProductionPlan, Inventory, BOM, etc.
   - Focus on supply chain visibility

4. **Implement Brand & Retail Models** (3-4 hours)
   - Product, SKU, Store, OSA, etc.
   - Focus on go-to-market data

5. **Build Out API Endpoints** (2-3 days)
   - Complete CRUD for all models
   - Add filtering, pagination, sorting
   - Implement proper RBAC checks

6. **Wire Up Copilot** (2-3 days)
   - Create Copilot endpoint
   - Implement LangGraph workflow
   - Connect to AI service tools
   - Add RAG for compliance Q&A

7. **Testing & Polish** (2-3 days)
   - Add comprehensive tests
   - Fix any remaining bugs
   - Set up CI/CD
   - Complete documentation

---

## 📊 **PROGRESS TRACKER**

**Overall Foundation Progress**: 35% Complete

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1: Core Infrastructure | ✅ Complete | 100% |
| Phase 2: Domain Models | 🔄 In Progress | 15% |
| Phase 3: API Endpoints | ⏳ Not Started | 5% |
| Phase 4: Copilot Integration | ⏳ Not Started | 0% |
| Phase 5: Testing & CI/CD | ⏳ Not Started | 0% |

---

## 🎯 **SUCCESS CRITERIA**

Foundation is complete when:
- ✅ All domain models implemented with proper relationships
- ✅ All CRUD APIs working with tenant isolation
- ✅ Copilot endpoint functional with at least 2-3 tools per context
- ✅ RAG working for compliance Q&A
- ✅ 80%+ test coverage
- ✅ CI/CD pipeline running
- ✅ Can demo multi-tenant workflow end-to-end
- ✅ Documentation complete

**Target Completion**: 2-4 weeks from start (we're ~1 week in)

---

## 🚀 **AFTER FOUNDATION**

Once foundation is solid, we'll shift to iterative feature development:
1. Pick highest-value features per context
2. Build end-to-end (backend + frontend + AI)
3. Ship, gather feedback, iterate

**Philosophy**: Foundation first, then iterate fast!

