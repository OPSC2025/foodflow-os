"""
Pytest fixtures for testing.

Provides test database, test client, and mock data for tests.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.core.database import Base, get_db_session
from src.core.config import get_settings
from src.core.tenancy import Tenant
from src.contexts.identity.domain.models import User, Role, Permission
from src.core.security import hash_password, create_access_token


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    settings = get_settings()
    test_db_url = settings.get_test_database_url
    
    engine = create_async_engine(
        test_db_url,
        echo=False,
        future=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    
    # Override database dependency
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    # Create client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    
    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_tenant(test_session: AsyncSession) -> Tenant:
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Tenant",
        slug="test",
        schema_name="tenant_test",
        is_active=True,
        settings={},
    )
    test_session.add(tenant)
    await test_session.commit()
    await test_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_permission(test_session: AsyncSession) -> Permission:
    """Create a test permission."""
    perm = Permission(
        name="test.read",
        resource="test",
        action="read",
        description="Test permission",
    )
    test_session.add(perm)
    await test_session.commit()
    await test_session.refresh(perm)
    return perm


@pytest_asyncio.fixture
async def test_role(test_session: AsyncSession, test_tenant: Tenant, test_permission: Permission) -> Role:
    """Create a test role."""
    role = Role(
        tenant_id=test_tenant.id,
        name="test_role",
        description="Test role",
        is_system=False,
    )
    role.permissions = [test_permission]
    test_session.add(role)
    await test_session.commit()
    await test_session.refresh(role)
    return role


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession, test_tenant: Tenant, test_role: Role) -> User:
    """Create a test user."""
    user = User(
        tenant_id=test_tenant.id,
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    user.roles = [test_role]
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest.fixture
def test_access_token(test_user: User, test_tenant: Tenant) -> str:
    """Create test access token."""
    return create_access_token(
        subject=str(test_user.id),
        tenant_id=str(test_tenant.id),
        tenant_schema=test_tenant.schema_name,
        email=test_user.email,
        role="test_role",
    )


@pytest.fixture
def auth_headers(test_access_token: str) -> dict:
    """Create authorization headers for authenticated requests."""
    return {
        "Authorization": f"Bearer {test_access_token}",
    }


# Mock AI service responses
@pytest.fixture
def mock_ai_scrap_analysis():
    """Mock AI service response for scrap analysis."""
    return {
        "scrap_analysis": {
            "top_reasons": [
                {"reason": "Temperature deviation", "percentage": 45.0},
                {"reason": "Material defect", "percentage": 30.0},
                {"reason": "Equipment malfunction", "percentage": 25.0},
            ],
            "trend": "increasing",
            "recommendations": [
                "Check heating element calibration",
                "Review incoming material quality",
                "Schedule equipment maintenance",
            ],
        },
        "confidence": 0.85,
        "model_version": "v1.0-stub",
    }


@pytest.fixture
def mock_ai_trial_suggestion():
    """Mock AI service response for trial suggestion."""
    return {
        "trial_suggestion": {
            "parameters": {
                "line_speed": 95.0,
                "temperature": 180.0,
                "pressure": 2.5,
            },
            "expected_outcome": "Reduce scrap rate by 15%",
            "risks": ["Minor quality variation in first 100 units"],
        },
        "confidence": 0.78,
        "model_version": "v1.0-stub",
    }


@pytest.fixture
def mock_ai_lot_risk():
    """Mock AI service response for lot risk calculation."""
    return {
        "risk_score": 0.35,
        "risk_level": "medium",
        "risk_factors": [
            {"factor": "Supplier history", "impact": 0.15},
            {"factor": "Process deviation", "impact": 0.20},
        ],
        "affected_products": ["SKU-123", "SKU-456"],
        "recommended_actions": [
            "Increase testing frequency",
            "Review supplier certifications",
        ],
        "confidence": 0.82,
        "model_version": "v1.0-stub",
    }

