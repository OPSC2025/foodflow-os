"""
Database initialization script for FoodFlow OS.

Creates initial schema and optionally seeds sample data.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.core.config import settings
from src.core.database import async_engine, init_db
from src.core.security import get_password_hash


async def create_schema():
    """Create database schema using Alembic migrations."""
    print("Creating database schema...")
    
    # Import all models to ensure they're registered
    from src.contexts.identity.domain import models as identity_models
    from src.contexts.plant_ops.domain import models as plant_ops_models
    
    # Initialize database (creates tables)
    await init_db()
    
    print("✓ Database schema created successfully")


async def seed_sample_data():
    """Seed sample data for development/testing."""
    print("\nSeeding sample data...")
    
    from datetime import datetime, timedelta
    from uuid import uuid4
    
    from sqlalchemy.ext.asyncio import AsyncSession
    
    from src.contexts.identity.domain.models import Tenant, User
    from src.contexts.plant_ops.domain.models import ProductionLine, Sensor
    from src.core.database import async_session_maker
    
    async with async_session_maker() as session:
        # Create sample tenant
        tenant_id = uuid4()
        tenant = Tenant(
            id=tenant_id,
            name="Demo Food Manufacturing Co.",
            slug="demo-food-mfg",
            is_active=True,
            subscription_tier="enterprise",
            subscription_expires_at=datetime.utcnow() + timedelta(days=365),
            settings={
                "timezone": "America/New_York",
                "currency": "USD",
                "language": "en",
            },
        )
        session.add(tenant)
        
        # Create sample admin user
        admin_user = User(
            id=uuid4(),
            tenant_id=tenant_id,
            email="admin@demo-food-mfg.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
            roles=["admin", "plant_ops", "fsq", "planning"],
            permissions=["*"],
        )
        session.add(admin_user)
        
        # Create sample operator user
        operator_user = User(
            id=uuid4(),
            tenant_id=tenant_id,
            email="operator@demo-food-mfg.com",
            hashed_password=get_password_hash("operator123"),
            full_name="Plant Operator",
            is_active=True,
            is_superuser=False,
            roles=["plant_ops"],
            permissions=["plant_ops:read", "plant_ops:write"],
        )
        session.add(operator_user)
        
        # Create sample production lines
        lines_data = [
            {
                "line_number": "LINE-01",
                "name": "Packaging Line 1",
                "description": "Primary packaging line for frozen products",
                "capacity_per_hour": 1000,
                "target_speed": 16.67,
            },
            {
                "line_number": "LINE-02",
                "name": "Packaging Line 2",
                "description": "Secondary packaging line for frozen products",
                "capacity_per_hour": 800,
                "target_speed": 13.33,
            },
            {
                "line_number": "LINE-03",
                "name": "Processing Line 1",
                "description": "Primary processing line for raw materials",
                "capacity_per_hour": 500,
                "target_speed": 8.33,
            },
        ]
        
        line_ids = []
        for line_data in lines_data:
            line_id = uuid4()
            line_ids.append(line_id)
            line = ProductionLine(
                id=line_id,
                tenant_id=tenant_id,
                status="idle",
                is_active=True,
                last_maintenance_date=datetime.utcnow() - timedelta(days=30),
                next_maintenance_date=datetime.utcnow() + timedelta(days=60),
                **line_data,
            )
            session.add(line)
        
        # Create sample sensors for each line
        sensor_types = [
            ("temperature", "Temperature", "°C", 0, 100),
            ("pressure", "Pressure", "PSI", 0, 150),
            ("flow_rate", "Flow Rate", "L/min", 0, 500),
            ("vibration", "Vibration", "mm/s", 0, 50),
        ]
        
        for i, line_id in enumerate(line_ids):
            for j, (sensor_type, name, unit, min_val, max_val) in enumerate(sensor_types):
                sensor = Sensor(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    line_id=line_id,
                    sensor_code=f"SENSOR-{i+1:02d}-{j+1:02d}",
                    sensor_type=sensor_type,
                    name=f"{name} - Line {i+1}",
                    description=f"{name} sensor for production line {i+1}",
                    unit=unit,
                    min_value=min_val,
                    max_value=max_val,
                    is_active=True,
                    last_calibration_date=datetime.utcnow() - timedelta(days=90),
                    next_calibration_date=datetime.utcnow() + timedelta(days=90),
                )
                session.add(sensor)
        
        await session.commit()
        
        print("✓ Sample data seeded successfully")
        print(f"\n  Tenant: {tenant.name} ({tenant.slug})")
        print(f"  Admin: {admin_user.email} / admin123")
        print(f"  Operator: {operator_user.email} / operator123")
        print(f"  Production Lines: {len(lines_data)}")
        print(f"  Sensors: {len(lines_data) * len(sensor_types)}")


async def check_database_connection():
    """Check if database connection is working."""
    print("Checking database connection...")
    
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


async def main():
    """Main initialization function."""
    print("=" * 60)
    print("FoodFlow OS - Database Initialization")
    print("=" * 60)
    print(f"\nDatabase URL: {settings.DATABASE_URL.split('@')[1]}")  # Hide credentials
    print()
    
    # Check connection
    if not await check_database_connection():
        print("\nPlease ensure PostgreSQL is running and accessible.")
        sys.exit(1)
    
    # Create schema
    await create_schema()
    
    # Seed sample data if requested
    if "--seed" in sys.argv or "-s" in sys.argv:
        await seed_sample_data()
    else:
        print("\nSkipping sample data seeding.")
        print("Run with --seed flag to add sample data.")
    
    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the backend: uvicorn src.main:app --reload")
    print("2. Access API docs: http://localhost:8000/api/docs")
    print("3. Login with sample credentials (if seeded)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
