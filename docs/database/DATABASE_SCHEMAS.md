# FoodFlow OS: Database Schemas

**Version:** 1.0  
**Date:** November 16, 2025

---

## Overview

FoodFlow OS uses a **polyglot persistence** architecture with multiple specialized databases:

| Database | Purpose | Services |
|----------|---------|----------|
| **PostgreSQL** | Transactional data (users, tenants, subscriptions) | Identity, Tenant, Integration, Data Room, Notification |
| **Neo4j** | Graph relationships (traceability, supplier networks) | FoodGraph |
| **MongoDB** | Unstructured data (vision results, training images) | Vision |
| **TimescaleDB** | Time-series data (sensors, production metrics) | Sensor Analytics, Production Analytics, Forecast |
| **Redis** | Caching, session storage, job queues | All services |
| **Pinecone** | Vector embeddings (RAG) | LLM Orchestration |

---

## 1. PostgreSQL Schemas

### 1.1 Identity Service

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    tenant_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);

-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    tenant_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, tenant_id)
);

CREATE INDEX idx_roles_tenant_id ON roles(tenant_id);

-- Permissions table
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource, action)
);

-- User-Role mapping
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Role-Permission mapping
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Refresh tokens
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
```

### 1.2 Tenant Service

```sql
-- Tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    logo_url VARCHAR(500),
    primary_color VARCHAR(7),
    subscription_plan VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_subscription_status ON tenants(subscription_status);

-- Subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    stripe_subscription_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_tenant_id ON subscriptions(tenant_id);

-- Usage metrics table
CREATE TABLE usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    value NUMERIC NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_metrics_tenant_id ON usage_metrics(tenant_id);
CREATE INDEX idx_usage_metrics_timestamp ON usage_metrics(timestamp);

-- Feature flags table
CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, feature_name)
);

CREATE INDEX idx_feature_flags_tenant_id ON feature_flags(tenant_id);
```

### 1.3 Integration Service

```sql
-- Connectors table
CREATE TABLE connectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_connectors_tenant_id ON connectors(tenant_id);
CREATE INDEX idx_connectors_type ON connectors(type);

-- Sync jobs table
CREATE TABLE sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_id UUID REFERENCES connectors(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    records_synced INTEGER DEFAULT 0,
    errors JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sync_jobs_connector_id ON sync_jobs(connector_id);
CREATE INDEX idx_sync_jobs_status ON sync_jobs(status);

-- Webhooks table
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_id UUID REFERENCES connectors(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    events JSONB NOT NULL,
    secret VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_webhooks_connector_id ON webhooks(connector_id);
```

### 1.4 Data Room Service

```sql
-- Data rooms table
CREATE TABLE data_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_tenant_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_rooms_owner_tenant_id ON data_rooms(owner_tenant_id);

-- Contracts table
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_room_id UUID REFERENCES data_rooms(id) ON DELETE CASCADE,
    participant_tenant_id UUID NOT NULL,
    data_scope JSONB NOT NULL,
    permissions JSONB NOT NULL,
    expiry_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contracts_data_room_id ON contracts(data_room_id);
CREATE INDEX idx_contracts_participant_tenant_id ON contracts(participant_tenant_id);

-- Access requests table
CREATE TABLE access_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_room_id UUID REFERENCES data_rooms(id) ON DELETE CASCADE,
    requester_tenant_id UUID NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by UUID
);

CREATE INDEX idx_access_requests_data_room_id ON access_requests(data_room_id);
CREATE INDEX idx_access_requests_requester_tenant_id ON access_requests(requester_tenant_id);
```

### 1.5 Notification Service

```sql
-- Notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    channel VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_tenant_id ON notifications(tenant_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);

-- Templates table
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500),
    body TEXT NOT NULL,
    channel VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_templates_tenant_id ON templates(tenant_id);

-- Channels table
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, type)
);

CREATE INDEX idx_channels_tenant_id ON channels(tenant_id);
```

### 1.6 LLM Orchestration Service

```sql
-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversations_tenant_id ON conversations(tenant_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    agent VARCHAR(100),
    confidence NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

-- Approvals table (Human-in-the-Loop)
CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    action_payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    approved_by UUID,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_approvals_conversation_id ON approvals(conversation_id);
CREATE INDEX idx_approvals_status ON approvals(status);
```

### 1.7 Optimization Service

```sql
-- Optimization runs table
CREATE TABLE optimization_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    objective_value NUMERIC,
    solve_time NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_optimization_runs_tenant_id ON optimization_runs(tenant_id);
CREATE INDEX idx_optimization_runs_type ON optimization_runs(type);

-- Production plans table
CREATE TABLE production_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES optimization_runs(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    quantity NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_production_plans_run_id ON production_plans(run_id);

-- Inventory plans table
CREATE TABLE inventory_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES optimization_runs(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    safety_stock NUMERIC NOT NULL,
    reorder_point NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_plans_run_id ON inventory_plans(run_id);

-- Routing plans table
CREATE TABLE routing_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES optimization_runs(id) ON DELETE CASCADE,
    vehicle_id VARCHAR(100) NOT NULL,
    route JSONB NOT NULL,
    distance NUMERIC NOT NULL,
    duration NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_routing_plans_run_id ON routing_plans(run_id);
```

---

## 2. Neo4j Schema (FoodGraph)

### 2.1 Node Labels

```cypher
-- Product hierarchy
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT ingredient_id IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT sku_id IF NOT EXISTS FOR (s:SKU) REQUIRE s.id IS UNIQUE;

-- Supply chain entities
CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT batch_id IF NOT EXISTS FOR (b:Batch) REQUIRE b.id IS UNIQUE;
CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;

-- Indexes for performance
CREATE INDEX product_tenant_id IF NOT EXISTS FOR (p:Product) ON (p.tenant_id);
CREATE INDEX ingredient_tenant_id IF NOT EXISTS FOR (i:Ingredient) ON (i.tenant_id);
CREATE INDEX supplier_tenant_id IF NOT EXISTS FOR (s:Supplier) ON (s.tenant_id);
CREATE INDEX batch_tenant_id IF NOT EXISTS FOR (b:Batch) ON (b.tenant_id);
```

### 2.2 Node Properties

```cypher
-- Product node
(:Product {
    id: String,
    tenant_id: String,
    name: String,
    category: String,
    brand: String,
    created_at: DateTime,
    updated_at: DateTime
})

-- Ingredient node
(:Ingredient {
    id: String,
    tenant_id: String,
    name: String,
    allergens: [String],
    origin_country: String,
    created_at: DateTime,
    updated_at: DateTime
})

-- SKU node
(:SKU {
    id: String,
    tenant_id: String,
    product_id: String,
    sku_code: String,
    size: String,
    unit: String,
    created_at: DateTime,
    updated_at: DateTime
})

-- Supplier node
(:Supplier {
    id: String,
    tenant_id: String,
    name: String,
    country: String,
    risk_score: Float,
    certifications: [String],
    created_at: DateTime,
    updated_at: DateTime
})

-- Batch node
(:Batch {
    id: String,
    tenant_id: String,
    batch_number: String,
    production_date: Date,
    expiry_date: Date,
    quantity: Float,
    unit: String,
    created_at: DateTime,
    updated_at: DateTime
})

-- Location node
(:Location {
    id: String,
    tenant_id: String,
    name: String,
    type: String,
    address: String,
    coordinates: Point,
    created_at: DateTime,
    updated_at: DateTime
})
```

### 2.3 Relationship Types

```cypher
-- Product relationships
(Product)-[:CONTAINS]->(Ingredient)
(Product)-[:HAS_SKU]->(SKU)
(Product)-[:PRODUCED_AT]->(Location)

-- Ingredient relationships
(Ingredient)-[:SOURCED_FROM]->(Supplier)
(Ingredient)-[:CONTAINS]->(Ingredient)  // For composite ingredients

-- Batch relationships
(Batch)-[:OF_PRODUCT]->(Product)
(Batch)-[:USES_INGREDIENT]->(Batch)  // Ingredient batch used in product batch
(Batch)-[:PRODUCED_AT]->(Location)
(Batch)-[:SHIPPED_TO]->(Location)

-- Supplier relationships
(Supplier)-[:SUPPLIES_TO]->(Supplier)  // Multi-tier supply chain
(Supplier)-[:LOCATED_AT]->(Location)
```

### 2.4 Example Queries

```cypher
-- Forward traceability (ingredient → finished goods)
MATCH path = (ingredient:Ingredient {id: $ingredient_id})-[:CONTAINS*]->(product:Product)
WHERE ingredient.tenant_id = $tenant_id
RETURN path

-- Backward traceability (finished good → ingredients)
MATCH path = (product:Product {id: $product_id})-[:CONTAINS*]->(ingredient:Ingredient)
WHERE product.tenant_id = $tenant_id
RETURN path

-- Supplier network (multi-tier)
MATCH path = (supplier:Supplier {id: $supplier_id})-[:SUPPLIES_TO*]->(downstream:Supplier)
WHERE supplier.tenant_id = $tenant_id
RETURN path

-- Risk propagation (identify products affected by high-risk supplier)
MATCH (supplier:Supplier {risk_score: > 0.7})<-[:SOURCED_FROM]-(ingredient:Ingredient)<-[:CONTAINS]-(product:Product)
WHERE supplier.tenant_id = $tenant_id
RETURN DISTINCT product

-- Batch traceability (find all batches using a specific ingredient batch)
MATCH path = (ingredient_batch:Batch {id: $ingredient_batch_id})-[:USES_INGREDIENT*]->(product_batch:Batch)
WHERE ingredient_batch.tenant_id = $tenant_id
RETURN path
```

---

## 3. MongoDB Schema (Vision Service)

### 3.1 Collections

```javascript
// vision_models collection
{
    _id: ObjectId,
    tenant_id: String,
    name: String,
    version: String,
    type: String,  // "defect_detection", "label_verification", "quality_inspection"
    sku: String,
    accuracy: Number,
    model_path: String,
    onnx_path: String,
    created_at: Date,
    updated_at: Date
}

// Indexes
db.vision_models.createIndex({ tenant_id: 1 });
db.vision_models.createIndex({ sku: 1 });
db.vision_models.createIndex({ type: 1 });

// vision_results collection
{
    _id: ObjectId,
    tenant_id: String,
    model_id: ObjectId,
    image_url: String,
    inference_time: Number,  // milliseconds
    defects: [
        {
            type: String,
            confidence: Number,
            bbox: {
                x: Number,
                y: Number,
                width: Number,
                height: Number
            }
        }
    ],
    created_at: Date
}

// Indexes
db.vision_results.createIndex({ tenant_id: 1 });
db.vision_results.createIndex({ model_id: 1 });
db.vision_results.createIndex({ created_at: -1 });

// training_images collection
{
    _id: ObjectId,
    tenant_id: String,
    sku: String,
    image_url: String,
    label: String,  // "defect" or "ok"
    bbox: {
        x: Number,
        y: Number,
        width: Number,
        height: Number
    },
    defect_type: String,
    created_at: Date
}

// Indexes
db.training_images.createIndex({ tenant_id: 1 });
db.training_images.createIndex({ sku: 1 });
db.training_images.createIndex({ label: 1 });
```

---

## 4. TimescaleDB Schema

### 4.1 Sensor Analytics Service

```sql
-- Create hypertable for sensor data
CREATE TABLE sensor_data (
    time TIMESTAMPTZ NOT NULL,
    tenant_id UUID NOT NULL,
    sensor_id UUID NOT NULL,
    location_id UUID,
    metric VARCHAR(50) NOT NULL,
    value NUMERIC NOT NULL,
    unit VARCHAR(20)
);

SELECT create_hypertable('sensor_data', 'time');

CREATE INDEX idx_sensor_data_tenant_sensor ON sensor_data (tenant_id, sensor_id, time DESC);
CREATE INDEX idx_sensor_data_metric ON sensor_data (metric, time DESC);

-- Sensor anomalies table
CREATE TABLE sensor_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    sensor_id UUID NOT NULL,
    time TIMESTAMPTZ NOT NULL,
    metric VARCHAR(50) NOT NULL,
    value NUMERIC NOT NULL,
    expected_value NUMERIC,
    anomaly_score NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sensor_anomalies_tenant_sensor ON sensor_anomalies (tenant_id, sensor_id);
CREATE INDEX idx_sensor_anomalies_time ON sensor_anomalies (time DESC);

-- Sensor alerts table
CREATE TABLE sensor_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    sensor_id UUID NOT NULL,
    metric VARCHAR(50) NOT NULL,
    condition VARCHAR(20) NOT NULL,  // "gt", "lt", "eq"
    threshold NUMERIC NOT NULL,
    notification_channel VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sensor_alerts_tenant_sensor ON sensor_alerts (tenant_id, sensor_id);

-- Sensors table
CREATE TABLE sensors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    location_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sensors_tenant_id ON sensors (tenant_id);
```

### 4.2 Production Analytics Service

```sql
-- Create hypertable for production events
CREATE TABLE production_events (
    time TIMESTAMPTZ NOT NULL,
    tenant_id UUID NOT NULL,
    line_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    duration INTERVAL,
    quantity NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT create_hypertable('production_events', 'time');

CREATE INDEX idx_production_events_tenant_line ON production_events (tenant_id, line_id, time DESC);
CREATE INDEX idx_production_events_type ON production_events (event_type, time DESC);

-- Downtime events table
CREATE TABLE downtime_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    line_id UUID NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    reason VARCHAR(255),
    category VARCHAR(50),  // "planned", "unplanned"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_downtime_events_tenant_line ON downtime_events (tenant_id, line_id);
CREATE INDEX idx_downtime_events_time ON downtime_events (start_time DESC);

-- Quality events table
CREATE TABLE quality_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    line_id UUID NOT NULL,
    time TIMESTAMPTZ NOT NULL,
    defect_type VARCHAR(100),
    quantity NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quality_events_tenant_line ON quality_events (tenant_id, line_id);
CREATE INDEX idx_quality_events_time ON quality_events (time DESC);

-- OEE metrics table (materialized view)
CREATE TABLE oee_metrics (
    time TIMESTAMPTZ NOT NULL,
    tenant_id UUID NOT NULL,
    line_id UUID NOT NULL,
    availability NUMERIC NOT NULL,
    performance NUMERIC NOT NULL,
    quality NUMERIC NOT NULL,
    oee NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT create_hypertable('oee_metrics', 'time');

CREATE INDEX idx_oee_metrics_tenant_line ON oee_metrics (tenant_id, line_id, time DESC);
```

### 4.3 Forecast Service

```sql
-- Create hypertable for forecasts
CREATE TABLE forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    sku VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    forecast_date DATE NOT NULL,
    horizon INTEGER NOT NULL,
    p10 NUMERIC NOT NULL,
    p50 NUMERIC NOT NULL,
    p90 NUMERIC NOT NULL,
    model VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_forecasts_tenant_sku ON forecasts (tenant_id, sku, forecast_date DESC);
CREATE INDEX idx_forecasts_date ON forecasts (forecast_date DESC);

-- Actuals table (for forecast accuracy calculation)
CREATE TABLE actuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    sku VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    date DATE NOT NULL,
    quantity NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_actuals_tenant_sku ON actuals (tenant_id, sku, date DESC);

-- Forecast accuracy table
CREATE TABLE forecast_accuracy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    sku VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    date DATE NOT NULL,
    mape NUMERIC,  // Mean Absolute Percentage Error
    rmse NUMERIC,  // Root Mean Squared Error
    bias NUMERIC,  // Forecast Bias
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_forecast_accuracy_tenant_sku ON forecast_accuracy (tenant_id, sku, date DESC);

-- Inventory recommendations table
CREATE TABLE inventory_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    sku VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    safety_stock NUMERIC NOT NULL,
    reorder_point NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_recommendations_tenant_sku ON inventory_recommendations (tenant_id, sku);
```

---

## 5. Redis Schema

### 5.1 Key Patterns

```
# Session storage
session:{session_id} → JSON (user session data)
TTL: 7 days

# JWT
