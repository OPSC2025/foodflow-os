# FoodFlow OS Backend

AI-driven operating system for food manufacturing networks - Backend API

## Architecture

- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL with async SQLAlchemy 2.0
- **Authentication**: JWT with refresh tokens
- **Multi-tenancy**: Schema-per-tenant isolation
- **Events**: Transactional outbox pattern
- **API Style**: RESTful with OpenAPI documentation

## Project Structure

```
backend/
├── src/
│   ├── main.py                          # FastAPI application entry point
│   ├── core/                            # Core infrastructure
│   │   ├── config.py                    # Configuration management
│   │   ├── database.py                  # Database setup and session management
│   │   ├── security.py                  # Authentication and authorization
│   │   └── events.py                    # Domain event system
│   └── contexts/                        # Bounded contexts (DDD)
│       ├── identity/                    # Identity & Access Management
│       │   └── domain/
│       │       └── models.py            # User, Tenant, ApiKey models
│       └── plant_ops/                   # PlantOps bounded context
│           ├── domain/
│           │   ├── models.py            # Domain models
│           │   └── schemas.py           # Pydantic schemas
│           ├── application/
│           │   └── services.py          # Business logic services
│           ├── infrastructure/
│           │   └── repositories.py      # Data access layer
│           └── api/                     # HTTP endpoints
│               ├── lines.py             # Production lines API
│               ├── batches.py           # Production batches API
│               └── sensors.py           # Sensors API
├── pyproject.toml                       # Python dependencies
├── Dockerfile                           # Container image
└── .env.example                         # Environment variables template
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for caching)

### Local Development

1. **Install dependencies**:
   ```bash
   cd backend
   pip install poetry
   poetry install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start database** (using Docker Compose from project root):
   ```bash
   cd ..
   docker-compose up postgres redis -d
   ```

4. **Run migrations**:
   ```bash
   # TODO: Add Alembic migrations
   ```

5. **Start development server**:
   ```bash
   poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access API documentation**:
   - Swagger UI: http://localhost:8000/api/docs
   - ReDoc: http://localhost:8000/api/redoc
   - OpenAPI JSON: http://localhost:8000/api/openapi.json

### Docker Development

```bash
# From project root
docker-compose up backend -d

# View logs
docker-compose logs -f backend

# Access shell
docker-compose exec backend bash
```

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - API information

### PlantOps - Production Lines
- `POST /api/v1/plant-ops/lines` - Create line
- `GET /api/v1/plant-ops/lines` - List lines
- `GET /api/v1/plant-ops/lines/{id}` - Get line
- `PATCH /api/v1/plant-ops/lines/{id}` - Update line
- `POST /api/v1/plant-ops/lines/{id}/status` - Update line status
- `DELETE /api/v1/plant-ops/lines/{id}` - Delete line

### PlantOps - Production Batches
- `POST /api/v1/plant-ops/batches` - Create batch
- `GET /api/v1/plant-ops/batches` - List batches
- `GET /api/v1/plant-ops/batches/{id}` - Get batch
- `POST /api/v1/plant-ops/batches/{id}/start` - Start batch
- `POST /api/v1/plant-ops/batches/{id}/complete` - Complete batch
- `PATCH /api/v1/plant-ops/batches/{id}` - Update batch

### PlantOps - Sensors
- `POST /api/v1/plant-ops/sensors` - Create sensor
- `GET /api/v1/plant-ops/sensors` - List sensors
- `GET /api/v1/plant-ops/sensors/{id}` - Get sensor
- `PATCH /api/v1/plant-ops/sensors/{id}` - Update sensor
- `DELETE /api/v1/plant-ops/sensors/{id}` - Delete sensor
- `POST /api/v1/plant-ops/sensors/{id}/readings` - Record reading
- `POST /api/v1/plant-ops/sensors/readings/bulk` - Bulk record readings
- `GET /api/v1/plant-ops/sensors/{id}/readings` - Get readings

## Key Features

### Multi-Tenancy
- Schema-per-tenant isolation for data security
- Automatic tenant context from JWT token
- Tenant provisioning utilities

### Authentication
- JWT access tokens (30 min expiry)
- JWT refresh tokens (7 day expiry)
- API key support for programmatic access
- Role-based access control (RBAC)

### Domain Events
- Transactional outbox pattern for reliability
- Event store for querying history
- Pre-defined events: BatchCreated, BatchStarted, BatchCompleted, LineDowntime, ScrapDetected, AnomalyDetected

### Real-time Capabilities
- Sensor data ingestion with anomaly detection
- Bulk operations for high-throughput scenarios
- Time-series optimized queries

### OEE Calculation
- Automatic calculation from availability, performance, quality
- Scrap rate and yield rate tracking
- Cost tracking (labor, material, scrap)

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints everywhere
- Async/await for I/O operations
- Pydantic for validation

### Testing
```bash
# Run tests
poetry run pytest

# With coverage
poetry run pytest --cov=src --cov-report=html
```

### Database Migrations
```bash
# Create migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

## Production Deployment

### Environment Variables
See `.env.example` for required configuration.

### Database
- Use connection pooling (configured in settings)
- Enable SSL for connections
- Regular backups
- Consider read replicas for scaling

### Security
- Change `SECRET_KEY` to a strong random value
- Use HTTPS only
- Enable rate limiting
- Configure CORS appropriately
- Use secrets management (e.g., AWS Secrets Manager)

### Monitoring
- Enable Prometheus metrics
- Configure Sentry for error tracking
- Set up structured logging
- Monitor database performance

### Scaling
- Horizontal scaling with load balancer
- Separate read/write database connections
- Redis for caching and sessions
- Consider async task queue (Celery) for heavy operations

## Next Steps (Arc 1 Roadmap)

- [ ] Add Alembic database migrations
- [ ] Implement authentication endpoints
- [ ] Add analytics and metrics endpoints
- [ ] Build anomaly detection ML model
- [ ] Create LLM Gateway for Copilot
- [ ] Add WebSocket support for real-time updates
- [ ] Implement frontend dashboard
- [ ] Set up CI/CD pipeline
- [ ] Add comprehensive test suite
- [ ] Performance optimization and load testing

## License

Proprietary - All rights reserved
