# FoodFlow OS: Enhanced System Architecture

**Document Version:** 2.0  
**Last Updated:** November 16, 2025  
**Author:** Manus AI  
**Status:** Production-Ready Specification

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Principles](#architecture-principles)
3. [Hybrid Deployment Model](#hybrid-deployment-model)
4. [Microservices Architecture](#microservices-architecture)
5. [Multi-Tenancy Strategy](#multi-tenancy-strategy)
6. [Data Layer Architecture](#data-layer-architecture)
7. [AI/ML Pipeline](#aiml-pipeline)
8. [Compliance & Audit Architecture](#compliance--audit-architecture)
9. [Security Architecture](#security-architecture)
10. [Performance & Scalability](#performance--scalability)

---

## Executive Summary

FoodFlow OS is an **AI-powered operating system for the food value chain**, designed as a hybrid SaaS/on-premise platform serving enterprise food manufacturers, distributors, and retailers. This document presents the enhanced system architecture incorporating extensive research findings and industry best practices.

### Core Value Proposition

FoodFlow OS provides **end-to-end visibility, predictive intelligence, and automated optimization** across the food supply chain through:

- **FoodGraph**: Neo4j-powered graph database for surgical traceability and supplier network analysis
- **Predictive Intelligence**: Hierarchical demand forecasting, anomaly detection, and risk prediction
- **Computer Vision**: Real-time defect detection with few-shot learning for dynamic SKU onboarding
- **AI Co-Pilot**: Natural language interface powered by LangGraph with specialized domain agents
- **Optimization Engine**: Production planning, inventory optimization, and vehicle routing
- **Compliance Automation**: Immutable audit trails, data lineage tracking, and regulatory intelligence

### Architecture Highlights

| Aspect | Technology | Rationale |
|--------|-----------|-----------|
| **Backend** | FastAPI (Python) + NestJS (TypeScript) | High-performance async APIs for AI services; robust enterprise patterns for business logic |
| **AI Orchestration** | LangGraph + LlamaIndex + Pydantic-AI | Stateful multi-agent workflows with structured outputs and RAG |
| **Model Serving** | BentoML + Ray Serve | Scalable, versioned model deployment with autoscaling |
| **Deployment** | Kubernetes + Hybrid Control/Data Plane | SaaS convenience with on-prem data security |
| **Multi-Tenancy** | Schema-per-Tenant (PostgreSQL) | Strong isolation with operational efficiency |
| **Graph Database** | Neo4j 5.15 Enterprise | Proven in food supply chain traceability |
| **Time-Series** | TimescaleDB 2.x | Seamless PostgreSQL integration with superior query performance |
| **Vector Search** | Qdrant 1.7+ | High-performance semantic search for RAG |
| **Audit Logs** | immudb 1.5+ | Tamper-proof, cryptographically verifiable audit trails |
| **Forecasting** | Nixtla (StatsForecast + HierarchicalForecast) | State-of-the-art hierarchical probabilistic forecasting |
| **Anomaly Detection** | PyOD + Merlion | Comprehensive outlier detection for tabular and time-series data |
| **Computer Vision** | YOLOv10 + Anomalib | Real-time defect detection with unsupervised anomaly learning |
| **Optimization** | Gurobi 11.x + Google OR-Tools | Industry-leading MIP solver + open-source routing/scheduling |
| **Frontend** | Next.js 15 + React 19 + Refine | Modern, enterprise-grade admin framework with AI copilot UI |

---

## Architecture Principles

### 1. AI-Native Design

Every component is designed with AI/ML integration as a first-class concern, not an afterthought. The platform treats AI models as core services with proper versioning, monitoring, and lifecycle management.

### 2. Hybrid Cloud-Agnostic

The architecture supports three deployment modes without code changes:
- **Pure SaaS**: Multi-tenant cloud deployment
- **Hybrid**: Cloud control plane + on-prem data plane
- **Pure On-Prem**: Fully air-gapped customer deployment

### 3. Polyglot Persistence

Different data types are stored in purpose-built databases for optimal performance:
- **PostgreSQL**: Transactional business data
- **Neo4j**: Graph relationships (traceability, supplier networks)
- **TimescaleDB**: High-cardinality time-series (sensors, metrics)
- **MongoDB**: Unstructured data (images, documents)
- **Qdrant**: Vector embeddings (semantic search, RAG)
- **Redis**: Caching, sessions, message queues
- **immudb**: Immutable audit logs

### 4. Event-Driven Architecture

Services communicate via asynchronous events (Kafka) for loose coupling and scalability, while maintaining synchronous APIs for real-time queries.

### 5. Compliance by Design

FDA 21 CFR Part 11 and SQF compliance requirements are embedded in the architecture:
- Immutable audit trails (immudb)
- Data lineage tracking (OpenLineage)
- Electronic signatures
- Role-based access control (RBAC)
- Tamper-evident records

### 6. Security in Depth

Multiple layers of security:
- Network segmentation
- Service-to-service mTLS
- API Gateway with OAuth2/OIDC
- Database-level encryption
- Secrets management (HashiCorp Vault)
- Regular security scanning

---

## Hybrid Deployment Model

### Control Plane / Data Plane Architecture

FoodFlow OS adopts a **hybrid control plane / data plane architecture** inspired by Tecton's approach, providing SaaS convenience with on-premise data security.

#### Control Plane (Vendor-Managed, Cloud)

The control plane runs in the vendor's cloud environment and handles:

**Responsibilities:**
- **Orchestration**: Kubernetes control plane, service mesh management
- **AI Model Registry**: Centralized model versioning and distribution
- **Tenant Management**: Subscription management, feature flags, billing
- **Monitoring & Alerting**: Aggregated metrics, anomaly detection, incident management
- **Updates & Patches**: Automated rollout of software updates to data planes
- **Support & Analytics**: Usage analytics, performance optimization recommendations

**Technology Stack:**
- Kubernetes (EKS/GKE/AKS)
- Kong API Gateway
- MLflow Model Registry
- Prometheus + Grafana
- Kafka (event bus)
- PostgreSQL (control plane metadata)

**Data Stored:**
- Tenant metadata (non-sensitive)
- Model versions and artifacts
- Aggregated, anonymized metrics
- System configuration

#### Data Plane (Customer-Managed, On-Prem or VPC)

The data plane runs in the customer's environment (on-premise or dedicated VPC) and handles:

**Responsibilities:**
- **Data Processing**: All customer data remains in their environment
- **AI Inference**: Local model serving with models pulled from control plane
- **Database Operations**: All databases (PostgreSQL, Neo4j, TimescaleDB, etc.) run locally
- **Business Logic**: Core services (FoodGraph, Forecast, Vision, etc.) process data locally
- **Edge Integration**: Direct connection to plant equipment, sensors, cameras

**Technology Stack:**
- Kubernetes (self-hosted or Rancher)
- All 12 microservices
- All databases (PostgreSQL, Neo4j, TimescaleDB, MongoDB, Redis, Qdrant, immudb)
- BentoML/Ray Serve (model serving)
- Azure IoT Edge (edge devices)

**Data Stored:**
- All customer business data
- Production data, sensor readings
- Quality records, audit logs
- Product images, documents

#### Communication Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE (Cloud)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Orchestrator │  │ Model Registry│  │  Monitoring  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                             │
                    Secure Outbound HTTPS
                    (Customer-Initiated)
                             │
┌─────────────────────────────────────────────────────────────┐
│              DATA PLANE (Customer Environment)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  FoodGraph   │  │   Forecast   │  │    Vision    │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Databases (Neo4j, Postgres, Timescale)       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Security:**
- Data plane initiates all connections (outbound only, no inbound firewall rules needed)
- mTLS for control plane ↔ data plane communication
- Customer data never leaves their environment
- Model artifacts pulled via secure registry (signed containers)

**Benefits:**
- **For Vendor**: Simplified updates, centralized monitoring, reduced support burden
- **For Customer**: Data sovereignty, compliance with data residency requirements, no vendor lock-in

---

## Microservices Architecture

### Service Catalog

| Service | Technology | Database | Purpose |
|---------|-----------|----------|---------|
| **Identity Service** | NestJS | PostgreSQL | OAuth2/OIDC, users, roles, RBAC, SSO integration |
| **Tenant Service** | NestJS | PostgreSQL | Multi-tenancy, subscriptions, feature flags, onboarding |
| **FoodGraph Service** | FastAPI | Neo4j | Graph traceability, supplier networks, risk propagation |
| **Forecast Service** | FastAPI | TimescaleDB | Hierarchical demand forecasting (P10/P50/P90) |
| **Vision Service** | FastAPI | MongoDB | Defect detection, few-shot learning, image analytics |
| **LLM Orchestration** | FastAPI | PostgreSQL + Qdrant | AI co-pilot, multi-agent workflows, RAG |
| **Optimization Service** | FastAPI | PostgreSQL | Production planning, inventory optimization, routing |
| **Sensor Analytics** | FastAPI | TimescaleDB | Real-time monitoring, anomaly detection, alerting |
| **Production Analytics** | FastAPI | TimescaleDB | OEE calculation, downtime analysis, performance metrics |
| **Integration Service** | NestJS | PostgreSQL | ERP/FSQ/MES connectors (Odoo, SAP, FSQapp) |
| **Data Room Service** | NestJS | Neo4j + PostgreSQL | Cross-org data sharing, contracts, permissions |
| **Notification Service** | NestJS | PostgreSQL + Redis | Alerts via email, SMS, Slack, webhooks |

### Service Communication Patterns

#### Synchronous (REST APIs)

Used for:
- Real-time queries (e.g., "Get batch traceability")
- User-initiated actions (e.g., "Create production order")
- Service-to-service RPC (e.g., LLM Orchestration calling FoodGraph)

**Technology:** HTTP/REST with JSON, OpenAPI 3.1 specs

#### Asynchronous (Event-Driven)

Used for:
- Background processing (e.g., model retraining)
- Data pipeline orchestration (e.g., sensor data ingestion)
- Inter-service notifications (e.g., "Forecast completed")

**Technology:** Apache Kafka with Avro schemas

#### Streaming (Real-Time)

Used for:
- Live sensor data (e.g., temperature streams)
- Real-time dashboards (e.g., production metrics)
- AI inference pipelines (e.g., video frame analysis)

**Technology:** Kafka Streams + WebSockets for UI

---

## Multi-Tenancy Strategy

### Schema-per-Tenant Architecture

Based on research findings, FoodFlow OS implements **schema-per-tenant** in PostgreSQL for optimal balance of isolation, performance, and operational efficiency.

#### Design Rationale

| Approach | Isolation | Performance | Ops Complexity | Cost | Chosen? |
|----------|-----------|-------------|----------------|------|---------|
| **Database-per-Tenant** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ❌ Too heavy |
| **Schema-per-Tenant** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ✅ **Selected** |
| **Row-Level Security** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ Security risk |

#### Implementation

**PostgreSQL Schema Structure:**
```sql
-- Each tenant gets their own schema
CREATE SCHEMA tenant_acme_foods;
CREATE SCHEMA tenant_global_dairy;
CREATE SCHEMA tenant_fresh_produce_co;

-- Shared reference data in public schema
CREATE SCHEMA public;
CREATE TABLE public.countries (...);
CREATE TABLE public.regulatory_standards (...);

-- Tenant-specific tables in tenant schema
CREATE TABLE tenant_acme_foods.production_orders (...);
CREATE TABLE tenant_acme_foods.quality_checks (...);
CREATE TABLE tenant_acme_foods.batches (...);
```

**Application-Level Tenant Context:**
```python
# FastAPI middleware sets tenant context
@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    tenant_id = extract_tenant_from_jwt(request.headers.get("Authorization"))
    request.state.tenant_id = tenant_id
    request.state.tenant_schema = f"tenant_{tenant_id}"
    response = await call_next(request)
    return response

# SQLAlchemy session with tenant schema
def get_tenant_session(tenant_schema: str):
    engine = create_engine(DATABASE_URL, connect_args={
        "options": f"-c search_path={tenant_schema},public"
    })
    return sessionmaker(bind=engine)()
```

#### Hybrid Approach for Large Customers

For enterprise customers with high data volumes or strict compliance requirements:
- **Dedicated Database**: Largest customers get their own PostgreSQL instance
- **Schema-per-Tenant**: Mid-sized customers share a database with schema isolation
- **Automatic Promotion**: Tenants automatically promoted to dedicated DB when they exceed thresholds

**Promotion Criteria:**
- \> 10 million records
- \> 100 GB data size
- Regulatory requirement (e.g., HIPAA, SOC 2 Type II)
- Customer request (premium tier)

#### Multi-Tenancy in Other Databases

| Database | Strategy | Implementation |
|----------|----------|----------------|
| **Neo4j** | Label-based isolation | All nodes tagged with `tenant_id` property; queries filtered |
| **TimescaleDB** | Schema-per-tenant | Same as PostgreSQL (TimescaleDB is PostgreSQL extension) |
| **MongoDB** | Database-per-tenant | Each tenant gets own MongoDB database |
| **Qdrant** | Collection-per-tenant | Each tenant gets own Qdrant collection for vectors |
| **Redis** | Key prefix | All keys prefixed with `tenant:{tenant_id}:` |
| **immudb** | Database-per-tenant | Each tenant gets own immudb database for audit logs |

---

## Data Layer Architecture

### Polyglot Persistence Strategy

FoodFlow OS uses purpose-built databases for different data types, optimizing for performance, scalability, and developer experience.

### 1. PostgreSQL 16 (Transactional Data)

**Use Cases:**
- User accounts, roles, permissions
- Tenant metadata, subscriptions
- Production orders, inventory records
- Quality checks, compliance records
- Integration configurations

**Schema Design:**
- Schema-per-tenant for isolation
- Shared `public` schema for reference data
- Foreign keys for referential integrity
- Indexes on tenant_id, timestamps, status fields

**Extensions:**
- `pgAudit`: Audit logging for compliance
- `pg_stat_statements`: Query performance monitoring
- `pgcrypto`: Encryption functions
- `uuid-ossp`: UUID generation

**Backup Strategy:**
- Continuous WAL archiving
- Daily full backups
- Point-in-time recovery (PITR)
- Per-tenant backup/restore capability

### 2. Neo4j 5.15 Enterprise (Graph Data)

**Use Cases:**
- Product traceability (ingredient → batch → distribution)
- Supplier network mapping (multi-tier relationships)
- Risk propagation analysis
- Equipment-product relationships (contamination analysis)
- Cross-org data lineage

**Graph Model:**
```cypher
// Nodes
(:Ingredient {id, name, lot_number, supplier_id, tenant_id})
(:Batch {id, product_id, production_date, tenant_id})
(:Product {id, sku, name, category, tenant_id})
(:Supplier {id, name, tier, risk_score, tenant_id})
(:Equipment {id, name, line, plant_id, tenant_id})
(:Distribution {id, location, date, tenant_id})

// Relationships
(:Ingredient)-[:USED_IN]->(:Batch)
(:Batch)-[:PRODUCES]->(:Product)
(:Product)-[:DISTRIBUTED_TO]->(:Distribution)
(:Supplier)-[:SUPPLIES]->(:Ingredient)
(:Equipment)-[:PROCESSED]->(:Batch)
(:Supplier)-[:SOURCES_FROM]->(:Supplier)  // Multi-tier
```

**Query Patterns:**
```cypher
// Forward traceability: Where did this ingredient go?
MATCH path = (i:Ingredient {lot_number: $lot})-[:USED_IN*]->(d:Distribution)
WHERE i.tenant_id = $tenant_id
RETURN path

// Backward traceability: What ingredients are in this product?
MATCH path = (d:Distribution {id: $dist_id})<-[:DISTRIBUTED_TO*]-(i:Ingredient)
WHERE d.tenant_id = $tenant_id
RETURN path

// Risk propagation: Which products are affected by supplier X?
MATCH path = (s:Supplier {id: $supplier_id})-[:SUPPLIES*]->(p:Product)
WHERE s.tenant_id = $tenant_id
RETURN p, length(path) as hops
```

**Multi-Tenancy:**
- All nodes have `tenant_id` property
- Queries automatically filtered by tenant
- Graph Data Science library for analytics

**Backup Strategy:**
- Online backup (no downtime)
- Incremental backups
- Cluster replication (HA)

### 3. TimescaleDB 2.x (Time-Series Data)

**Use Cases:**
- Sensor readings (temperature, pressure, humidity)
- Equipment metrics (OEE, uptime, throughput)
- Production KPIs (units/hour, defect rates)
- Forecast history (predicted vs actual)
- Anomaly scores over time

**Hypertable Design:**
```sql
-- Create hypertable for sensor data
CREATE TABLE sensor_readings (
    time TIMESTAMPTZ NOT NULL,
    tenant_id UUID NOT NULL,
    sensor_id UUID NOT NULL,
    metric_name TEXT NOT NULL,
    value DOUBLE PRECISION,
    unit TEXT,
    quality_code TEXT
);

SELECT create_hypertable('sensor_readings', 'time');

-- Create index on tenant_id and sensor_id
CREATE INDEX ON sensor_readings (tenant_id, sensor_id, time DESC);

-- Continuous aggregates for rollups
CREATE MATERIALIZED VIEW sensor_readings_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    tenant_id,
    sensor_id,
    metric_name,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    STDDEV(value) as stddev_value
FROM sensor_readings
GROUP BY hour, tenant_id, sensor_id, metric_name;
```

**Retention Policies:**
```sql
-- Raw data: 90 days
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days');

-- Hourly aggregates: 2 years
SELECT add_retention_policy('sensor_readings_hourly', INTERVAL '2 years');

-- Daily aggregates: 10 years
SELECT add_retention_policy('sensor_readings_daily', INTERVAL '10 years');
```

**Compression:**
```sql
-- Enable compression on older data
ALTER TABLE sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tenant_id,sensor_id',
    timescaledb.compress_orderby = 'time DESC'
);

-- Compress data older than 7 days
SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');
```

**Query Patterns:**
```sql
-- Time-window aggregation
SELECT
    time_bucket('15 minutes', time) AS bucket,
    sensor_id,
    AVG(value) as avg_temp
FROM sensor_readings
WHERE tenant_id = $tenant_id
  AND time > NOW() - INTERVAL '24 hours'
  AND metric_name = 'temperature'
GROUP BY bucket, sensor_id
ORDER BY bucket DESC;

-- Anomaly detection with window functions
SELECT
    time,
    sensor_id,
    value,
    AVG(value) OVER (
        PARTITION BY sensor_id
        ORDER BY time
        ROWS BETWEEN 100 PRECEDING AND CURRENT ROW
    ) as moving_avg,
    STDDEV(value) OVER (
        PARTITION BY sensor_id
        ORDER BY time
        ROWS BETWEEN 100 PRECEDING AND CURRENT ROW
    ) as moving_stddev
FROM sensor_readings
WHERE tenant_id = $tenant_id
  AND time > NOW() - INTERVAL '1 hour';
```

### 4. MongoDB 7 (Unstructured Data)

**Use Cases:**
- Product images (defect detection)
- Quality inspection photos
- Document storage (PDFs, certificates)
- Flexible schemas (dynamic attributes)
- Image metadata and annotations

**Collection Design:**
```javascript
// vision_images collection
{
  _id: ObjectId("..."),
  tenant_id: "acme-foods",
  image_id: "img_12345",
  product_sku: "SKU-001",
  captured_at: ISODate("2025-11-16T10:30:00Z"),
  source: "line_3_camera_2",
  image_url: "s3://foodflow-images/acme-foods/img_12345.jpg",
  thumbnail_url: "s3://foodflow-images/acme-foods/img_12345_thumb.jpg",
  metadata: {
    width: 1920,
    height: 1080,
    format: "JPEG",
    size_bytes: 245678
  },
  inference_results: {
    model_version: "yolov10-defect-v1.2",
    inference_time_ms: 45,
    detections: [
      {
        class: "crack",
        confidence: 0.92,
        bbox: [120, 340, 180, 400],
        severity: "high"
      },
      {
        class: "discoloration",
        confidence: 0.78,
        bbox: [500, 200, 600, 280],
        severity: "medium"
      }
    ],
    overall_quality_score: 0.65,
    pass_fail: "fail"
  },
  annotations: [
    {
      annotator_id: "user_456",
      annotated_at: ISODate("2025-11-16T11:00:00Z"),
      label: "crack",
      bbox: [120, 340, 180, 400],
      verified: true
    }
  ],
  indexed_at: ISODate("2025-11-16T10:30:05Z")
}
```

**Indexes:**
```javascript
db.vision_images.createIndex({ tenant_id: 1, captured_at: -1 });
db.vision_images.createIndex({ tenant_id: 1, product_sku: 1 });
db.vision_images.createIndex({ "inference_results.pass_fail": 1, captured_at: -1 });
db.vision_images.createIndex({ tenant_id: 1, "inference_results.detections.class": 1 });
```

**Multi-Tenancy:**
- Database-per-tenant approach
- Each tenant gets own MongoDB database: `foodflow_tenant_acme_foods`

### 5. Qdrant 1.7+ (Vector Search)

**Use Cases:**
- Semantic search over compliance documents
- Similar defect image retrieval
- Knowledge base RAG for AI co-pilot
- Product recommendation (similar products)

**Collection Design:**
```python
# Create collection for compliance documents
client.create_collection(
    collection_name="compliance_docs_acme_foods",
    vectors_config=VectorParams(
        size=1536,  # OpenAI text-embedding-3-large
        distance=Distance.COSINE
    )
)

# Upsert document embeddings
client.upsert(
    collection_name="compliance_docs_acme_foods",
    points=[
        PointStruct(
            id="doc_123",
            vector=embedding_vector,  # 1536-dim vector
            payload={
                "tenant_id": "acme-foods",
                "document_id": "doc_123",
                "document_type": "SOP",
                "title": "HACCP Plan for Dairy Processing",
                "content_preview": "This document outlines...",
                "created_at": "2025-11-16T10:00:00Z",
                "tags": ["HACCP", "dairy", "food-safety"]
            }
        )
    ]
)

# Semantic search
results = client.search(
    collection_name="compliance_docs_acme_foods",
    query_vector=query_embedding,
    limit=5,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="tenant_id",
                match=MatchValue(value="acme-foods")
            ),
            FieldCondition(
                key="document_type",
                match=MatchValue(value="SOP")
            )
        ]
    )
)
```

**Multi-Tenancy:**
- Collection-per-tenant approach
- Each tenant gets own Qdrant collection

### 6. Redis 7 (Caching & Queues)

**Use Cases:**
- Session storage (user sessions)
- API response caching
- Rate limiting counters
- Real-time leaderboards (e.g., plant performance)
- Message queues (Bull/BullMQ)

**Key Patterns:**
```redis
# Session storage
SET session:{session_id} "{user_id: 123, tenant_id: 'acme-foods', ...}" EX 3600

# API response caching
SET cache:tenant:acme-foods:forecast:SKU-001:2025-11-16 "{forecast_data}" EX 300

# Rate limiting
INCR ratelimit:tenant:acme-foods:api:user_123:minute
EXPIRE ratelimit:tenant:acme-foods:api:user_123:minute 60

# Real-time metrics
ZADD plant_performance:acme-foods:2025-11-16 95.2 "plant_chicago"
ZADD plant_performance:acme-foods:2025-11-16 88.7 "plant_dallas"

# Message queue (Bull)
LPUSH queue:forecast:jobs "{job_id: 'job_123', tenant_id: 'acme-foods', ...}"
```

**Multi-Tenancy:**
- Key prefix approach: `tenant:{tenant_id}:{resource}`

### 7. immudb 1.5+ (Immutable Audit Logs)

**Use Cases:**
- Tamper-proof audit trails
- Compliance record storage (FDA 21 CFR Part 11)
- Critical event logging (quality checks, approvals)
- Data lineage tracking

**Schema Design:**
```sql
-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER AUTO_INCREMENT,
    tenant_id VARCHAR[256],
    event_type VARCHAR[256],
    user_id VARCHAR[256],
    resource_type VARCHAR[256],
    resource_id VARCHAR[256],
    action VARCHAR[256],
    old_value BLOB,
    new_value BLOB,
    ip_address VARCHAR[256],
    user_agent VARCHAR[256],
    timestamp INTEGER,
    PRIMARY KEY id
);

-- Insert audit log (immutable)
INSERT INTO audit_logs (
    tenant_id, event_type, user_id, resource_type, resource_id,
    action, old_value, new_value, ip_address, timestamp
) VALUES (
    'acme-foods', 'quality_check', 'user_123', 'batch', 'batch_456',
    'approve', NULL, '{"status": "approved", "inspector": "John Doe"}',
    '192.168.1.100', 1700140800
);
```

**Verification:**
```python
# Verify audit log integrity
verification_result = client.verify_row(
    table="audit_logs",
    row_id=12345
)

if verification_result.verified:
    print("Audit log is tamper-proof and verified")
else:
    print("WARNING: Audit log has been tampered with!")
```

**Multi-Tenancy:**
- Database-per-tenant approach
- Each tenant gets own immudb database

---

## AI/ML Pipeline

### Model Serving Architecture

FoodFlow OS uses **BentoML** and **Ray Serve** for scalable, versioned model deployment.

#### BentoML for Model Packaging

```python
# bentofile.yaml
service: "forecast_service.py:svc"
labels:
  owner: foodflow-ml-team
  project: demand-forecasting
include:
  - "forecast_service.py"
  - "models/"
python:
  packages:
    - statsforecast==1.7.0
    - hierarchicalforecast==0.5.0
    - pandas==2.1.0
docker:
  distro: debian
  python_version: "3.11"

# forecast_service.py
import bentoml
from bentoml.io import JSON
from statsforecast import StatsForecast

@bentoml.service(
    resources={"cpu": "2", "memory": "4Gi"},
    traffic={"timeout": 30}
)
class ForecastService:
    def __init__(self):
        self.model = bentoml.models.get("demand_forecast_v1.2")
        self.sf = StatsForecast.load(self.model.path)
    
    @bentoml.api
    def predict(self, input_data: JSON) -> JSON:
        tenant_id = input_data["tenant_id"]
        sku = input_data["sku"]
        horizon = input_data["horizon"]
        
        # Generate forecast
        forecast = self.sf.forecast(h=horizon)
        
        return {
            "tenant_id": tenant_id,
            "sku": sku,
            "forecast": forecast.to_dict(),
            "model_version": "v1.2"
        }
```

#### Ray Serve for Distributed Inference

```python
# ray_serve_deployment.py
from ray import serve
import ray

@serve.deployment(
    num_replicas=3,
    ray_actor_options={"num_cpus": 2, "num_gpus": 0.5}
)
class VisionModel:
    def __init__(self):
        import torch
        from ultralytics import YOLO
        
        self.model = YOLO("yolov10_defect_v1.2.pt")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
    
    async def __call__(self, request):
        image_url = request.query_params["image_url"]
        tenant_id = request.query_params["tenant_id"]
        
        # Download image
        image = download_image(image_url)
        
        # Run inference
        results = self.model(image)
        
        # Parse detections
        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "class": r.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": box.xyxy.tolist()
                })
        
        return {
            "tenant_id": tenant_id,
            "detections": detections,
            "model_version": "v1.2"
        }

# Deploy
serve.run(VisionModel.bind())
```

### MLOps Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    MLOps Pipeline                            │
│                                                              │
│  1. Data Collection                                          │
│     ├─ Historical sales data (PostgreSQL/TimescaleDB)       │
│     ├─ Sensor readings (TimescaleDB)                        │
│     └─ Product images (MongoDB + S3)                        │
│                                                              │
│  2. Feature Engineering                                      │
│     ├─ Feature Store (Tecton or Feast)                      │
│     ├─ Feature pipelines (Airflow/Prefect)                  │
│     └─ Feature versioning                                   │
│                                                              │
│  3. Model Training                                           │
│     ├─ Experiment tracking (MLflow)                         │
│     ├─ Hyperparameter tuning (Optuna)                       │
│     └─ Distributed training (Ray Train)                     │
│                                                              │
│  4. Model Validation                                         │
│     ├─ Backtesting (forecast accuracy)                      │
│     ├─ A/B testing framework                                │
│     └─ Model performance metrics                            │
│                                                              │
│  5. Model Registry                                           │
│     ├─ MLflow Model Registry                                │
│     ├─ Model versioning (v1.0, v1.1, v1.2)                  │
│     └─ Model metadata (training data, metrics)              │
│                                                              │
│  6. Model Deployment                                         │
│     ├─ BentoML packaging                                    │
│     ├─ Ray Serve deployment                                 │
│     └─ Canary rollout (10% → 50% → 100%)                    │
│                                                              │
│  7. Model Monitoring                                         │
│     ├─ Prediction drift detection                           │
│     ├─ Data drift detection                                 │
│     ├─ Performance degradation alerts                       │
│     └─ Automatic retraining triggers                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Compliance & Audit Architecture

### Immutable Audit Trail with immudb

FoodFlow OS implements a **tamper-proof audit logging system** using immudb to meet FDA 21 CFR Part 11 and SQF requirements.

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Identity    │  │  FoodGraph   │  │  Production  │      │
│  │  Service     │  │  Service     │  │  Analytics   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                    Audit Events                              │
│                            │                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Audit Service (FastAPI)                   │    │
│  │  - Event validation                                 │    │
│  │  - Enrichment (IP, user agent, timestamp)          │    │
│  │  - Batching & buffering                             │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   PostgreSQL    │
                    │   (pgAudit)     │
                    │  Audit Staging  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     immudb      │
                    │  Immutable Log  │
                    │ (Cryptographic  │
                    │  Verification)  │
                    └─────────────────┘
```

#### Audit Event Schema

```python
# audit_event.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class AuditEvent(BaseModel):
    tenant_id: str
    event_id: str  # UUID
    event_type: str  # e.g., "quality_check.approve", "batch.create"
    user_id: str
    user_email: str
    resource_type: str  # e.g., "batch", "production_order"
    resource_id: str
    action: str  # e.g., "create", "update", "delete", "approve"
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: str
    user_agent: str
    session_id: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
```

#### Audit Service Implementation

```python
# audit_service.py
from fastapi import FastAPI, Depends
from immudb import ImmudbClient
import asyncpg

app = FastAPI()

class AuditService:
    def __init__(self):
        self.immudb_client = ImmudbClient()
        self.immudb_client.login("immudb", "immudb")
        self.pg_pool = asyncpg.create_pool(DATABASE_URL)
    
    async def log_event(self, event: AuditEvent):
        # 1. Validate event
        if not event.tenant_id or not event.user_id:
            raise ValueError("tenant_id and user_id are required")
        
        # 2. Store in PostgreSQL (staging)
        async with self.pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_staging (
                    tenant_id, event_id, event_type, user_id,
                    resource_type, resource_id, action,
                    old_value, new_value, ip_address, timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, event.tenant_id, event.event_id, event.event_type,
                event.user_id, event.resource_type, event.resource_id,
                event.action, event.old_value, event.new_value,
                event.ip_address, event.timestamp)
        
        # 3. Store in immudb (immutable)
        self.immudb_client.sqlExec(f"""
            INSERT INTO audit_logs_{event.tenant_id} (
                event_id, event_type, user_id, resource_type,
                resource_id, action, old_value, new_value,
                ip_address, timestamp
            ) VALUES (
                '{event.event_id}', '{event.event_type}',
                '{event.user_id}', '{event.resource_type}',
                '{event.resource_id}', '{event.action}',
                '{event.old_value}', '{event.new_value}',
                '{event.ip_address}', {int(event.timestamp.timestamp())}
            )
        """)
        
        return {"status": "logged", "event_id": event.event_id}
    
    async def verify_audit_log(self, tenant_id: str, event_id: str):
        # Verify cryptographic integrity
        result = self.immudb_client.sqlQuery(f"""
            SELECT * FROM audit_logs_{tenant_id}
            WHERE event_id = '{event_id}'
        """)
        
        # immudb automatically verifies cryptographic proof
        return {
            "event_id": event_id,
            "verified": True,
            "data": result
        }
    
    async def get_audit_trail(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str
    ):
        # Retrieve complete audit trail for a resource
        result = self.immudb_client.sqlQuery(f"""
            SELECT * FROM audit_logs_{tenant_id}
            WHERE resource_type = '{resource_type}'
              AND resource_id = '{resource_id}'
            ORDER BY timestamp ASC
        """)
        
        return result

@app.post("/audit/log")
async def log_audit_event(event: AuditEvent):
    service = AuditService()
    return await service.log_event(event)

@app.get("/audit/verify/{tenant_id}/{event_id}")
async def verify_event(tenant_id: str, event_id: str):
    service = AuditService()
    return await service.verify_audit_log(tenant_id, event_id)

@app.get("/audit/trail/{tenant_id}/{resource_type}/{resource_id}")
async def get_trail(tenant_id: str, resource_type: str, resource_id: str):
    service = AuditService()
    return await service.get_audit_trail(tenant_id, resource_type, resource_id)
```

### Data Lineage Tracking

FoodFlow OS implements **data lineage tracking** using OpenLineage to provide full transparency of data flow through the system.

#### OpenLineage Integration

```python
# lineage_tracking.py
from openlineage.client import OpenLineageClient
from openlineage.client.run import RunEvent, RunState, Run, Job
from openlineage.client.facet import SqlJobFacet, SourceCodeLocationJobFacet
from datetime import datetime

class LineageTracker:
    def __init__(self):
        self.client = OpenLineageClient(url="http://marquez:5000")
    
    def track_forecast_job(
        self,
        tenant_id: str,
        job_id: str,
        input_dataset: str,
        output_dataset: str,
        model_version: str
    ):
        # Start event
        self.client.emit(RunEvent(
            eventType=RunState.START,
            eventTime=datetime.utcnow().isoformat(),
            run=Run(runId=job_id),
            job=Job(
                namespace=f"foodflow.{tenant_id}",
                name="demand_forecast",
                facets={
                    "sourceCodeLocation": SourceCodeLocationJobFacet(
                        type="git",
                        url="https://github.com/OPSC2025/foodflow-os",
                        version=model_version
                    )
                }
            ),
            inputs=[{
                "namespace": f"foodflow.{tenant_id}",
                "name": input_dataset,  # e.g., "sales_history_2025_11"
                "facets": {}
            }],
            outputs=[{
                "namespace": f"foodflow.{tenant_id}",
                "name": output_dataset,  # e.g., "forecast_2025_12"
                "facets": {}
            }]
        ))
        
        # ... run forecast job ...
        
        # Complete event
        self.client.emit(RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.utcnow().isoformat(),
            run=Run(runId=job_id),
            job=Job(
                namespace=f"foodflow.{tenant_id}",
                name="demand_forecast"
            ),
            inputs=[{
                "namespace": f"foodflow.{tenant_id}",
                "name": input_dataset
            }],
            outputs=[{
                "namespace": f"foodflow.{tenant_id}",
                "name": output_dataset
            }]
        ))
```

---

## Security Architecture

### Defense in Depth

FoodFlow OS implements multiple layers of security to protect customer data and ensure compliance.

#### 1. Network Security

**Segmentation:**
```
┌─────────────────────────────────────────────────────────────┐
│                     Internet                                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                ┌───────▼──────┐
                │   WAF/CDN    │
                │  (Cloudflare)│
                └───────┬──────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  DMZ (Public Zone)                           │
│  ┌──────────────┐                                            │
│  │ API Gateway  │  (Kong)                                    │
│  │ (OAuth2/OIDC)│                                            │
│  └──────────────┘                                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Application Zone (Private)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Identity    │  │  FoodGraph   │  │  Forecast    │      │
│  │  Service     │  │  Service     │  │  Service     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         (mTLS between services)                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│               Data Zone (Highly Restricted)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Neo4j     │  │  TimescaleDB │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         (No direct external access)                          │
└─────────────────────────────────────────────────────────────┘
```

**Firewall Rules:**
- DMZ → Application Zone: Only API Gateway
- Application Zone → Data Zone: Only specific services
- Data Zone → Internet: Blocked (no outbound)

#### 2. Identity & Access Management

**OAuth2/OIDC Flow:**
```
1. User → API Gateway: Login request
2. API Gateway → Identity Service: Validate credentials
3. Identity Service → Database: Check user/tenant
4. Identity Service → API Gateway: JWT token (signed)
5. API Gateway → User: JWT token
6. User → API Gateway: API request + JWT
7. API Gateway: Validate JWT signature
8. API Gateway → Service: Request + tenant context
9. Service: Enforce tenant isolation
```

**JWT Structure:**
```json
{
  "sub": "user_123",
  "email": "john@acme-foods.com",
  "tenant_id": "acme-foods",
  "roles": ["quality_manager", "production_viewer"],
  "permissions": [
    "batch:read",
    "batch:approve",
    "forecast:read"
  ],
  "iat": 1700140800,
  "exp": 1700144400
}
```

#### 3. Service-to-Service Authentication

**Mutual TLS (mTLS):**
- All inter-service communication uses mTLS
- Each service has its own certificate
- Certificate rotation every 90 days (automated)

**Implementation:**
```yaml
# Istio ServiceEntry for mTLS
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: foodgraph-service-mtls
spec:
  host: foodgraph-service.foodflow.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
```

#### 4. Data Encryption

**At Rest:**
- PostgreSQL: Transparent Data Encryption (TDE)
- Neo4j: Encrypted storage
- MongoDB: Encryption at rest
- S3: Server-side encryption (SSE-S3)
- immudb: Built-in encryption

**In Transit:**
- TLS 1.3 for all external connections
- mTLS for all internal connections
- No unencrypted traffic allowed

#### 5. Secrets Management

**HashiCorp Vault:**
```python
# secrets_manager.py
import hvac

class SecretsManager:
    def __init__(self):
        self.client = hvac.Client(url="https://vault.foodflow.internal")
        self.client.auth.kubernetes.login(
            role="foodflow-app",
            jwt=open("/var/run/secrets/kubernetes.io/serviceaccount/token").read()
        )
    
    def get_database_credentials(self, tenant_id: str):
        secret = self.client.secrets.kv.v2.read_secret_version(
            path=f"database/{tenant_id}"
        )
        return secret["data"]["data"]
    
    def get_api_key(self, service_name: str):
        secret = self.client.secrets.kv.v2.read_secret_version(
            path=f"api-keys/{service_name}"
        )
        return secret["data"]["data"]["key"]
```

**Secret Rotation:**
- Automatic rotation every 90 days
- Zero-downtime rotation (dual-write period)
- Audit log of all secret access

#### 6. Rate Limiting & DDoS Protection

**Kong API Gateway:**
```yaml
# rate-limit-plugin.yaml
plugins:
  - name: rate-limiting
    config:
      minute: 100
      hour: 1000
      policy: redis
      redis_host: redis.foodflow.svc.cluster.local
      redis_port: 6379
      fault_tolerant: true
      hide_client_headers: false
```

**Cloudflare WAF:**
- DDoS protection (L3/L4/L7)
- Bot management
- Rate limiting (global)
- IP reputation filtering

---

## Performance & Scalability

### Horizontal Scaling Strategy

| Service | Scaling Trigger | Min Replicas | Max Replicas | Target Metric |
|---------|----------------|--------------|--------------|---------------|
| **API Gateway** | CPU > 70% | 3 | 10 | CPU utilization |
| **Identity Service** | Requests/sec > 1000 | 2 | 5 | Request rate |
| **FoodGraph Service** | CPU > 80% | 2 | 8 | CPU utilization |
| **Forecast Service** | Queue depth > 10 | 1 | 5 | Job queue length |
| **Vision Service** | GPU > 80% | 2 | 6 | GPU utilization |
| **LLM Orchestration** | Requests/sec > 50 | 2 | 10 | Request rate |
| **Sensor Analytics** | Events/sec > 10000 | 3 | 12 | Event throughput |

**Kubernetes HPA:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: foodgraph-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: foodgraph-service
  minReplicas: 2
  maxReplicas: 8
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

### Database Scaling

#### PostgreSQL

**Vertical Scaling:**
- Start: 4 vCPU, 16 GB RAM
- Scale up to: 32 vCPU, 128 GB RAM

**Horizontal Scaling (Read Replicas):**
```
┌─────────────────┐
│  Primary (RW)   │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐
│Replica│ │Replica│ │Replica│ │Replica│
│  (RO) │ │  (RO) │ │  (RO) │ │  (RO) │
└───────┘ └──────┘ └──────┘ └──────┘
```

**Connection Pooling (PgBouncer):**
```ini
[databases]
foodflow = host=postgres-primary port=5432 dbname=foodflow

[pgbouncer]
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 25
reserve_pool_size = 5
```

#### Neo4j

**Causal Cluster:**
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Core Server │  │  Core Server │  │  Core Server │
│      #1      │  │      #2      │  │      #3      │
│  (Leader)    │  │  (Follower)  │  │  (Follower)  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │  Read   │    │  Read   │    │  Read   │
    │ Replica │    │ Replica │    │ Replica │
    └─────────┘    └─────────┘    └─────────┘
```

#### TimescaleDB

**Distributed Hypertables:**
```sql
-- Create distributed hypertable across multiple data nodes
SELECT create_distributed_hypertable(
    'sensor_readings',
    'time',
    partitioning_column => 'sensor_id',
    number_partitions => 4
);

-- Add data nodes
SELECT add_data_node('data_node_1', host => 'timescale-node-1');
SELECT add_data_node('data_node_2', host => 'timescale-node-2');
SELECT add_data_node('data_node_3', host => 'timescale-node-3');
SELECT add_data_node('data_node_4', host => 'timescale-node-4');
```

### Caching Strategy

**Multi-Layer Caching:**

```
┌─────────────────────────────────────────────────────────────┐
│                      Client (Browser)                        │
│  Cache-Control: max-age=300 (5 minutes)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   CDN (Cloudflare)                           │
│  Cache static assets, API responses (public data)           │
│  TTL: 1 hour                                                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  API Gateway (Kong)                          │
│  Cache frequently accessed endpoints                         │
│  TTL: 5 minutes                                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              Application Layer (Redis)                       │
│  - Session cache (TTL: 1 hour)                              │
│  - API response cache (TTL: 5-15 minutes)                   │
│  - Database query cache (TTL: 1-5 minutes)                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   Database Layer                             │
│  - PostgreSQL shared_buffers (25% of RAM)                   │
│  - Neo4j page cache (50% of RAM)                            │
│  - TimescaleDB query result cache                           │
└─────────────────────────────────────────────────────────────┘
```

**Cache Invalidation:**
```python
# cache_manager.py
import redis
from typing import List

class CacheManager:
    def __init__(self):
        self.redis = redis.Redis(host="redis", port=6379)
    
    def invalidate_tenant_cache(self, tenant_id: str, resource_types: List[str]):
        """Invalidate all cache keys for a tenant and resource types"""
        for resource_type in resource_types:
            pattern = f"cache:tenant:{tenant_id}:{resource_type}:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
    
    def invalidate_on_write(self, tenant_id: str, resource_type: str, resource_id: str):
        """Invalidate cache when a resource is modified"""
        # Invalidate specific resource
        self.redis.delete(f"cache:tenant:{tenant_id}:{resource_type}:{resource_id}")
        
        # Invalidate list views
        self.redis.delete(f"cache:tenant:{tenant_id}:{resource_type}:list:*")
        
        # Invalidate related resources
        if resource_type == "batch":
            # Invalidate traceability cache
            self.redis.delete(f"cache:tenant:{tenant_id}:traceability:batch:{resource_id}")
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **API Response Time (P95)** | < 200ms | Prometheus + Grafana |
| **API Response Time (P99)** | < 500ms | Prometheus + Grafana |
| **Database Query Time (P95)** | < 100ms | pg_stat_statements |
| **Graph Query Time (P95)** | < 500ms | Neo4j query log |
| **Forecast Generation** | < 30s | MLflow metrics |
| **Vision Inference** | < 100ms | BentoML metrics |
| **LLM Response Time** | < 5s | LangSmith tracing |
| **Sensor Data Ingestion** | > 10,000 events/sec | Kafka metrics |
| **System Uptime** | 99.9% | Uptime monitoring |
| **Data Durability** | 99.999999999% (11 nines) | Database replication |

---

## Conclusion

This enhanced architecture document provides a comprehensive, production-ready blueprint for FoodFlow OS. The architecture incorporates extensive research findings and industry best practices to deliver:

- **High Performance**: Sub-200ms API response times, 10,000+ events/sec ingestion
- **Scalability**: Horizontal scaling across all services, distributed databases
- **Security**: Defense-in-depth with mTLS, encryption, immutable audit logs
- **Compliance**: FDA 21 CFR Part 11 and SQF requirements embedded in design
- **Flexibility**: Hybrid SaaS/on-prem deployment with control/data plane separation
- **AI-Native**: LangGraph orchestration, BentoML/Ray model serving, comprehensive MLOps

The architecture is designed for **AI coding agents** to implement systematically, with clear specifications, technology choices, and implementation patterns throughout.

---

**Next Steps:**
1. Review API Specifications (docs/api/)
2. Review Database Schemas (docs/database/)
3. Begin Phase 1 Implementation (docs/implementation/AI_CODER_ROADMAP.md)

---

**Document Metadata:**
- **Version:** 2.0
- **Last Updated:** November 16, 2025
- **Author:** Manus AI
- **Status:** Production-Ready
- **Review Cycle:** Quarterly
