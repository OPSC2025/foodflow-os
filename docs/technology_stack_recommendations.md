# FoodFlow OS: Technology Stack Recommendations

**Date:** November 16, 2025  
**Based on:** Extensive research across 15+ sources and frameworks

---

## Executive Summary

This document consolidates research findings across all critical technology areas for FoodFlow OS and provides definitive recommendations for the production technology stack. All recommendations are based on November 2025 state-of-the-art technologies, proven at scale in enterprise environments.

---

## 1. Graph Database: Neo4j

**Decision:** Neo4j Enterprise Edition

**Rationale:**
- Most mature graph database with strongest ecosystem
- Excels at read-heavy workloads (critical for traceability queries)
- Native graph processing engine (faster than multi-model databases)
- Battle-tested in enterprise environments (eBay, VISA, Intuit)
- Cypher query language is intuitive and SQL-like
- Best integration with enterprise tools and frameworks

**Multi-Tenancy Strategy:**
- Separate Neo4j database per organization (complete data isolation)
- Shared "network graph" database for cross-org relationships (data rooms)
- Application-level access control for fine-grained permissions

**Alternative Considered:** ArangoDB (multi-model, better multi-tenancy support, but less mature graph features)

**Use Cases in FoodFlow OS:**
- FoodGraph (product relationships, batch/lot traceability)
- Supplier networks and risk propagation
- Recall path computation (forward/backward tracing)
- Digital twin relationships

---

## 2. Time-Series Forecasting: Nixtla Ecosystem

**Decision:** StatsForecast + HierarchicalForecast + NeuralForecast

**Rationale:**
- Native hierarchical forecasting with reconciliation (critical for SKU × Location × Time hierarchies)
- Probabilistic forecasts (P10, P50, P90) for risk management
- Optimized for high performance and scalability (thousands of SKUs)
- Active development (v1.3.1 released November 2025)
- Apache 2.0 license, strong community
- Easy integration with pandas and feature stores

**Forecasting Hierarchy:**
```
Total (All Products, All Locations)
├── By Brand
│   ├── By Category
│   │   ├── By Product
│   │   │   └── By SKU
│   │   │       └── By Location
│   │   │           └── By Channel
```

**Reconciliation Methods:**
- MinTrace (primary): Minimizes total forecast variance
- BottomUp (fallback): Simple aggregation
- TopDown (for top-level constraints): Distributes forecasts

**Alternatives Considered:**
- Prophet (Meta): Good for single series, lacks hierarchical reconciliation
- Darts: More complex API, heavier dependencies

**Use Cases in FoodFlow OS:**
- Demand forecasting (SKU-level, location-level, brand-level)
- Inventory optimization (safety stock, reorder points)
- Production planning (capacity requirements)
- Supply chain risk (supplier disruption probability)

---

## 3. Edge Computing: Azure IoT Edge

**Decision:** Azure IoT Edge + ONNX Runtime

**Rationale:**
- Enterprise-grade with strong security and compliance
- Container-based deployment (Docker) for easy updates
- Native AI/ML support (ONNX runtime, GPU acceleration)
- Built-in OPC UA module for PLC/SCADA integration
- Offline capabilities (store-and-forward messaging)
- Centralized device management and fleet-wide updates
- Best integration with Azure ML for model training/deployment

**Edge Hardware:**
- Industrial PCs: Advantech ARK series or Axiomtek eBOX
- CPU: Intel Core i7 or AMD Ryzen 7 (8+ cores)
- RAM: 32GB DDR4/DDR5
- GPU: NVIDIA Jetson AGX Orin (for vision inference)
- Storage: 512GB NVMe SSD
- Connectivity: Ethernet, Wi-Fi 6, 4G/5G backup
- Operating Temperature: -20°C to 60°C (industrial grade)

**OPC UA Integration:**
- Advantech WISE-PaaS or HMS Anybus X-gateway
- Connects to PLCs, SCADA, MES systems
- Standard industrial protocol

**Alternatives Considered:**
- AWS IoT Greengrass: Similar capabilities, better if using AWS ecosystem
- ClearBlade: Purpose-built for industrial IoT, smaller ecosystem

**Use Cases in FoodFlow OS:**
- Real-time vision inspection (defect detection)
- Sensor data aggregation and anomaly detection
- Local inference (ONNX models)
- Store-and-forward to cloud when connectivity is limited

---

## 4. Computer Vision: YOLOv10 + Few-Shot Learning

**Decision:** YOLOv10 for defect detection + Few-Shot Learning for dynamic SKU onboarding

**Rationale:**
- YOLOv10 offers best speed/accuracy tradeoff for real-time inspection
- Outperforms Mask R-CNN in speed (critical for production lines)
- Few-shot learning enables rapid onboarding of new SKUs (N=5-10 images)
- ONNX export for edge deployment
- Active development and strong community

**Model Architecture:**
- YOLOv10n (nano) for edge devices with limited compute
- YOLOv10s (small) for standard industrial PCs
- YOLOv10m (medium) for high-accuracy applications

**Few-Shot Learning Approach:**
- Operator captures 5-10 images of good + defective product
- Label with simple UI (FoodFlow OS orchestrates)
- Fine-tune YOLOv10 backbone on edge or in cloud
- Deploy updated model to edge via Azure IoT Edge
- Entire pipeline automated by FoodFlow OS

**Alternatives Considered:**
- Mask R-CNN: Higher accuracy but slower (not suitable for real-time)
- Faster R-CNN: Two-stage, better for small/overlapping objects but slower

**Use Cases in FoodFlow OS:**
- Automated visual inspection (burns, breaks, underfill, contamination)
- Label verification (OCR + object detection)
- Packaging defect detection
- Dynamic SKU onboarding (few-shot learning)

---

## 5. Optimization: Gurobi + Google OR-Tools

**Decision:** Gurobi for production planning, Google OR-Tools for routing

**Rationale:**
- Gurobi: Market-leading performance for large MIPs, clean Python API, free academic licenses
- OR-Tools: Free, open-source, excels at routing problems (VRP, TSP)
- Both integrate seamlessly with Python and modern MLOps stacks

**Use Cases:**
- **Gurobi:**
  - Production planning and scheduling
  - Inventory optimization
  - Capacity planning
  - Supply-demand matching

- **OR-Tools:**
  - Vehicle routing (distribution optimization)
  - Delivery route optimization
  - Warehouse picking optimization

**Alternatives Considered:**
- CPLEX: Similar performance to Gurobi, more expensive
- PuLP: Free but limited performance for large problems
- Pyomo: Flexible but more boilerplate code

**Deployment:**
- Optimization Service API (FastAPI)
- Containerized (Docker)
- Scheduled optimization runs (daily, weekly)
- Real-time optimization for urgent scenarios

---

## 6. LLM Orchestration: LangGraph

**Decision:** LangGraph (primary) + Pydantic-AI (validation)

**Rationale:**
- Robust state management with PostgreSQL checkpointing (critical for production)
- Asynchronous operations and distributed systems support
- Graph-based workflow design (matches FoodFlow OS complexity)
- Best for complex, stateful workflows with conditional logic
- Strong integration with LangChain ecosystem
- Production-ready with proven deployment patterns

**Architecture:**
```
LangGraph Workflow
├── Supervisor Node (routes queries)
├── Specialized Agent Nodes
│   ├── FoodGraph Agent (Neo4j queries)
│   ├── Forecast Agent (demand predictions)
│   ├── Vision Agent (defect analysis)
│   ├── Compliance Agent (regulatory Q&A)
│   └── Optimization Agent (production planning)
├── Tool Nodes (function calling)
└── Human-in-the-Loop Nodes (approval gates)
```

**Why Not CrewAI:**
- Better for role-based collaboration (less relevant for FoodFlow OS)
- Weaker state management than LangGraph
- Less flexible for complex conditional workflows

**Why Not AutoGen:**
- Conversation-focused (not ideal for FoodFlow OS use cases)
- Less robust checkpointing than LangGraph
- Simpler use cases than FoodFlow OS requires

**Multi-Tenant RAG Strategy:**
- Separate Pinecone namespace per organization
- Global knowledge base (shared FSQ/regulatory docs)
- Per-tenant knowledge base (SOPs, specifications, policies)
- Application-level access control with data room contracts

**Use Cases in FoodFlow OS:**
- Natural language queries ("Is batch #12345 safe to ship?")
- Multi-turn conversations with context
- Complex workflows (recall investigation, root cause analysis)
- Human-in-the-loop approvals (critical decisions)

---

## 7. Vector Database: Pinecone

**Decision:** Pinecone (managed) or Qdrant (self-hosted)

**Rationale:**
- **Pinecone:** Fully managed, excellent performance, native multi-tenancy (namespaces)
- **Qdrant:** Self-hosted option for data sovereignty, open-source, good performance

**Multi-Tenancy:**
- Pinecone: Separate namespace per organization
- Qdrant: Separate collection per organization

**Use Cases in FoodFlow OS:**
- RAG for LLM orchestration (document retrieval)
- Semantic search (specifications, SOPs, policies)
- Similar product search (find similar defects, batches)

**Alternatives Considered:**
- Weaviate: Good but less mature than Pinecone/Qdrant
- Milvus: Open-source, good for large-scale but more complex

---

## 8. Feature Store: Feast (Open-Source) or Tecton (Managed)

**Decision:** Feast for MVP, migrate to Tecton for scale

**Rationale:**
- **Feast:** Open-source, free, good for MVP and small-scale deployments
- **Tecton:** Managed, enterprise-grade, 100K QPS at millisecond latency, better for production scale

**Feature Store Architecture:**
```
Offline Store (PostgreSQL + TimescaleDB)
    ↓
Feature Registry (Feast/Tecton)
    ↓
Online Store (Redis)
    ↓
Real-Time Serving (FastAPI)
```

**Use Cases in FoodFlow OS:**
- Feature serving for ML models (forecasting, anomaly detection, risk scoring)
- Real-time feature computation (sensor aggregates, production metrics)
- Historical feature retrieval (model training)

**Alternatives Considered:**
- Hopsworks: Good but more complex setup
- AWS SageMaker Feature Store: Locked into AWS ecosystem

---

## 9. MLOps Platform: MLflow + Kubeflow

**Decision:** MLflow for experiment tracking, Kubeflow for pipeline orchestration

**Rationale:**
- **MLflow:** Simple, lightweight, excellent for experiment tracking and model registry
- **Kubeflow:** Kubernetes-native, scalable, composable ML workflows

**MLOps Architecture:**
```
Model Development (Jupyter, VS Code)
    ↓
Experiment Tracking (MLflow)
    ↓
Model Training (Kubeflow Pipelines)
    ↓
Model Registry (MLflow)
    ↓
Model Deployment (KServe on Kubernetes)
    ↓
Model Monitoring (Prometheus + Grafana)
```

**Use Cases in FoodFlow OS:**
- Experiment tracking (forecasting models, vision models)
- Model versioning and registry
- Automated retraining pipelines
- Model deployment and serving
- Model performance monitoring

**Alternatives Considered:**
- ZenML: Good but adds complexity
- Vertex AI: Locked into Google Cloud ecosystem

---

## 10. Real-Time Data Pipeline: Apache Kafka

**Decision:** Apache Kafka (self-hosted) or Azure Event Hub (managed)

**Rationale:**
- **Kafka:** Industry standard, high throughput, strong ecosystem, flexible
- **Azure Event Hub:** Managed Kafka-compatible service, easier operations

**Data Pipeline Architecture:**
```
Data Sources (PLCs, Sensors, Vision, ERP, FSQ)
    ↓
Change Data Capture (Debezium for PostgreSQL CDC)
    ↓
Kafka Topics (partitioned by tenant)
    ↓
Stream Processing (Kafka Streams or Flink)
    ↓
Sinks (PostgreSQL, TimescaleDB, Neo4j, Redis, S3)
```

**Use Cases in FoodFlow OS:**
- Real-time event streaming (sensor data, production events)
- Change data capture (sync between databases)
- Event-driven architecture (triggers, notifications)
- Stream processing (aggregations, enrichment)

**Alternatives Considered:**
- RabbitMQ: Better for traditional messaging, lower throughput
- AWS Kinesis: Locked into AWS ecosystem

---

## 11. Databases

### Transactional Data: PostgreSQL 16

**Rationale:**
- Industry standard, mature, reliable
- Excellent JSON support (JSONB)
- Strong ACID guarantees
- Best integration with ORMs (SQLAlchemy, Prisma)

**Use Cases:**
- Users, organizations, tenants
- Orders, shipments, inventory
- Audit logs, notifications

### Time-Series Data: TimescaleDB

**Rationale:**
- PostgreSQL extension (familiar SQL interface)
- Optimized for time-series workloads
- Automatic partitioning and compression
- Continuous aggregates (materialized views)

**Use Cases:**
- Sensor data (temperature, humidity, pressure)
- Production metrics (throughput, downtime, quality)
- Forecasts (historical and predicted values)

### Document Store: MongoDB

**Rationale:**
- Flexible schema for unstructured data
- Excellent for documents and specifications
- Strong aggregation pipeline

**Use Cases:**
- Specifications, SOPs, policies
- Audit documents, COAs
- Unstructured FSQ records

### Cache: Redis

**Rationale:**
- In-memory, extremely fast
- Excellent for caching and sessions
- Pub/sub for real-time updates

**Use Cases:**
- Feature serving (online feature store)
- Session management
- Real-time leaderboards and dashboards

---

## 12. Backend Framework: FastAPI (Python) + NestJS (TypeScript)

**Decision:** FastAPI for ML/data services, NestJS for business logic services

**Rationale:**
- **FastAPI:** Best for Python-based ML/data services, async support, automatic OpenAPI docs
- **NestJS:** Best for TypeScript-based business logic, modular architecture, excellent for microservices

**Service Breakdown:**
- **FastAPI:** Forecast Service, Vision Service, LLM Orchestration Service, Optimization Service
- **NestJS:** User Service, Tenant Service, Notification Service, Integration Service

---

## 13. Frontend: Next.js 15 + React 19 + TypeScript

**Decision:** Next.js 15 (App Router) with React Server Components

**Rationale:**
- Best-in-class developer experience
- Server-side rendering for performance
- React Server Components for reduced bundle size
- Excellent TypeScript support
- Strong ecosystem and community

**UI Component Library:** shadcn/ui (Tailwind CSS + Radix UI)

**State Management:** Zustand (lightweight) + TanStack Query (server state)

**Visualization:** Recharts (charts), React Flow (graphs), Mapbox (maps)

---

## 14. Infrastructure: Kubernetes + Docker

**Decision:** Kubernetes for orchestration, Docker for containerization

**Rationale:**
- Industry standard for container orchestration
- Excellent for microservices architecture
- Strong ecosystem (Helm, Istio, Prometheus)
- Cloud-agnostic (can run on AWS, Azure, GCP, on-prem)

**Deployment:**
- Development: Docker Compose
- Staging/Production: Kubernetes (EKS, AKS, or GKE)

---

## 15. Monitoring & Observability: Prometheus + Grafana + OpenTelemetry

**Decision:** Prometheus for metrics, Grafana for visualization, OpenTelemetry for traces

**Rationale:**
- Industry standard, open-source
- Excellent Kubernetes integration
- Strong ecosystem and community

**Monitoring Stack:**
- Metrics: Prometheus
- Visualization: Grafana
- Traces: Jaeger (via OpenTelemetry)
- Logs: Loki
- Alerts: Alertmanager

---

## Complete Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Graph Database** | Neo4j Enterprise | FoodGraph, traceability, supplier networks |
| **Transactional DB** | PostgreSQL 16 | Users, orders, inventory, audit logs |
| **Time-Series DB** | TimescaleDB | Sensor data, production metrics, forecasts |
| **Document Store** | MongoDB | Specifications, SOPs, policies, documents |
| **Vector Database** | Pinecone / Qdrant | RAG, semantic search |
| **Cache** | Redis | Feature serving, sessions, real-time updates |
| **Message Bus** | Apache Kafka / Azure Event Hub | Event streaming, CDC, real-time data pipeline |
| **Forecasting** | Nixtla (StatsForecast, HierarchicalForecast) | Demand forecasting, hierarchical reconciliation |
| **Computer Vision** | YOLOv10 + Few-Shot Learning | Defect detection, label verification |
| **Optimization** | Gurobi + Google OR-Tools | Production planning, routing |
| **LLM Orchestration** | LangGraph + Pydantic-AI | Natural language interface, agent workflows |
| **Feature Store** | Feast / Tecton | Feature serving for ML models |
| **MLOps** | MLflow + Kubeflow | Experiment tracking, model registry, pipelines |
| **Edge Runtime** | Azure IoT Edge + ONNX Runtime | Edge inference, OPC UA integration |
| **Backend (ML)** | FastAPI (Python) | ML/data services |
| **Backend (Business)** | NestJS (TypeScript) | Business logic services |
| **Frontend** | Next.js 15 + React 19 + TypeScript | Web UI (workspaces) |
| **Container** | Docker | Containerization |
| **Orchestration** | Kubernetes | Container orchestration |
| **Monitoring** | Prometheus + Grafana + OpenTelemetry | Metrics, visualization, traces |

---

## Next Steps

1. Design detailed system architecture (microservices, data flow, APIs)
2. Create comprehensive API specifications
3. Design database schemas (PostgreSQL, Neo4j, MongoDB, TimescaleDB)
4. Design LangGraph workflows for LLM orchestration
5. Create implementation roadmap for AI coders
6. Set up GitHub repository with complete documentation

---

## References

- Neo4j vs TigerGraph vs ArangoDB: https://risingwave.com/blog/graph-database-battle-neo4j-tigergraph-and-arangodb-compared/
- Nixtla HierarchicalForecast: https://github.com/Nixtla/hierarchicalforecast
- Edge AI in Food Manufacturing: https://www.barbara.tech/blog/how-edge-ai-is-shaping-the-future-of-food-beverage-manufacturing
- MIP Solvers Comparison: https://medium.com/operations-research-bit/mip-solvers-unleashed-a-beginners-guide-to-pulp-cplex-gurobi-google-or-tools-and-pyomo-0150d4bd3999
- LangGraph vs CrewAI vs AutoGen: https://sparkco.ai/blog/langgraph-vs-crewai-vs-autogen-2025-deployment-showdown
- Feature Stores in 2025: https://www.gocodeo.com/post/top-5-feature-stores-in-2025-tecton-feast-and-beyond
- MLOps Platforms: https://neptune.ai/blog/mlops-tools-platforms-landscape
- Kafka vs Event Hub: https://www.kai-waehner.de/blog/2024/10/19/when-to-choose-apache-kafka-vs-azure-event-hubs-vs-confluent-cloud-for-a-microsoft-fabric-lakehouse/
