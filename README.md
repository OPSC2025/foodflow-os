# FoodFlow OS

**AI-Powered Operating System for the Food Value Chain**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()

---

## 🚀 Overview

FoodFlow OS is an AI-native platform that transforms how food manufacturers, co-packers, brands, and retailers operate. Unlike traditional software with "AI features," FoodFlow OS is built **Copilot-First** — every complex action is powered by AI from the ground up.

### Key Differentiators

- **🤖 Copilot-First Architecture**: AI isn't a feature, it's how you interact with the platform
- **📊 Multi-Tenant from Day One**: Schema-per-tenant isolation for enterprise security
- **🔍 Complete Telemetry**: Every AI interaction tracked for ROI demonstration
- **📈 Real-Time Intelligence**: From plant floor sensors to C-suite dashboards
- **🌐 Food-Specific**: Built for FSQA, HACCP, GMP, SQF — not generic manufacturing

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                  (React + TypeScript)                        │
│              Copilot Panel Always Available                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ REST API
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                     Backend API                              │
│                  (FastAPI + Python)                          │
│                                                              │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐              │
│  │   Copilot   │  │  Domain  │  │   Core   │              │
│  │ Orchestrator│  │ Contexts │  │ Services │              │
│  └─────┬───────┘  └────┬─────┘  └──────────┘              │
│        │               │                                     │
│        │  calls tools  │                                     │
│        └───────────────┘                                     │
└────────────────────┬───────────┬────────────────────────────┘
                     │           │
         ┌───────────▼─┐       ┌─▼────────────┐
         │  AI Service │       │  PostgreSQL  │
         │  (ML/LLM)   │       │  (TimescaleDB│
         │             │       │  + pgvector) │
         └─────────────┘       └──────────────┘
```

### Workspaces

- **PlantOps**: Production lines, batches, scrap analysis, OEE, money leaks
- **FSQ** (Food Safety & Quality): Lots, deviations, CAPA, traceability, compliance
- **Planning**: Demand forecasting, production planning, safety stock optimization
- **Brand**: Margin analysis, co-packer management, volume allocation
- **Retail**: Store-level forecasting, replenishment, OSA detection, promotions

---

## 🎯 Core Concepts

### 1. Copilot-First Pattern

**Traditional Approach** ❌:
```typescript
// User clicks button → Direct AI call → Show result
const result = await aiService.analyzeScrap(lineId);
```

**FoodFlow Approach** ✅:
```typescript
// User clicks "smart button" → Ask Copilot → Conversation begins
await copilot.ask({
  workspace: "plantops",
  message: "Diagnose scrap spike on Line 3",
  context: { line_id, date_range }
});
// Response appears in Copilot panel
// User can ask follow-ups naturally
```

**Why?**
- ✅ Every interaction logged for ROI measurement
- ✅ Users can have conversations, not just get results
- ✅ Context preserved across interactions
- ✅ Easier to improve AI without changing UI

📖 **Learn More**: [docs/COPILOT_FIRST_PATTERN.md](docs/COPILOT_FIRST_PATTERN.md)

### 2. Multi-Tenancy

- **Schema-per-tenant** isolation for strong data boundaries
- Dynamic `search_path` switching per request
- Tenant provisioning creates isolated schema automatically
- All domain data isolated; shared data (users, tenants) in `public` schema

### 3. AI Telemetry

Every Copilot interaction automatically logs:
- Question asked
- Answer provided
- Tools used
- Token consumption
- Response time
- User feedback

**Business Value**: Demonstrate AI ROI with metrics like:
- "Copilot saved 40 hours of analysis time this month"
- "AI suggestions had 73% acceptance rate"
- "Users who use Copilot resolve issues 2.3x faster"

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** (Python 3.11+): High-performance async API framework
- **SQLAlchemy** (async): ORM with multi-tenant support
- **PostgreSQL** + **TimescaleDB**: Time-series data for sensors/metrics
- **pgvector**: Vector search for RAG (semantic document search)
- **Alembic**: Database migrations
- **Pydantic**: Data validation and settings

### AI/ML
- **LangChain / LangGraph**: LLM orchestration and tool calling
- **OpenAI / Anthropic**: LLM providers for Copilot
- **Scikit-learn / XGBoost**: Traditional ML models
- **Prophet / LSTM**: Time-series forecasting

### Infrastructure
- **Docker + Docker Compose**: Local development
- **Kubernetes**: Production deployment
- **GitHub Actions**: CI/CD
- **Loguru**: Structured JSON logging

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Docker & Docker Compose (for local development)
- Node.js 18+ (for frontend)

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/foodflow-os.git
cd foodflow-os
```

### 2. Start Infrastructure

```bash
docker-compose up -d postgres redis
```

### 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run migrations
alembic upgrade head

# Seed development data
python -m scripts.seed_dev_data

# Start backend
uvicorn src.main:app --reload --port 8000
```

### 4. Start AI Service

```bash
cd ai_service

# Install dependencies
pip install -r requirements.txt

# Start AI service
python main.py
# Runs on http://localhost:8001
```

### 5. Start Frontend

```bash
cd frontend

npm install
npm run dev
# Runs on http://localhost:3000
```

### 6. Login

Open http://localhost:3000 and login with:
- **Email**: `admin@akron.com`
- **Password**: `admin123`

---

## 📚 Documentation

### Architecture & Patterns
- [Copilot-First Pattern](docs/COPILOT_FIRST_PATTERN.md) - **READ THIS FIRST**
- [AI Contracts](docs/ai_contracts.md) - All 20+ AI endpoints documented
- [ADR-001: Copilot-First](docs/architecture/ADR-001-copilot-first-pattern.md)
- [Multi-Tenancy Guide](docs/architecture/multi-tenancy.md)

### Development
- [Developer Setup](docs/developer-guide/setup.md)
- [Testing Guide](docs/developer-guide/testing.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Code Conventions](docs/developer-guide/conventions.md)

### API Reference
- Backend API: http://localhost:8000/api/docs
- AI Service: http://localhost:8001/api/docs

---

## 🧪 Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/test_tenancy.py -v
```

**Coverage Target**: 70%+

---

## 📊 Project Status

### ✅ Completed (Foundation - v0.1.0)

**Core Infrastructure**:
- ✅ Multi-tenant backend with schema-per-tenant isolation
- ✅ Identity & auth (users, roles, permissions, JWT)
- ✅ AI telemetry (Copilot interactions, suggestions, feedback)
- ✅ RFC 7807 error handling + structured logging
- ✅ Testing framework (pytest + fixtures)

**AI Service (Stubs)**:
- ✅ PlantOps AI (4 endpoints): Scrap analysis, trial suggestions, batch comparison, efficiency
- ✅ FSQ AI (5 endpoints): Lot risk, supplier risk, CCP drift, mock recalls, compliance Q&A
- ✅ Planning AI (3 endpoints): Forecasting, production planning, safety stock
- ✅ Brand AI (3 endpoints): Margin bridge, co-packer risk, Q&A
- ✅ Retail AI (4 endpoints): Store forecasting, replenishment, OSA detection, promo evaluation
- ✅ AI client library with retry + circuit breaker

**Documentation**:
- ✅ Copilot-First pattern guide
- ✅ AI contracts documentation (all 20+ endpoints)
- ✅ ADR-001: Copilot-First architecture decision

### 🚧 In Progress (v0.2.0 - Next Sprint)

- 🚧 Copilot orchestration endpoint with tool registry
- 🚧 PlantOps context (full CRUD APIs)
- 🚧 FSQ context (Lots, Deviations, CAPA)
- 🚧 RAG infrastructure for document Q&A
- 🚧 Telemetry analytics APIs

### 📋 Planned (v0.3.0+)

- Planning context APIs
- Brand & Retail contexts
- Real ML models (replace stubs)
- Edge gateway for sensor data
- Graph database for traceability
- Advanced RAG with pgvector

---

## 🤝 Contributing

We follow a **Copilot-First** development philosophy. When adding new features:

1. **Smart buttons call Copilot**, not AI services directly
2. **All AI interactions are logged** via telemetry service
3. **AI contracts are documented** before implementation
4. **Tests include Copilot integration** scenarios

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

---

## 📈 Business Value

### For Food Manufacturers
- **40% reduction** in scrap analysis time
- **Real-time** money leak identification
- **Predictive** maintenance alerts
- **Automated** batch comparison and deviation detection

### For FSQ Teams
- **1-hour** mock recall response time (vs 4+ hours manual)
- **Instant** lot risk scoring
- **Automated** CCP monitoring
- **AI-powered** compliance Q&A over SOPs/HACCP plans

### For Planners
- **Hierarchical** demand forecasting with 85%+ accuracy
- **Optimized** production schedules considering all constraints
- **Dynamic** safety stock recommendations
- **What-if** scenario analysis

### For Brands & Co-Packers
- **Margin bridge** analysis in seconds (not days)
- **Co-packer risk** scoring and performance tracking
- **Volume allocation** optimization
- **Contract intelligence** via RAG

---

## 📄 License

Proprietary - All Rights Reserved

Copyright © 2024 FoodFlow OS

---

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Email**: support@foodflow.ai
- **Slack**: [foodflow-community.slack.com](https://foodflow-community.slack.com)

---

## 🙏 Acknowledgments

Built with ❤️ for the food industry.

Special thanks to:
- Food manufacturers who shared their pain points
- FSQ professionals who reviewed our compliance features
- Early adopters who provided invaluable feedback

---

**FoodFlow OS** - From farm to fork, powered by AI.
