# Time-Series Forecasting & Edge Computing Research

**Date:** November 16, 2025

---

## Time-Series Forecasting for Supply Chain

### Recommended Framework: Nixtla Ecosystem

**Primary Libraries:**
1. **StatsForecast** - Fast univariate forecasting models
2. **HierarchicalForecast** - Hierarchical and grouped time series reconciliation
3. **NeuralForecast** - Deep learning models for forecasting

### Key Capabilities

**Hierarchical Forecasting:**
- Cross-sectional aggregations (categories, brands, geographical groupings)
- Temporal aggregations (weeks, months, years)
- Coherent forecasts across all levels (necessary for consistent decision-making)

**Reconciliation Methods:**
- **BottomUp**: Simple addition to upper levels
- **TopDown**: Distributes top-level forecasts through hierarchies
- **MiddleOut**: Anchors predictions in middle level
- **MinTrace**: Minimizes total forecast variance
- **ERM**: Optimizes reconciliation matrix with L1 regularization

**Probabilistic Methods:**
- **Normality**: MinTrace variance-covariance under normality assumption
- **Bootstrap**: Generates distribution of reconciled predictions
- **PERMBU**: Reconciles predictions with rank permutation copulas

**Why Nixtla for FoodFlow OS:**
1. **Hierarchical Structure Matches Use Case:**
   - SKU × Location × Channel × Time
   - Brand → Category → Product → SKU
   - Region → DC → Store
   
2. **Probabilistic Forecasts:**
   - Not just point estimates but full distributions (P10, P50, P90)
   - Critical for inventory optimization and risk management
   
3. **Performance:**
   - Optimized for high performance and scalability
   - Can handle thousands of SKUs across hundreds of locations
   
4. **Integration:**
   - Works seamlessly with pandas DataFrames
   - Easy integration with feature stores
   - Compatible with MLOps pipelines

5. **Active Development:**
   - Latest version 1.3.1 (November 2025)
   - Strong community and documentation
   - Apache 2.0 license

### Alternative Frameworks Considered

**Prophet (Meta):**
- Good for single time series
- Lacks native hierarchical reconciliation
- Less performant at scale

**Darts (Unit8):**
- Comprehensive forecasting library
- More complex API
- Heavier dependencies

**sktime:**
- Scikit-learn compatible
- Good for research
- Less optimized for production scale

### Implementation Approach for FoodFlow OS

**Architecture:**
```
Feature Store (TimescaleDB + PostgreSQL)
    ↓
StatsForecast (Base Models: AutoARIMA, ETS, Theta, etc.)
    ↓
HierarchicalForecast (Reconciliation: MinTrace, BottomUp, TopDown)
    ↓
Forecast Service API
    ↓
Workspace UIs (BrandOps, RetailOps, PlantOps)
```

**Forecast Hierarchy for FoodFlow:**
```
Total (All Products, All Locations)
├── By Brand
│   ├── By Category
│   │   ├── By Product
│   │   │   └── By SKU
│   │   │       └── By Location
│   │   │           └── By Channel
```

**Probabilistic Outputs:**
- P10 (pessimistic scenario)
- P50 (median/expected scenario)
- P90 (optimistic scenario)
- Full distribution for Monte Carlo simulations

---

## Edge Computing for Food Manufacturing

### Key Findings

**Why Edge AI is Critical for Food & Beverage:**

1. **Real-Time Requirements:**
   - Production lines operate at high speeds (thousands of units per minute)
   - Quality inspection must happen in real-time
   - Cannot tolerate cloud latency (100-500ms roundtrip)
   - Need <10ms response times for reject triggers

2. **Network Limitations:**
   - Many plants have limited or unreliable internet connectivity
   - Cannot depend on cloud for mission-critical operations
   - Store-and-forward required for data sync

3. **Data Volume:**
   - Cameras generate massive amounts of data (GB/hour per camera)
   - Sending all raw data to cloud is cost-prohibitive
   - Edge processing reduces bandwidth by 90%+

4. **Privacy & Security:**
   - Sensitive production data stays on-premise
   - Compliance with data sovereignty requirements
   - Reduced attack surface

### Edge AI Applications in Food Manufacturing

**1. Automated Visual Inspection:**
- Computer vision for defect detection
- Thousands of items per minute
- Accuracy exceeds human inspectors
- Detects: burns, breaks, underfill, overfill, contamination, bad seals

**2. Real-Time Quality Control:**
- Continuous monitoring of production lines
- Anomaly detection (fill weights, temperatures, speeds)
- Immediate alerts and corrective actions

**3. Predictive Maintenance:**
- Sensor data analysis for equipment health
- Predict failures before they occur
- Reduce unplanned downtime

**4. Supply Chain Optimization:**
- Real-time tracking and traceability
- Bottleneck prediction
- Quality concern early warnings

### Edge Computing Platforms for FoodFlow OS

**Recommended Platform: Azure IoT Edge (Microsoft)**

**Reasons:**
1. **Enterprise-Grade:**
   - Battle-tested in industrial environments
   - Strong security and compliance features
   - Excellent documentation and support

2. **Container-Based:**
   - Deploy models as Docker containers
   - Easy updates and rollbacks
   - Consistent dev/prod environments

3. **AI/ML Support:**
   - Native integration with Azure ML
   - ONNX runtime for model inference
   - GPU acceleration support

4. **OPC UA Integration:**
   - Built-in OPC UA module
   - Connects to PLCs, SCADA, MES systems
   - Industry-standard protocol

5. **Offline Capabilities:**
   - Store-and-forward messaging
   - Local storage and processing
   - Automatic sync when connectivity restored

6. **Management:**
   - Centralized device management
   - Remote deployment and monitoring
   - Fleet-wide updates

**Alternative Platforms:**

**AWS IoT Greengrass:**
- Similar capabilities to Azure IoT Edge
- Better if already using AWS ecosystem
- Lambda functions at the edge

**ClearBlade:**
- Purpose-built for industrial IoT
- Strong edge intelligence features
- Smaller ecosystem than Azure/AWS

**Eclipse ioFog (IBM-backed):**
- Open-source
- Microservices architecture
- Good for custom deployments

### Edge Hardware for FoodFlow OS

**Recommended: Industrial PCs with GPU**

**Specifications:**
- **CPU:** Intel Core i7 or AMD Ryzen 7 (8+ cores)
- **RAM:** 32GB DDR4/DDR5
- **Storage:** 512GB NVMe SSD
- **GPU:** NVIDIA Jetson AGX Orin or RTX A2000 (for vision inference)
- **Connectivity:** Ethernet (Gigabit), Wi-Fi 6, 4G/5G backup
- **I/O:** RS-485, RS-232, Digital I/O for PLC integration
- **Operating Temperature:** -20°C to 60°C (industrial grade)
- **Certifications:** UL, CE, IP65 (dust/water resistant)

**Vendors:**
- **Advantech:** IPC-610, ARK series
- **Axiomtek:** eBOX series
- **Siemens:** SIMATIC IPC series
- **Dell:** Edge Gateway 5200

### OPC UA Integration

**OPC UA (Open Platform Communications Unified Architecture):**
- Industry-standard protocol for industrial automation
- Connects to PLCs, SCADA, MES, ERP systems
- Secure, reliable, platform-independent

**OPC UA Gateways for FoodFlow OS:**
- **Advantech WISE-PaaS:** Industrial IoT gateway with OPC UA support
- **HMS Anybus X-gateway:** Modbus TCP to OPC UA/MQTT
- **Kepware KEPServerEX:** OPC UA server with 150+ driver protocols

**Integration Architecture:**
```
PLCs / SCADA / MES
    ↓ (OPC UA)
Edge Gateway (OPC UA Client)
    ↓
Edge Agent (FoodFlow OS)
    ↓ (MQTT/HTTPS)
Cloud (FoodFlow OS Core)
```

### Edge ML Model Deployment

**Model Formats:**
- **ONNX (Open Neural Network Exchange):** Cross-platform, optimized inference
- **TensorFlow Lite:** Lightweight for edge devices
- **PyTorch Mobile:** PyTorch models on edge

**Deployment Pipeline:**
```
Model Training (Cloud)
    ↓
Model Optimization (Quantization, Pruning)
    ↓
Model Conversion (ONNX/TFLite)
    ↓
Model Registry (Versioned)
    ↓
Edge Deployment (Azure IoT Edge / Docker)
    ↓
Edge Inference (Real-Time)
    ↓
Telemetry & Monitoring (Cloud)
```

**Few-Shot Learning for Dynamic SKU Onboarding:**
- Operator captures N images of good + defective product
- Label with simple UI
- Fine-tune model on edge or in cloud
- Deploy updated model to edge
- OS orchestrates entire pipeline

### Challenges in Edge AI Adoption

**1. Technical & Infrastructure:**
- Requires robust hardware and integration with existing systems
- Step-by-step approach recommended for food manufacturing (often outdated facilities)

**2. Data Privacy & Security:**
- Must comply with regulations
- Protect sensitive production data
- Implement defense-in-depth security

**3. Skill Gaps:**
- Need data scientists and ML engineers
- Training for plant operators and engineers
- Consider external partners for initial deployment

**4. Integration Complexity:**
- Integrating with legacy systems is time-consuming
- May require infrastructure upgrades
- Phased rollout recommended

---

## Recommendations for FoodFlow OS

### Forecasting Stack

**Core:**
- **Nixtla StatsForecast** - Base forecasting models
- **Nixtla HierarchicalForecast** - Hierarchical reconciliation
- **Nixtla NeuralForecast** - Deep learning models (optional, for advanced use cases)

**Supporting:**
- **PostgreSQL + TimescaleDB** - Feature store and historical data
- **Redis** - Caching for frequently accessed forecasts
- **FastAPI** - Forecast service API

**Deployment:**
- **Docker** - Containerized forecast services
- **Kubernetes** - Orchestration and scaling
- **MLflow** - Model registry and experiment tracking

### Edge Computing Stack

**Core:**
- **Azure IoT Edge** - Edge runtime and management
- **ONNX Runtime** - Model inference
- **Docker** - Containerization

**Supporting:**
- **OPC UA Gateway** - PLC/SCADA integration
- **MQTT Broker** - Message bus (Mosquitto or RabbitMQ)
- **InfluxDB** - Local time-series storage
- **Grafana** - Local monitoring dashboards

**Hardware:**
- **Advantech or Axiomtek Industrial PCs** - Edge compute
- **NVIDIA Jetson AGX Orin** - GPU for vision inference (if needed)

**Deployment:**
- **Azure IoT Hub** - Device management and provisioning
- **Azure Device Update** - OTA updates for edge devices

### Integration Architecture

```
Plant Floor:
    PLCs / SCADA / MES (OPC UA)
        ↓
    Edge Gateway (OPC UA Client)
        ↓
    Edge Agent (FoodFlow OS)
        - Vision inference (ONNX)
        - Anomaly detection
        - Store-and-forward
        ↓ (MQTT/HTTPS)
Cloud:
    FoodFlow OS Core
        - FoodGraph (Neo4j)
        - Forecast Service (Nixtla)
        - LLM Orchestration
        - Data Warehouse (PostgreSQL)
        ↓
    Workspace UIs
        - PlantOps
        - BrandOps
        - RetailOps
        - FSQ
```

---

## Next Research Topics

1. Computer vision frameworks for food manufacturing (YOLO, Mask R-CNN, few-shot learning)
2. Optimization engines (MILP solvers for production planning)
3. LLM orchestration and RAG architectures
4. Feature stores and MLOps platforms
5. Real-time data pipelines (Kafka, EventHub)
6. Multi-tenancy and cross-org data sharing patterns
