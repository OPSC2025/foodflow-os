# FoodFlow OS: System Architecture

**Version:** 1.0  
**Date:** November 16, 2025  
**Author:** Manus AI  
**Status:** Architecture Design

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Principles](#architecture-principles)
4. [Microservices Architecture](#microservices-architecture)
5. [Data Architecture](#data-architecture)
6. [Integration Architecture](#integration-architecture)
7. [AI/ML Architecture](#aiml-architecture)
8. [Edge Architecture](#edge-architecture)
9. [Security Architecture](#security-architecture)
10. [Deployment Architecture](#deployment-architecture)
11. [Scalability & Performance](#scalability--performance)
12. [Disaster Recovery & Business Continuity](#disaster-recovery--business-continuity)

---

## Executive Summary

FoodFlow OS is an **AI-powered operating system for the food value chain**, designed to unify data from production, supply chain, quality control, and regulatory systems into a single, intelligent platform. The system serves as a **data and intelligence hub** that enables food companies to make better decisions through real-time insights, predictive analytics, and AI-powered assistance.

### Core Value Proposition

FoodFlow OS positions itself as the **"operating system"** layer that sits between existing enterprise systems (ERP, FSQ, MES, PLCs) and decision-makers (FSQ teams, operations managers, executives). It does not replace these systems but instead **aggregates, enriches, and intelligently surfaces** their data through:

1. **FoodGraph** - A knowledge graph that maps relationships between products, ingredients, suppliers, batches, and locations
2. **AI Co-Pilot** - Natural language interface powered by specialized AI agents
3. **Predictive Intelligence** - Forecasting, anomaly detection, and risk scoring
4. **Optimization Engine** - Production planning, inventory optimization, and routing
5. **Cross-Org Data Rooms** - Secure data sharing between trading partners

### Key Design Principles

1. **Integration-First**: Connect to existing systems via APIs, not replacement
2. **AI-Native**: LLM orchestration and specialized AI agents at the core
3. **Graph-Centric**: Neo4j FoodGraph as the source of truth for relationships
4. **Multi-Tenant**: Complete data isolation with optional cross-org data rooms
5. **Edge-Capable**: Deploy AI models at the edge for real-time inference
6. **Event-Driven**: Kafka-based real-time data pipeline
7. **Cloud-Agnostic**: Kubernetes-based deployment on any cloud or on-prem

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FoodFlow OS Platform                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Workspace Layer (UI)                      │  │
│  │  Next.js 15 + React 19 + TypeScript + shadcn/ui             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                ↓                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   API Gateway (Kong)                         │  │
│  │  Authentication, Rate Limiting, Routing, Observability       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                ↓                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Microservices Layer                         │  │
│  │                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │   Identity  │  │   Tenant    │  │ Notification│         │  │
│  │  │   Service   │  │   Service   │  │   Service   │         │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │  │
│  │                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │  FoodGraph  │  │  Forecast   │  │   Vision    │         │  │
│  │  │   Service   │  │   Service   │  │   Service   │         │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │  │
│  │                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │     LLM     │  │Optimization │  │ Integration │         │  │
│  │  │Orchestration│  │   Service   │  │   Service   │         │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │  │
│  │                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │  Data Room  │  │   Sensor    │  │  Production │         │  │
│  │  │   Service   │  │  Analytics  │  │  Analytics  │         │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                ↓                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     Data Layer                               │  │
│  │                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │   Neo4j     │  │ PostgreSQL  │  │ TimescaleDB │         │  │
│  │  │  (FoodGraph)│  │(Transactional)│ │(Time-Series)│         │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │  │
│  │                                                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │  │
│  │  │   MongoDB   │  │   Pinecone  │  │    Redis    │         │  │
│  │  │ (Documents) │  │  (Vectors)  │  │   (Cache)   │         │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                ↓                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Event Streaming Layer                       │  │
│  │                   Apache Kafka / Azure Event Hub             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                ↓                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Integration Layer                         │  │
│  │  ERP (Odoo, SAP) | FSQ (FSQapp) | MES | PLCs | Sensors      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          Edge Layer                                 │
│  Azure IoT Edge + ONNX Runtime (deployed at plants)                │
│  Vision Inference | Sensor Aggregation | OPC UA Integration        │
└─────────────────────────────────────────────────────────────────────┘
```

### System Components

#### 1. Workspace Layer (Frontend)
- **Technology**: Next.js 15 + React 19 + TypeScript
- **Purpose**: Multi-tenant web application for FSQ teams, operations managers, and executives
- **Features**: Dashboards, natural language queries, traceability visualization, forecasts, alerts

#### 2. API Gateway
- **Technology**: Kong or AWS API Gateway
- **Purpose**: Single entry point for all API requests
- **Features**: Authentication (OAuth2/OIDC), rate limiting, routing, observability

#### 3. Microservices Layer
- **Technology**: FastAPI (Python) for ML services, NestJS (TypeScript) for business services
- **Purpose**: Domain-driven microservices architecture
- **Services**: 12 core services (detailed below)

#### 4. Data Layer
- **Neo4j**: FoodGraph (product relationships, traceability)
- **PostgreSQL**: Transactional data (users, orders, inventory)
- **TimescaleDB**: Time-series data (sensors, production metrics, forecasts)
- **MongoDB**: Documents (specifications, SOPs, policies)
- **Pinecone**: Vector database (RAG, semantic search)
- **Redis**: Cache (feature serving, sessions)

#### 5. Event Streaming Layer
- **Technology**: Apache Kafka or Azure Event Hub
- **Purpose**: Real-time event streaming and change data capture (CDC)
- **Topics**: Partitioned by tenant for data isolation

#### 6. Integration Layer
- **Purpose**: Connect to external systems (ERP, FSQ, MES, PLCs, sensors)
- **Patterns**: REST APIs, GraphQL, OPC UA, MQTT, webhooks

#### 7. Edge Layer
- **Technology**: Azure IoT Edge + ONNX Runtime
- **Purpose**: Deploy AI models at the edge for real-time inference
- **Capabilities**: Vision inference, sensor aggregation, OPC UA integration

---

## Architecture Principles

### 1. Integration-First, Not Replacement

FoodFlow OS is designed to **augment, not replace** existing enterprise systems. It connects to ERP, FSQ, MES, and PLC systems via APIs and aggregates their data into a unified view.

**Why This Matters:**
- Food companies have significant investments in existing systems
- Replacing systems is expensive, risky, and time-consuming
- Integration allows faster time-to-value and lower risk

**Implementation:**
- Integration Service with pre-built connectors (Odoo, SAP, FSQapp, etc.)
- Standardized data models with transformation logic
- Bidirectional sync (read from and write to external systems)

### 2. AI-Native Architecture

AI is not a feature but the **core orchestration layer** of FoodFlow OS. LLM orchestration (LangGraph) sits at the center and coordinates specialized AI agents.

**Why This Matters:**
- Natural language is the most intuitive interface for FSQ teams
- AI agents can handle complex, multi-step workflows
- Continuous learning from user interactions improves accuracy over time

**Implementation:**
- LangGraph workflows with specialized agent nodes
- Multi-tenant RAG with Pinecone namespaces
- Human-in-the-loop for critical decisions
- Confidence calibration and explainability

### 3. Graph-Centric Data Model

The **FoodGraph** (Neo4j) is the source of truth for all relationships between products, ingredients, suppliers, batches, and locations.

**Why This Matters:**
- Traceability queries (forward/backward tracing) are naturally graph problems
- Graph databases excel at relationship queries (10-100x faster than SQL joins)
- Supplier risk propagation requires graph algorithms

**Implementation:**
- Neo4j as the primary graph database
- Cypher queries for traceability and supplier networks
- Graph algorithms for risk propagation and community detection

### 4. Multi-Tenant with Data Isolation

Each organization has **complete data isolation** with separate databases, namespaces, and access controls. Optional **data rooms** enable secure cross-org data sharing.

**Why This Matters:**
- Food companies are highly protective of their data
- Regulatory compliance (GDPR, CCPA) requires strict data isolation
- Data rooms enable collaboration without compromising security

**Implementation:**
- Separate Neo4j database per organization
- Separate Pinecone namespace per organization
- Application-level access control with JWT tokens
- Data room contracts with granular permissions

### 5. Edge-Capable for Real-Time Inference

AI models are deployed at the edge (plant floor) for **real-time inference** without cloud latency.

**Why This Matters:**
- Production lines operate at high speed (100+ units/minute)
- Cloud latency (50-200ms) is too slow for real-time inspection
- Edge deployment ensures uptime even with internet outages

**Implementation:**
- Azure IoT Edge with ONNX Runtime
- YOLOv10 models for vision inference
- Store-and-forward messaging to cloud

### 6. Event-Driven Architecture

All state changes are published as **events** to Kafka, enabling real-time reactions and downstream processing.

**Why This Matters:**
- Decouples services (producer doesn't know about consumers)
- Enables real-time dashboards and alerts
- Simplifies auditing and compliance

**Implementation:**
- Kafka topics partitioned by tenant
- Event schemas with Avro or Protobuf
- Stream processing with Kafka Streams or Flink

### 7. Cloud-Agnostic Deployment

FoodFlow OS runs on **any cloud (AWS, Azure, GCP) or on-premises** using Kubernetes.

**Why This Matters:**
- Food companies have diverse infrastructure preferences
- Avoids vendor lock-in
- Enables hybrid cloud deployments

**Implementation:**
- Kubernetes for container orchestration
- Helm charts for deployment
- Terraform for infrastructure as code

---

## Microservices Architecture

FoodFlow OS is composed of **12 core microservices**, each with a single responsibility and well-defined API contracts.

### Service Catalog

| Service | Technology | Purpose | Database |
|---------|-----------|---------|----------|
| **Identity Service** | NestJS | Authentication, authorization, users, roles | PostgreSQL |
| **Tenant Service** | NestJS | Multi-tenancy, organizations, subscriptions | PostgreSQL |
| **FoodGraph Service** | FastAPI | Graph queries, traceability, supplier networks | Neo4j |
| **Forecast Service** | FastAPI | Demand forecasting, hierarchical reconciliation | TimescaleDB, PostgreSQL |
| **Vision Service** | FastAPI | Defect detection, label verification, few-shot learning | MongoDB (images), Redis (cache) |
| **LLM Orchestration Service** | FastAPI | Natural language queries, agent workflows, RAG | Pinecone, PostgreSQL |
| **Optimization Service** | FastAPI | Production planning, inventory optimization, routing | PostgreSQL |
| **Sensor Analytics Service** | FastAPI | Anomaly detection, real-time monitoring | TimescaleDB |
| **Production Analytics Service** | FastAPI | OEE, downtime analysis, quality metrics | TimescaleDB, PostgreSQL |
| **Integration Service** | NestJS | ERP/FSQ/MES connectors, data transformation | PostgreSQL, MongoDB |
| **Data Room Service** | NestJS | Cross-org data sharing, contracts, permissions | PostgreSQL, Neo4j |
| **Notification Service** | NestJS | Alerts, emails, SMS, Slack, webhooks | PostgreSQL, Redis |

### Service Details

#### 1. Identity Service

**Responsibility**: Authentication, authorization, user management, role-based access control (RBAC)

**Technology**: NestJS + TypeScript + Passport.js + JWT

**Key Features**:
- OAuth2/OIDC authentication
- JWT token issuance and validation
- Role-based access control (RBAC)
- Multi-factor authentication (MFA)
- SSO integration (SAML, LDAP)

**API Endpoints**:
```
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
GET    /auth/me
POST   /users
GET    /users/:id
PUT    /users/:id
DELETE /users/:id
GET    /roles
POST   /roles
```

**Database Schema** (PostgreSQL):
```sql
users (id, email, password_hash, first_name, last_name, tenant_id, created_at, updated_at)
roles (id, name, description, tenant_id, created_at, updated_at)
permissions (id, resource, action, description, created_at, updated_at)
user_roles (user_id, role_id)
role_permissions (role_id, permission_id)
```

#### 2. Tenant Service

**Responsibility**: Multi-tenancy, organization management, subscription management

**Technology**: NestJS + TypeScript + Stripe (billing)

**Key Features**:
- Tenant onboarding and provisioning
- Subscription management (plans, billing, invoicing)
- Feature flags (enable/disable features per tenant)
- Tenant-level configuration (branding, settings)
- Usage tracking and quotas

**API Endpoints**:
```
POST   /tenants
GET    /tenants/:id
PUT    /tenants/:id
DELETE /tenants/:id
GET    /tenants/:id/subscription
PUT    /tenants/:id/subscription
GET    /tenants/:id/usage
```

**Database Schema** (PostgreSQL):
```sql
tenants (id, name, slug, logo_url, primary_color, subscription_plan, subscription_status, created_at, updated_at)
subscriptions (id, tenant_id, plan, status, current_period_start, current_period_end, stripe_subscription_id, created_at, updated_at)
usage_metrics (id, tenant_id, metric_name, value, timestamp)
feature_flags (id, tenant_id, feature_name, enabled, created_at, updated_at)
```

#### 3. FoodGraph Service

**Responsibility**: Graph queries, traceability, supplier networks, risk propagation

**Technology**: FastAPI + Python + Neo4j Python Driver

**Key Features**:
- Forward/backward traceability queries
- Supplier network visualization
- Risk propagation algorithms
- Batch/lot relationships
- Product hierarchy (brand → category → product → SKU)

**API Endpoints**:
```
POST   /graph/query                    # Cypher query execution
GET    /graph/traceability/forward     # Forward tracing from ingredient
GET    /graph/traceability/backward    # Backward tracing from finished good
GET    /graph/suppliers/:id/network    # Supplier network
GET    /graph/suppliers/:id/risk       # Supplier risk score
POST   /graph/nodes                    # Create node
PUT    /graph/nodes/:id                # Update node
DELETE /graph/nodes/:id                # Delete node
POST   /graph/relationships            # Create relationship
DELETE /graph/relationships/:id        # Delete relationship
```

**Neo4j Schema**:
```cypher
// Nodes
(:Product {id, name, brand, category, sku, tenant_id})
(:Ingredient {id, name, allergens, tenant_id})
(:Supplier {id, name, country, risk_score, tenant_id})
(:Batch {id, batch_number, production_date, expiry_date, quantity, tenant_id})
(:Location {id, name, type, address, tenant_id})

// Relationships
(:Product)-[:CONTAINS]->(:Ingredient)
(:Ingredient)-[:SOURCED_FROM]->(:Supplier)
(:Batch)-[:PRODUCED_AT]->(:Location)
(:Batch)-[:CONTAINS]->(:Ingredient)
(:Batch)-[:SHIPPED_TO]->(:Location)
```

#### 4. Forecast Service

**Responsibility**: Demand forecasting, hierarchical reconciliation, inventory optimization

**Technology**: FastAPI + Python + Nixtla (StatsForecast, HierarchicalForecast)

**Key Features**:
- Hierarchical demand forecasting (brand → category → product → SKU → location)
- Probabilistic forecasts (P10, P50, P90)
- Forecast reconciliation (MinTrace, BottomUp, TopDown)
- Inventory optimization (safety stock, reorder points)
- Forecast accuracy tracking

**API Endpoints**:
```
POST   /forecasts/demand               # Generate demand forecast
GET    /forecasts/:id                  # Get forecast by ID
GET    /forecasts/accuracy             # Forecast accuracy metrics
POST   /forecasts/inventory/optimize   # Optimize inventory levels
GET    /forecasts/hierarchies          # Get forecast hierarchies
```

**Database Schema** (TimescaleDB):
```sql
forecasts (id, tenant_id, sku, location, forecast_date, horizon, p10, p50, p90, model, created_at)
actuals (id, tenant_id, sku, location, date, quantity, created_at)
forecast_accuracy (id, tenant_id, sku, location, date, mape, rmse, bias, created_at)
inventory_recommendations (id, tenant_id, sku, location, safety_stock, reorder_point, created_at)
```

#### 5. Vision Service

**Responsibility**: Defect detection, label verification, few-shot learning, dynamic SKU onboarding

**Technology**: FastAPI + Python + YOLOv10 + ONNX Runtime

**Key Features**:
- Real-time defect detection (burns, breaks, underfill, contamination)
- Label verification (OCR + object detection)
- Few-shot learning (5-10 images to onboard new SKU)
- Model training and deployment to edge
- Inference result storage and analysis

**API Endpoints**:
```
POST   /vision/inference               # Run inference on image
POST   /vision/models/train            # Train model with few-shot learning
GET    /vision/models/:id              # Get model details
POST   /vision/models/:id/deploy       # Deploy model to edge
GET    /vision/results                 # Get inference results
GET    /vision/defects/summary         # Defect summary analytics
```

**Database Schema** (MongoDB):
```javascript
// Collections
vision_models {
  _id, tenant_id, name, version, type, sku, accuracy, created_at, updated_at
}

vision_results {
  _id, tenant_id, model_id, image_url, inference_time, defects: [{type, confidence, bbox}], created_at
}

training_images {
  _id, tenant_id, sku, image_url, label, bbox, created_at
}
```

#### 6. LLM Orchestration Service

**Responsibility**: Natural language queries, agent workflows, RAG, human-in-the-loop

**Technology**: FastAPI + Python + LangGraph + Pinecone + Pydantic-AI

**Key Features**:
- Natural language query processing
- Multi-turn conversations with context
- Specialized AI agents (FoodGraph, Forecast, Vision, Compliance, Optimization)
- Multi-tenant RAG with Pinecone namespaces
- Human-in-the-loop for critical decisions
- Confidence calibration and explainability

**API Endpoints**:
```
POST   /llm/query                      # Natural language query
POST   /llm/conversations              # Start conversation
POST   /llm/conversations/:id/messages # Send message in conversation
GET    /llm/conversations/:id          # Get conversation history
POST   /llm/rag/ingest                 # Ingest documents for RAG
GET    /llm/rag/search                 # Semantic search
```

**LangGraph Workflow**:
```python
# Supervisor Node (routes queries)
supervisor = LangGraph.Node("supervisor", route_query)

# Specialized Agent Nodes
foodgraph_agent = LangGraph.Node("foodgraph_agent", query_foodgraph)
forecast_agent = LangGraph.Node("forecast_agent", generate_forecast)
vision_agent = LangGraph.Node("vision_agent", analyze_vision)
compliance_agent = LangGraph.Node("compliance_agent", answer_compliance)
optimization_agent = LangGraph.Node("optimization_agent", optimize_production)

# Tool Nodes
neo4j_tool = LangGraph.Tool("neo4j", execute_cypher_query)
forecast_tool = LangGraph.Tool("forecast", generate_demand_forecast)
vision_tool = LangGraph.Tool("vision", run_vision_inference)

# Human-in-the-Loop Node
human_approval = LangGraph.Node("human_approval", request_approval)

# Workflow
workflow = LangGraph.Workflow()
workflow.add_node(supervisor)
workflow.add_node(foodgraph_agent)
workflow.add_node(forecast_agent)
workflow.add_node(vision_agent)
workflow.add_node(compliance_agent)
workflow.add_node(optimization_agent)
workflow.add_node(human_approval)

workflow.add_edge(supervisor, foodgraph_agent, condition="query_type == 'traceability'")
workflow.add_edge(supervisor, forecast_agent, condition="query_type == 'forecast'")
workflow.add_edge(supervisor, vision_agent, condition="query_type == 'vision'")
workflow.add_edge(supervisor, compliance_agent, condition="query_type == 'compliance'")
workflow.add_edge(supervisor, optimization_agent, condition="query_type == 'optimization'")
workflow.add_edge(optimization_agent, human_approval, condition="requires_approval == True")
```

**Database Schema** (PostgreSQL + Pinecone):
```sql
-- PostgreSQL
conversations (id, tenant_id, user_id, title, created_at, updated_at)
messages (id, conversation_id, role, content, agent, confidence, created_at)
approvals (id, conversation_id, message_id, status, approved_by, approved_at, created_at)

-- Pinecone (Vector Database)
Namespace: tenant_{tenant_id}
Vectors: document_embeddings (1536 dimensions for OpenAI ada-002)
Metadata: {document_id, title, content, source, created_at}
```

#### 7. Optimization Service

**Responsibility**: Production planning, inventory optimization, routing, capacity planning

**Technology**: FastAPI + Python + Gurobi + Google OR-Tools

**Key Features**:
- Production planning and scheduling (MIP)
- Inventory optimization (safety stock, reorder points)
- Vehicle routing (VRP, TSP)
- Capacity planning
- Supply-demand matching

**API Endpoints**:
```
POST   /optimization/production/plan   # Generate production plan
POST   /optimization/inventory/optimize # Optimize inventory levels
POST   /optimization/routing/optimize  # Optimize delivery routes
GET    /optimization/results/:id       # Get optimization results
```

**Database Schema** (PostgreSQL):
```sql
optimization_runs (id, tenant_id, type, status, objective_value, solve_time, created_at, updated_at)
production_plans (id, run_id, sku, location, date, quantity, created_at)
inventory_plans (id, run_id, sku, location, safety_stock, reorder_point, created_at)
routing_plans (id, run_id, vehicle_id, route: jsonb, distance, duration, created_at)
```

#### 8. Sensor Analytics Service

**Responsibility**: Anomaly detection, real-time monitoring, sensor data aggregation

**Technology**: FastAPI + Python + TimescaleDB + Scikit-learn

**Key Features**:
- Real-time anomaly detection (temperature, humidity, pressure)
- Sensor data aggregation and downsampling
- Alert generation (threshold-based and ML-based)
- Historical trend analysis

**API Endpoints**:
```
POST   /sensors/data                   # Ingest sensor data (bulk)
GET    /sensors/:
id/data                # Get sensor data for sensor
GET    /sensors/anomalies              # Get anomalies
POST   /sensors/alerts                 # Create alert rule
GET    /sensors/alerts                 # Get alert rules
```

**Database Schema** (TimescaleDB):
```sql
sensor_data (time, tenant_id, sensor_id, location_id, metric, value, unit)
sensor_anomalies (id, tenant_id, sensor_id, time, metric, value, expected_value, anomaly_score, created_at)
sensor_alerts (id, tenant_id, sensor_id, metric, condition, threshold, notification_channel, created_at, updated_at)
```

#### 9. Production Analytics Service

**Responsibility**: OEE calculation, downtime analysis, quality metrics, production dashboards

**Technology**: FastAPI + Python + TimescaleDB + Pandas

**Key Features**:
- Overall Equipment Effectiveness (OEE) calculation
- Downtime analysis (planned vs unplanned)
- Quality metrics (defect rate, first-pass yield)
- Production dashboards (real-time and historical)
- Shift reports and KPI tracking

**API Endpoints**:
```
GET    /production/oee                 # Get OEE metrics
GET    /
