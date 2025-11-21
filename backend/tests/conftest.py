"""
Pytest configuration and fixtures for FoodFlow OS tests.

Provides reusable fixtures for:
- Database connections and transactions
- Authentication and tenant context
- Sample data (tenants, users, domain entities)
- Mock AI service responses
- HTTP clients
"""

import asyncio
import uuid
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.config import get_settings
from src.core.database import Base, get_db
from src.main import app
from src.contexts.identity.domain.models import Tenant, User
from src.contexts.plant_ops.domain.models import ProductionLine, Batch
from src.contexts.fsq.domain.models import Lot, Supplier, Ingredient
from src.core.telemetry.models import CopilotInteraction


settings = get_settings()

# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new database session for a test.
    
    Uses nested transaction to rollback after each test.
    """
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with database session override.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# Sample data fixtures


@pytest_asyncio.fixture
async def sample_tenant(db_session: AsyncSession) -> Tenant:
    """Create a sample tenant for testing."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Tenant",
        slug="test-tenant",
        schema_name="tenant_test",
        is_active=True,
        settings={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession, sample_tenant: Tenant) -> User:
    """Create a sample user for testing."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="$2b$12$test_hash",  # Dummy hash
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_production_line(db_session: AsyncSession, sample_tenant: Tenant) -> ProductionLine:
    """Create a sample production line for testing."""
    line = ProductionLine(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        name="Test Line 1",
        plant_id=uuid.uuid4(),  # Dummy plant ID
        status="running",
        target_rate_per_hour=1000.0,
        efficiency_pct=85.5,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(line)
    await db_session.commit()
    await db_session.refresh(line)
    return line


@pytest_asyncio.fixture
async def sample_batch(
    db_session: AsyncSession,
    sample_tenant: Tenant,
    sample_production_line: ProductionLine
) -> Batch:
    """Create a sample batch for testing."""
    batch = Batch(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        batch_number="BATCH-001",
        line_id=sample_production_line.id,
        product_code="PROD-123",
        quantity_planned=1000.0,
        quantity_produced=950.0,
        status="completed",
        start_time=datetime.utcnow() - timedelta(hours=2),
        end_time=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)
    return batch


@pytest_asyncio.fixture
async def sample_supplier(db_session: AsyncSession, sample_tenant: Tenant) -> Supplier:
    """Create a sample supplier for testing."""
    supplier = Supplier(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        name="Test Supplier Inc",
        supplier_code="SUP-001",
        contact_email="supplier@example.com",
        risk_score=0.25,
        is_approved=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    return supplier


@pytest_asyncio.fixture
async def sample_ingredient(db_session: AsyncSession, sample_tenant: Tenant) -> Ingredient:
    """Create a sample ingredient for testing."""
    ingredient = Ingredient(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        name="Test Ingredient",
        ingredient_code="ING-001",
        category="raw_material",
        unit_of_measure="kg",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(ingredient)
    await db_session.commit()
    await db_session.refresh(ingredient)
    return ingredient


@pytest_asyncio.fixture
async def sample_lot(
    db_session: AsyncSession,
    sample_tenant: Tenant,
    sample_ingredient: Ingredient,
    sample_supplier: Supplier,
) -> Lot:
    """Create a sample lot for testing."""
    lot = Lot(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        lot_number="LOT-001",
        ingredient_id=sample_ingredient.id,
        supplier_id=sample_supplier.id,
        quantity=1000.0,
        unit="kg",
        production_date=datetime.utcnow() - timedelta(days=7),
        expiration_date=datetime.utcnow() + timedelta(days=365),
        status="approved",
        quality_status="passed",
        on_hold=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(lot)
    await db_session.commit()
    await db_session.refresh(lot)
    return lot


@pytest_asyncio.fixture
async def sample_copilot_interaction(
    db_session: AsyncSession,
    sample_tenant: Tenant,
    sample_user: User,
) -> CopilotInteraction:
    """Create a sample Copilot interaction for testing."""
    interaction = CopilotInteraction(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        user_id=sample_user.id,
        workspace="plantops",
        question="Why is Line 3 having so much scrap?",
        answer="Line 3 is experiencing increased scrap due to temperature fluctuations.",
        tools_used=["get_line_status", "analyze_scrap"],
        tokens_used=1250,
        duration_ms=2340.5,
        metadata={},
        created_at=datetime.utcnow(),
    )
    db_session.add(interaction)
    await db_session.commit()
    await db_session.refresh(interaction)
    return interaction


# Mock AI service responses


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "message": {
            "role": "assistant",
            "content": "This is a test response from the AI.",
        },
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
        "finish_reason": "stop",
    }


@pytest.fixture
def mock_llm_function_call_response():
    """Mock LLM response with function call."""
    return {
        "message": {
            "role": "assistant",
            "content": None,
        },
        "function_call": {
            "name": "get_line_status",
            "arguments": {"line_id": "test-line-id"},
        },
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 30,
            "total_tokens": 150,
        },
        "finish_reason": "function_call",
    }


@pytest.fixture
def mock_tool_result():
    """Mock tool execution result."""
    return {
        "success": True,
        "result": {
            "line_id": "test-line-id",
            "name": "Test Line",
            "status": "running",
            "efficiency_pct": 85.5,
        },
    }


# Authentication helpers


@pytest.fixture
def auth_headers(sample_user: User) -> dict:
    """Generate authentication headers for testing."""
    # In real implementation, generate proper JWT
    return {
        "Authorization": "Bearer test-token",
        "x-tenant-id": str(sample_user.tenant_id),
    }


# Test markers for pytest


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
