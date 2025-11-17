# FoodFlow OS: Implementation Roadmap for AI Coders

**Version:** 1.0  
**Date:** November 16, 2025  
**Purpose:** Step-by-step implementation guide for AI coding agents

---

## Overview

This roadmap is designed for **AI-assisted development** using tools like Cursor, Windsurf, GitHub Copilot, or similar AI coding agents. Each phase includes specific prompts and context to provide to your AI coder.

### Development Approach

1. **Monorepo Structure**: All services in a single repository for easier development
2. **Docker Compose**: Local development environment with all databases
3. **Kubernetes**: Production deployment with Helm charts
4. **CI/CD**: GitHub Actions for automated testing and deployment
5. **AI-First**: Use AI coding agents for 80%+ of code generation

### Team Structure (8-10 people)

- **1 Solution Architect**: Overall architecture, technology decisions, code review
- **2-3 Tech Leads**: Service ownership, AI coder orchestration, code review
- **5-6 AI Orchestrators**: Prompt engineering, AI coder supervision, testing

---

## Phase 1: Foundation & Infrastructure (Weeks 1-2)

### Goals
- Set up monorepo structure
- Configure Docker Compose for local development
- Implement Identity Service (authentication)
- Implement Tenant Service (multi-tenancy)

### Deliverables

#### 1.1 Monorepo Setup

**AI Coder Prompt**:
```
Create a monorepo structure for FoodFlow OS with the following layout:

foodflow-os/
├── services/
│   ├── identity-service/          # NestJS
│   ├── tenant-service/            # NestJS
│   ├── foodgraph-service/         # FastAPI
│   ├── forecast-service/          # FastAPI
│   ├── vision-service/            # FastAPI
│   ├── llm-orchestration-service/ # FastAPI
│   ├── optimization-service/      # FastAPI
│   ├── sensor-analytics-service/  # FastAPI
│   ├── production-analytics-service/ # FastAPI
│   ├── integration-service/       # NestJS
│   ├── data-room-service/         # NestJS
│   └── notification-service/      # NestJS
├── packages/
│   ├── shared-types/              # TypeScript types
│   ├── shared-utils/              # Utility functions
│   └── shared-config/             # Configuration
├── apps/
│   └── workspace-ui/              # Next.js 15
├── infra/
│   ├── docker/                    # Dockerfiles
│   ├── kubernetes/                # Helm charts
│   └── terraform/                 # Infrastructure as code
├── docs/                          # Documentation
├── scripts/                       # Utility scripts
├── docker-compose.yml             # Local development
├── package.json                   # Root package.json
├── pnpm-workspace.yaml            # PNPM workspace config
├── .gitignore
├── .env.example
└── README.md

Requirements:
- Use PNPM workspaces for monorepo management
- TypeScript for all TypeScript services
- Python 3.11+ for all Python services
- Shared configuration and types across services
- Docker Compose with all databases (PostgreSQL, Neo4j, MongoDB, TimescaleDB, Redis, Kafka, Pinecone)

Output:
- Complete directory structure
- package.json with workspace configuration
- docker-compose.yml with all services
- .env.example with all environment variables
- README.md with setup instructions
```

#### 1.2 Docker Compose Environment

**AI Coder Prompt**:
```
Create a Docker Compose file for FoodFlow OS local development with the following services:

Databases:
- PostgreSQL 16 (port 5432)
- Neo4j Enterprise 5.x (ports 7474, 7687)
- MongoDB 7.x (port 27017)
- TimescaleDB 2.x (port 5433)
- Redis 7.x (port 6379)
- Kafka 3.x (port 9092)
- Zookeeper 3.x (port 2181)

Infrastructure:
- Kong API Gateway (ports 8000, 8001, 8443, 8444)
- Prometheus (port 9090)
- Grafana (port 3000)
- Jaeger (ports 16686, 14268)

Requirements:
- All databases should persist data to volumes
- Health checks for all services
- Network isolation (separate networks for services and databases)
- Environment variables from .env file
- Resource limits (CPU, memory)

Output:
- docker-compose.yml
- .env.example
- README with instructions to start environment
```

#### 1.3 Identity Service (NestJS)

**AI Coder Prompt**:
```
Implement the Identity Service for FoodFlow OS using NestJS + TypeScript + Passport.js + JWT.

Context:
- This is the authentication and authorization service
- Multi-tenant (tenant_id in JWT token)
- OAuth2/OIDC support
- Role-based access control (RBAC)

Requirements:
1. Authentication:
   - POST /auth/login (email + password)
   - POST /auth/logout
   - POST /auth/refresh (refresh JWT token)
   - GET /auth/me (get current user)
   - POST /auth/register (create new user)
   - POST /auth/forgot-password
   - POST /auth/reset-password

2. User Management:
   - POST /users (create user)
   - GET /users/:id (get user)
   - PUT /users/:id (update user)
   - DELETE /users/:id (delete user)
   - GET /users (list users with pagination)

3. Role Management:
   - POST /roles (create role)
   - GET /roles/:id (get role)
   - PUT /roles/:id (update role)
   - DELETE /roles/:id (delete role)
   - GET /roles (list roles)
   - POST /roles/:id/permissions (assign permissions to role)

4. Database Schema (PostgreSQL):
   - users (id, email, password_hash, first_name, last_name, tenant_id, created_at, updated_at)
   - roles (id, name, description, tenant_id, created_at, updated_at)
   - permissions (id, resource, action, description, created_at, updated_at)
   - user_roles (user_id, role_id)
   - role_permissions (role_id, permission_id)

5. Security:
   - Bcrypt for password hashing
   - JWT tokens with 15-minute expiry
   - Refresh tokens with 7-day expiry
   - Rate limiting (10 requests/minute for login)
   - CORS configuration

6. Testing:
   - Unit tests for all services (Jest)
   - Integration tests for all endpoints
   - Test coverage > 80%

Technology Stack:
- NestJS 10+
- TypeScript 5+
- Passport.js (JWT strategy)
- TypeORM (PostgreSQL)
- Bcrypt
- Class-validator
- Class-transformer

Output:
- Complete NestJS service with all endpoints
- Database migrations (TypeORM)
- Unit tests (Jest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation (Swagger)
```

#### 1.4 Tenant Service (NestJS)

**AI Coder Prompt**:
```
Implement the Tenant Service for FoodFlow OS using NestJS + TypeScript + Stripe.

Context:
- This is the multi-tenancy and subscription management service
- Each tenant is an organization (food company)
- Subscription plans (Free, Pro, Enterprise)
- Feature flags per tenant

Requirements:
1. Tenant Management:
   - POST /tenants (create tenant)
   - GET /tenants/:id (get tenant)
   - PUT /tenants/:id (update tenant)
   - DELETE /tenants/:id (delete tenant)
   - GET /tenants (list tenants with pagination)

2. Subscription Management:
   - GET /tenants/:id/subscription (get subscription)
   - PUT /tenants/:id/subscription (update subscription)
   - POST /tenants/:id/subscription/cancel (cancel subscription)
   - POST /tenants/:id/subscription/reactivate (reactivate subscription)

3. Usage Tracking:
   - GET /tenants/:id/usage (get usage metrics)
   - POST /tenants/:id/usage (record usage)

4. Feature Flags:
   - GET /tenants/:id/features (get feature flags)
   - PUT /tenants/:id/features/:feature (enable/disable feature)

5. Database Schema (PostgreSQL):
   - tenants (id, name, slug, logo_url, primary_color, subscription_plan, subscription_status, created_at, updated_at)
   - subscriptions (id, tenant_id, plan, status, current_period_start, current_period_end, stripe_subscription_id, created_at, updated_at)
   - usage_metrics (id, tenant_id, metric_name, value, timestamp)
   - feature_flags (id, tenant_id, feature_name, enabled, created_at, updated_at)

6. Stripe Integration:
   - Create customer on tenant creation
   - Create subscription on plan selection
   - Handle webhooks (subscription.created, subscription.updated, subscription.deleted)
   - Sync subscription status

7. Testing:
   - Unit tests for all services (Jest)
   - Integration tests for all endpoints
   - Mock Stripe API calls
   - Test coverage > 80%

Technology Stack:
- NestJS 10+
- TypeScript 5+
- TypeORM (PostgreSQL)
- Stripe Node.js SDK
- Class-validator
- Class-transformer

Output:
- Complete NestJS service with all endpoints
- Database migrations (TypeORM)
- Stripe webhook handlers
- Unit tests (Jest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation (Swagger)
```

### Phase 1 Checklist

- [ ] Monorepo structure created
- [ ] Docker Compose environment running
- [ ] Identity Service implemented and tested
- [ ] Tenant Service implemented and tested
- [ ] API Gateway (Kong) configured
- [ ] All services containerized (Docker)
- [ ] Documentation updated

---

## Phase 2: Core Data Services (Weeks 3-6)

### Goals
- Implement FoodGraph Service (Neo4j traceability)
- Implement Forecast Service (Nixtla forecasting)
- Implement Sensor Analytics Service (anomaly detection)
- Implement Production Analytics Service (OEE)

### Deliverables

#### 2.1 FoodGraph Service (FastAPI + Neo4j)

**AI Coder Prompt**:
```
Implement the FoodGraph Service for FoodFlow OS using FastAPI + Python + Neo4j Python Driver.

Context:
- This is the core traceability and supplier network service
- Neo4j graph database for relationships
- Forward/backward traceability queries
- Supplier risk propagation

Requirements:
1. Graph Queries:
   - POST /graph/query (execute Cypher query)
   - GET /graph/traceability/forward (forward tracing from ingredient)
   - GET /graph/traceability/backward (backward tracing from finished good)
   - GET /graph/suppliers/:id/network (supplier network visualization)
   - GET /graph/suppliers/:id/risk (supplier risk score)

2. Node Management:
   - POST /graph/nodes (create node)
   - GET /graph/nodes/:id (get node)
   - PUT /graph/nodes/:id (update node)
   - DELETE /graph/nodes/:id (delete node)
   - GET /graph/nodes (list nodes with filters)

3. Relationship Management:
   - POST /graph/relationships (create relationship)
   - GET /graph/relationships/:id (get relationship)
   - PUT /graph/relationships/:id (update relationship)
   - DELETE /graph/relationships/:id (delete relationship)
   - GET /graph/relationships (list relationships with filters)

4. Neo4j Schema:
   - Nodes: Product, Ingredient, Supplier, Batch, Location
   - Relationships: CONTAINS, SOURCED_FROM, PRODUCED_AT, SHIPPED_TO
   - Properties: id, name, tenant_id, created_at, updated_at

5. Multi-Tenancy:
   - Separate Neo4j database per tenant
   - Application-level access control (JWT token validation)

6. Performance:
   - Index on tenant_id, id, name
   - Query optimization (EXPLAIN PLAN)
   - Caching with Redis (frequently accessed paths)

7. Testing:
   - Unit tests for all services (pytest)
   - Integration tests for all endpoints
   - Test coverage > 80%

Technology Stack:
- FastAPI 0.100+
- Python 3.11+
- Neo4j Python Driver 5.x
- Pydantic 2.x
- Redis (caching)

Output:
- Complete FastAPI service with all endpoints
- Neo4j schema (Cypher)
- Unit tests (pytest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation (automatic with FastAPI)
```

#### 2.2 Forecast Service (FastAPI + Nixtla)

**AI Coder Prompt**:
```
Implement the Forecast Service for FoodFlow OS using FastAPI + Python + Nixtla (StatsForecast, HierarchicalForecast).

Context:
- This is the demand forecasting service
- Hierarchical forecasting (brand → category → product → SKU → location)
- Probabilistic forecasts (P10, P50, P90)
- Forecast reconciliation (MinTrace, BottomUp, TopDown)

Requirements:
1. Forecasting:
   - POST /forecasts/demand (generate demand forecast)
   - GET /forecasts/:id (get forecast by ID)
   - GET /forecasts (list forecasts with filters)
   - DELETE /forecasts/:id (delete forecast)

2. Forecast Accuracy:
   - GET /forecasts/accuracy (forecast accuracy metrics)
   - POST /forecasts/accuracy/calculate (calculate accuracy for period)

3. Inventory Optimization:
   - POST /forecasts/inventory/optimize (optimize inventory levels)
   - GET /forecasts/inventory/recommendations (get inventory recommendations)

4. Hierarchies:
   - GET /forecasts/hierarchies (get forecast hierarchies)
   - POST /forecasts/hierarchies (create forecast hierarchy)

5. Database Schema (TimescaleDB):
   - forecasts (id, tenant_id, sku, location, forecast_date, horizon, p10, p50, p90, model, created_at)
   - actuals (id, tenant_id, sku, location, date, quantity, created_at)
   - forecast_accuracy (id, tenant_id, sku, location, date, mape, rmse, bias, created_at)
   - inventory_recommendations (id, tenant_id, sku, location, safety_stock, reorder_point, created_at)

6. Forecasting Models:
   - AutoARIMA (baseline)
   - AutoETS (exponential smoothing)
   - AutoTheta (theta method)
   - Ensemble (average of all models)

7. Hierarchical Reconciliation:
   - MinTrace (primary): Minimizes total forecast variance
   - BottomUp (fallback): Simple aggregation
   - TopDown (for top-level constraints): Distributes forecasts

8. Testing:
   - Unit tests for all services (pytest)
   - Integration tests for all endpoints
   - Test coverage > 80%

Technology Stack:
- FastAPI 0.100+
- Python 3.11+
- StatsForecast 1.7+
- HierarchicalForecast 0.5+
- Pandas 2.x
- TimescaleDB (via SQLAlchemy)

Output:
- Complete FastAPI service with all endpoints
- Database migrations (Alembic)
- Unit tests (pytest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation
```

#### 2.3 Sensor Analytics Service (FastAPI + TimescaleDB)

**AI Coder Prompt**:
```
Implement the Sensor Analytics Service for FoodFlow OS using FastAPI + Python + TimescaleDB + Scikit-learn.

Context:
- This is the real-time sensor monitoring and anomaly detection service
- Time-series data (temperature, humidity, pressure, etc.)
- Anomaly detection (threshold-based and ML-based)
- Alert generation

Requirements:
1. Sensor Data:
   - POST /sensors/data (ingest sensor data - bulk)
   - GET /sensors/:id/data (get sensor data for sensor)
   - GET /sensors (list sensors)
   - POST /sensors (register sensor)

2. Anomalies:
   - GET /sensors/anomalies (get anomalies)
   - GET /sensors/:id/anomalies (get anomalies for sensor)
   - POST /sensors/anomalies/detect (run anomaly detection)

3. Alerts:
   - POST /sensors/alerts (create alert rule)
   - GET /sensors/alerts (get alert rules)
   - PUT /sensors/alerts/:id (update alert rule)
   - DELETE /sensors/alerts/:id (delete alert rule)

4. Database Schema (TimescaleDB):
   - sensor_data (time, tenant_id, sensor_id, location_id, metric, value, unit)
   - sensor_anomalies (id, tenant_id, sensor_id, time, metric, value, expected_value, anomaly_score, created_at)
   - sensor_alerts (id, tenant_id, sensor_id, metric, condition, threshold, notification_channel, created_at, updated_at)
   - sensors (id, tenant_id, name, type, location_id, created_at, updated_at)

5. Anomaly Detection:
   - Threshold-based (value > threshold or value < threshold)
   - Z-score (statistical outlier detection)
   - Isolation Forest (ML-based anomaly detection)

6. Real-Time Processing:
   - Kafka consumer for real-time sensor data
   - Stream processing with sliding windows
   - Alert generation and notification

7. Testing:
   - Unit tests for all services (pytest)
   - Integration tests for all endpoints
   - Test coverage > 80%

Technology Stack:
- FastAPI 0.100+
- Python 3.11+
- TimescaleDB (via SQLAlchemy)
- Scikit-learn 1.3+
- Kafka Python client
- Pandas 2.x

Output:
- Complete FastAPI service with all endpoints
- Database migrations (Alembic)
- Kafka consumer for real-time data
- Anomaly detection models
- Unit tests (pytest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation
```

#### 2.4 Production Analytics Service (FastAPI + TimescaleDB)

**AI Coder Prompt**:
```
Implement the Production Analytics Service for FoodFlow OS using FastAPI + Python + TimescaleDB + Pandas.

Context:
- This is the production monitoring and OEE calculation service
- Overall Equipment Effectiveness (OEE)
- Downtime analysis (planned vs unplanned)
- Quality metrics (defect rate, first-pass yield)

Requirements:
1. OEE:
   - GET /production/oee (get OEE metrics)
   - GET /production/oee/history (get historical OEE)
   - POST /production/oee/calculate (calculate OEE for period)

2. Downtime:
   - GET /production/downtime (get downtime events)
   - POST /production/downtime (record downtime event)
   - GET /production/downtime/analysis (downtime analysis)

3. Quality:
   - GET /production/quality (get quality metrics)
   - POST /production/quality (record quality data)
   - GET /production/quality/trends (quality trends)

4. Shifts:
   - GET /production/shifts (get shift reports)
   - POST /production/shifts (record shift data)

5. Database Schema (TimescaleDB):
   - production_events (time, tenant_id, line_id, event_type, duration, quantity, created_at)
   - downtime_events (id, tenant_id, line_id, start_time, end_time, reason, category, created_at)
   - quality_events (id, tenant_id, line_id, time, defect_type, quantity, created_at)
   - oee_metrics (time, tenant_id, line_id, availability, performance, quality, oee, created_at)

6. OEE Calculation:
   - Availability = (Planned Production Time - Downtime) / Planned Production Time
   - Performance = (Actual Output / Theoretical Maximum Output)
   - Quality = (Good Units / Total Units)
   - OEE = Availability × Performance × Quality

7. Testing:
   - Unit tests for all services (pytest)
   - Integration tests for all endpoints
   - Test coverage > 80%

Technology Stack:
- FastAPI 0.100+
- Python 3.11+
- TimescaleDB (via SQLAlchemy)
- Pandas 2.x

Output:
- Complete FastAPI service with all endpoints
- Database migrations (Alembic)
- OEE calculation logic
- Unit tests (pytest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation
```

### Phase 2 Checklist

- [ ] FoodGraph Service implemented and tested
- [ ] Forecast Service implemented and tested
- [ ] Sensor Analytics Service implemented and tested
- [ ] Production Analytics Service implemented and tested
- [ ] All services integrated with API Gateway
- [ ] Documentation updated

---

## Phase 3: AI/ML Services (Weeks 7-10)

### Goals
- Implement Vision Service (YOLOv10 defect detection)
- Implement LLM Orchestration Service (LangGraph + RAG)
- Implement Optimization Service (Gurobi + OR-Tools)

### Deliverables

#### 3.1 Vision Service (FastAPI + YOLOv10)

**AI Coder Prompt**:
```
Implement the Vision Service for FoodFlow OS using FastAPI + Python + YOLOv10 + ONNX Runtime.

Context:
- This is the computer vision service for defect detection
- YOLOv10 for real-time object detection
- Few-shot learning for dynamic SKU onboarding
- ONNX export for edge deployment

Requirements:
1. Inference:
   - POST /vision/inference (run inference on image)
   - POST /vision/inference/batch (run inference on multiple images)
   - GET /vision/results (get inference results)
   - GET /vision/results/:id (get inference result by ID)

2. Model Management:
   - GET /vision/models (list models)
   - GET /vision/models/:id (get model details)
   - POST /vision/models/train (train model with few-shot learning)
   - POST /vision/models/:id/deploy (deploy model to edge)
   - DELETE /vision/models/:id (delete model)

3. Training Data:
   - POST /vision/training/images (upload training images)
   - GET /vision/training/images (list training images)
   - DELETE /vision/training/images/:id (delete training image)

4. Defect Analysis:
   - GET /vision/defects/summary (defect summary analytics)
   - GET /vision/defects/trends (defect trends over time)

5. Database Schema (MongoDB):
   - vision_models {_id, tenant_id, name, version, type, sku, accuracy, created_at, updated_at}
   - vision_results {_id, tenant_id, model_id, image_url, inference_time, defects: [{type, confidence, bbox}], created_at}
   - training_images {_id, tenant_id, sku, image_url, label, bbox, created_at}

6. YOLOv10 Integration:
   - Load pre-trained YOLOv10 model
   - Fine-tune with few-shot learning (5-10 images)
   - Export to ONNX format
   - Deploy to edge via Azure IoT Edge

7. Testing:
   - Unit tests for all services (pytest)
   - Integration tests for all endpoints
   - Test coverage > 80%

Technology Stack:
- FastAPI 0.100+
- Python 3.11+
- YOLOv10 (Ultralytics)
- ONNX Runtime
- PyTorch 2.x
- MongoDB (via Motor - async driver)
- OpenCV

Output:
- Complete FastAPI service with all endpoints
- YOLOv10 training pipeline
- ONNX export script
- Unit tests (pytest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation
```

#### 3.2 LLM Orchestration Service (FastAPI + LangGraph)

**AI Coder Prompt**:
```
Implement the LLM Orchestration Service for FoodFlow OS using FastAPI + Python + LangGraph + Pinecone + Pydantic-AI.

Context:
- This is the AI co-pilot service
- Natural language interface for FSQ teams
- Specialized AI agents (FoodGraph, Forecast, Vision, Compliance, Optimization)
- Multi-tenant RAG with Pinecone

Requirements:
1. Queries:
   - POST /llm/query (natural language query)
   - POST /llm/conversations (start conversation)
   - POST /llm/conversations/:id/messages (send message in conversation)
   - GET /llm/conversations/:id (get conversation history)
   - DELETE /llm/conversations/:id (delete conversation)

2. RAG:
   - POST /llm/rag/ingest (ingest documents for RAG)
   - GET /llm/rag/search (semantic search)
   - DELETE /llm/rag/documents/:id (delete document)

3. Approvals (Human-in-the-Loop):
   - GET /llm/approvals (get pending approvals)
   - POST /llm/approvals/:id/approve (approve action)
   - POST /llm/approvals/:id/reject (reject action)

4. Database Schema (PostgreSQL):
   - conversations (id, tenant_id, user_id, title, created_at, updated_at)
   - messages (id, conversation_id, role, content, agent, confidence, created_at)
   - approvals (id, conversation_id, message_id, status, approved_by, approved_at, created_at)

5. LangGraph Workflow:
   - Supervisor Node (routes queries to specialized agents)
   - FoodGraph Agent (traceability queries)
   - Forecast Agent (demand forecasts)
   - Vision Agent (defect analysis)
   - Compliance Agent (regulatory Q&A)
   - Optimization Agent (production planning)
   - Human-in-the-Loop Node (approval gates)

6. Multi-Tenant RAG:
   - Separate Pinecone namespace per tenant
   - Global knowledge base (shared FSQ/regulatory docs)
   - Per-tenant knowledge base (SOPs, specifications, policies)

7. LLM Models:
   - GPT-5.1 (primary)
   - Claude Sonnet 4.5 (fallback)
   - Gemini 2.5 Pro (specialized tasks)

8. Testing:
   - Unit tests for all services (pytest)
   - Integration tests for all endpoints
   - Test coverage > 80%

Technology Stack:
- FastAPI 0.100+
- Python 3.11+
- LangGraph 0.2+
- LangChain 0.3+
- Pydantic-AI 0.0.14+
- Pinecone 5.x
- OpenAI Python SDK
- Anthropic Python SDK
- Google Generative AI Python SDK

Output:
- Complete FastAPI service with all endpoints
- LangGraph workflow definitions
- RAG pipeline (ingestion, retrieval, generation)
- Unit tests (pytest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation
```

#### 3.3 Optimization Service (FastAPI + Gurobi)

**AI Coder Prompt**:
```
Implement the Optimization Service for FoodFlow OS using FastAPI + Python + Gurobi + Google OR-Tools.

Context:
- This is the production planning and optimization service
- Mixed Integer Programming (MIP) for production planning
- Vehicle Routing Problem (VRP) for delivery optimization

Requirements:
1. Production Planning:
   - POST /optimization/production/plan (generate production plan)
   - GET /optimization/production/plans/:id (get production plan)
   - GET /optimization/production/plans (list production plans)

2. Inventory Optimization:
   - POST /optimization/inventory/optimize (optimize inventory levels)
   - GET /optimization/inventory/recommendations (get inventory recommendations)

3. Routing:
   - POST /optimization/routing/optimize (optimize delivery routes)
   - GET /optimization/routing/plans/:id (get routing plan)

4. Results:
   - GET /optimization/results/:id (get optimization results)
   - GET /optimization/results (list optimization results)

5. Database Schema (PostgreSQL):
   - optimization_runs (id, tenant_id, type, status, objective_value, solve_time, created_at, updated_at)
   - production_plans (id, run_id, sku, location, date, quantity, created_at)
   - inventory_plans (id, run_id, sku, location, safety_stock, reorder_point, created_at)
   - routing_plans (id, run_id, vehicle_id, route: jsonb, distance, duration, created_at)

6. Optimization Models:
   - Production Planning (Gurobi MIP)
   - Inventory Optimization (Gurobi MIP)
   - Vehicle Routing (Google OR-Tools)

7. Testing:
   - Unit tests for all services (pytest)
   - Integration tests for all endpoints
   - Test coverage > 80%

Technology Stack:
- FastAPI 0.100+
- Python 3.11+
- Gurobi 11.x (requires license)
- Google OR-Tools 9.x
- Pandas 2.x

Output:
- Complete FastAPI service with all endpoints
- Optimization models (Gurobi, OR-Tools)
- Unit tests (pytest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation
```

### Phase 3 Checklist

- [ ] Vision Service implemented and tested
- [ ] LLM Orchestration Service implemented and tested
- [ ] Optimization Service implemented and tested
- [ ] All services integrated with API Gateway
- [ ] Documentation updated

---

## Phase 4: Integration & Edge (Weeks 11-14)

### Goals
- Implement Integration Service (ERP/FSQ/MES connectors)
- Implement Data Room Service (cross-org data sharing)
- Implement Notification Service (alerts, emails, SMS)
- Deploy edge runtime (Azure IoT Edge)

### Deliverables

#### 4.1 Integration Service (NestJS)

**AI Coder Prompt**:
```
Implement the Integration Service for FoodFlow OS using NestJS + TypeScript with pre-built connectors for Odoo, SAP, FSQapp.

Context:
- This is the integration layer for external systems
- Pre-built connectors for Odoo, SAP, FSQapp
- Data transformation (external → FoodFlow OS data models)
- Bidirectional sync

Requirements:
1. Connectors:
   - GET /integrations/connectors (list available connectors)
   - POST /integrations/connectors (configure connector)
   - GET /integrations/connectors/:id (get connector config)
   - PUT /integrations/connectors/:id (update connector config)
   - DELETE /integrations/connectors/:id (delete connector)
   - POST /integrations/connectors/:id/test (test connector)

2. Sync:
   - POST /integrations/sync (trigger sync)
   - GET /integrations/sync/status (get sync status)
   - GET /integrations/sync/history (get sync history)

3. Webhooks:
   - POST /integrations/webhooks (register webhook)
   - DELETE /integrations/webhooks/:id (delete webhook)
   - POST /webhooks/:connector_id (receive webhook)

4. Database Schema (PostgreSQL):
   - connectors (id, tenant_id, type, config: jsonb, status, created_at, updated_at)
   - sync_jobs (id, connector_id, status, started_at, completed_at, records_synced, errors: jsonb)
   - webhooks (id, connector_id, url, events: jsonb, secret, created_at, updated_at)

5. Connector Implementations:
   - Odoo (REST API)
   - SAP (OData API)
   - FSQapp (REST API)

6. Data Transformation:
   - External data models → FoodFlow OS data models
   - Validation with Pydantic schemas
   - Error handling and retry logic

7. Testing:
   - Unit tests for all services (Jest)
   - Integration tests for all endpoints
   - Mock external APIs
   - Test coverage > 80%

Technology Stack:
- NestJS 10+
- TypeScript 5+
- TypeORM (PostgreSQL)
- Axios (HTTP client)
- Class-validator
- Class-transformer

Output:
- Complete NestJS service with all endpoints
- Connector implementations (Odoo, SAP, FSQapp)
- Data transformation logic
- Unit tests (Jest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation (Swagger)
```

#### 4.2 Data Room Service (NestJS)

**AI Coder Prompt**:
```
Implement the Data Room Service for FoodFlow OS using NestJS + TypeScript + Neo4j.

Context:
- This is the cross-org data sharing service
- Secure data rooms with granular permissions
- Data room contracts (what data is shared, with whom, for how long)

Requirements:
1. Data Rooms:
   - POST /data-rooms (create data room)
   - GET /data-rooms/:id (get data room)
   - PUT /data-rooms/:id (update data room)
   - DELETE /data-rooms/:id (delete data room)
   - GET /data-rooms (list data rooms)

2. Contracts:
   - POST /data-rooms/:id/contracts (create contract)
   - GET /data-rooms/:id/contracts (list contracts)
   - PUT /data-rooms/:id/contracts/:contract_id (update contract)
   - DELETE /data-rooms/:id/contracts/:contract_id (delete contract)
   - POST /data-rooms/:id/contracts/:contract_id/approve (approve contract)

3. Access:
   - POST /data-rooms/:id/access (request access)
   - GET /data-rooms/:id/access (list access requests)
   - POST /data-rooms/:id/access/:request_id/approve (approve access)
   - POST /data-rooms/:id/access/:request_id/reject (reject access)

4. Data:
   - GET /data-rooms/:id/data (query data in data room)

5. Database Schema (PostgreSQL + Neo4j):
   - data_rooms (id, name, description, owner_tenant_id, created_at, updated_at)
   - contracts (id, data_room_id, participant_tenant_id, data_scope: jsonb, permissions: jsonb, expiry_date, status, created_at, updated_at)
   - access_requests (id, data_room_id, requester_tenant_id, status, requested_at, approved_at, approved_by)

6. Neo4j Integration:
   - Shared "network graph" database for cross-org relationships
   - Application-level access control (check contract permissions)

7. Testing:
   - Unit tests for all services (Jest)
   - Integration tests for all endpoints
   - Test coverage > 80%

Technology Stack:
- NestJS 10+
- TypeScript 5+
- TypeORM (PostgreSQL)
- Neo4j Python Driver (via microservice call)
- Class-validator
- Class-transformer

Output:
- Complete NestJS service with all endpoints
- Contract management logic
- Access control logic
- Unit tests (Jest)
- Integration tests
- Dockerfile
- README with setup instructions
- OpenAPI documentation (Swagger)
```

#### 4.3 Notification Service (NestJS)

**AI Coder Prompt**:
```
Implement the Notification Service for FoodFlow OS using NestJS + TypeScript + Bull (Redis queue).

Context:
- This is the notification and alerting service
- Multiple channels (email, SMS, Slack, webhooks)
- Async processing with Bull queues

Requirements:
1. Notifications:
   - POST /notifications (send notification)
   - GET /notifications (list notifications)
   - GET /notifications/:id (get notification)
   - PUT /notifications/:id/read (mark as read)

2. Templates:
   - POST /notifications/templates (create template)
   - GET /notifications/templates (list templates)
   - PUT /notifications/templates/:id (update template)
   - DELETE /notifications/templates/:id (delete template)

3. Channels:
   - POST /notifications/channels (configure channel)
   - GET /notifications/channels (list channels)
   - PUT /notifications/channels/:id (update channel)
   - DELETE /notifications/channels/:id (delete channel)

4. Database Schema (PostgreSQL):
   - notifications (id, tenant_id, user_id, type, title, message, channel, status, sent_at, read_at, created_at)
   - templates (id, tenant_id, name, subject, body, channel, created_at, updated_at)
   - channels (id, tenant_id, type, config: jsonb, create
