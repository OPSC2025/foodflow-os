"""
Seed script for development data.

Creates:
- Demo tenants (Akron facility + another demo company)
- Standard permissions
- Standard roles per tenant
- Sample users with different roles
- Sample PlantOps data (plants, lines, batches)
- Sample FSQ data (lots, deviations)

Usage:
    python -m scripts.seed_dev_data
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.core.config import get_settings
from src.core.security import hash_password
from src.core.tenancy import Tenant, TenantProvisioningService
from src.contexts.identity.domain.models import (
    User, Role, Permission,
    STANDARD_PERMISSIONS, STANDARD_ROLES
)
from src.contexts.plant_ops.domain.models import (
    Plant, ProductionLine, ProductionBatch, ScrapEvent,
    LineStatus, BatchStatus
)


settings = get_settings()


async def seed_permissions(session: AsyncSession):
    """Seed standard permissions."""
    print("🔐 Seeding permissions...")
    
    for perm_data in STANDARD_PERMISSIONS:
        # Check if exists
        from sqlalchemy import select
        result = await session.execute(
            select(Permission).where(Permission.name == perm_data["name"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            perm = Permission(
                name=perm_data["name"],
                resource=perm_data["resource"],
                action=perm_data["action"],
                description=perm_data.get("description"),
            )
            session.add(perm)
    
    await session.commit()
    print(f"✓ Created {len(STANDARD_PERMISSIONS)} permissions")


async def seed_tenants(session: AsyncSession) -> dict:
    """Seed demo tenants."""
    print("🏢 Seeding tenants...")
    
    tenant_service = TenantProvisioningService(session)
    tenants = {}
    
    # Akron facility
    akron = await tenant_service.create_tenant(
        name="Akron Food Manufacturing",
        slug="akron",
        contact_email="admin@akron-foods.com",
        contact_name="John Smith",
        settings={
            "timezone": "America/New_York",
            "locale": "en_US",
            "features": ["plantops", "fsq", "planning"],
        }
    )
    tenants["akron"] = akron
    print(f"✓ Created tenant: {akron.name} (schema: {akron.schema_name})")
    
    # Demo company
    demo = await tenant_service.create_tenant(
        name="Demo Foods Inc",
        slug="demo",
        contact_email="admin@demo-foods.com",
        contact_name="Jane Doe",
        settings={
            "timezone": "America/Los_Angeles",
            "locale": "en_US",
            "features": ["plantops", "fsq", "planning", "brand", "retail"],
        }
    )
    tenants["demo"] = demo
    print(f"✓ Created tenant: {demo.name} (schema: {demo.schema_name})")
    
    return tenants


async def seed_roles_for_tenant(session: AsyncSession, tenant_id):
    """Seed standard roles for a tenant."""
    from sqlalchemy import select
    
    # Get all permissions
    result = await session.execute(select(Permission))
    all_permissions = {p.name: p for p in result.scalars().all()}
    
    for role_name, role_config in STANDARD_ROLES.items():
        # Check if role exists
        result = await session.execute(
            select(Role).where(
                Role.tenant_id == tenant_id,
                Role.name == role_name,
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            role = Role(
                tenant_id=tenant_id,
                name=role_name,
                description=role_config["description"],
                is_system=True,
            )
            session.add(role)
            await session.flush()
            
            # Assign permissions
            # Expand wildcards like "plantops.plant.*" to all matching permissions
            role_permissions = []
            for perm_pattern in role_config["permissions"]:
                if "*" in perm_pattern:
                    # Wildcard matching
                    prefix = perm_pattern.replace(".*", "")
                    matching = [p for name, p in all_permissions.items() if name.startswith(prefix)]
                    role_permissions.extend(matching)
                else:
                    # Exact match
                    if perm_pattern in all_permissions:
                        role_permissions.append(all_permissions[perm_pattern])
            
            role.permissions = role_permissions
    
    await session.commit()


async def seed_users_for_tenant(session: AsyncSession, tenant_id, tenant_slug: str):
    """Seed sample users for a tenant."""
    print(f"👤 Seeding users for {tenant_slug}...")
    
    from sqlalchemy import select
    
    users_data = [
        {
            "email": f"admin@{tenant_slug}.com",
            "password": "admin123",
            "full_name": "Admin User",
            "roles": ["admin"],
        },
        {
            "email": f"operator@{tenant_slug}.com",
            "password": "operator123",
            "full_name": "Line Operator",
            "roles": ["operator"],
        },
        {
            "email": f"fsq@{tenant_slug}.com",
            "password": "fsq123",
            "full_name": "FSQ Manager",
            "roles": ["fsq_manager"],
        },
        {
            "email": f"planner@{tenant_slug}.com",
            "password": "planner123",
            "full_name": "Production Planner",
            "roles": ["planner"],
        },
    ]
    
    for user_data in users_data:
        # Check if user exists
        result = await session.execute(
            select(User).where(
                User.tenant_id == tenant_id,
                User.email == user_data["email"],
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            user = User(
                tenant_id=tenant_id,
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            await session.flush()
            
            # Assign roles
            result = await session.execute(
                select(Role).where(
                    Role.tenant_id == tenant_id,
                    Role.name.in_(user_data["roles"]),
                )
            )
            roles = list(result.scalars().all())
            user.roles = roles
            
            print(f"  ✓ Created user: {user.email} (roles: {', '.join(user_data['roles'])})")
    
    await session.commit()


async def seed_plantops_data(session: AsyncSession, tenant_id):
    """Seed PlantOps data (plants, lines, batches) for a tenant."""
    print(f"🏭 Seeding PlantOps data...")
    
    # Set search path to tenant schema
    tenant_schema = f"tenant_{str(tenant_id).replace('-', '_')}"
    # Note: This would need actual schema switching - simplified for now
    
    # Create plant
    plant = Plant(
        tenant_id=tenant_id,
        line_number="PLANT-01",
        name="Akron Main Plant",
        description="Primary production facility",
        plant_name="Akron Main",
        location="Akron, OH",
        design_speed=100.0,
        max_speed=120.0,
        min_speed=60.0,
        status=LineStatus.IDLE,
        is_active=True,
    )
    session.add(plant)
    await session.flush()
    
    # Create production lines
    lines_data = [
        {"name": "Sandwich Line 1", "line_type": "sandwich", "design_speed": 80.0},
        {"name": "Wrapper Line 1", "line_type": "wrapper", "design_speed": 100.0},
        {"name": "Packaging Line 1", "line_type": "packaging", "design_speed": 120.0},
    ]
    
    lines = []
    for i, line_data in enumerate(lines_data, 1):
        line = ProductionLine(
            tenant_id=tenant_id,
            line_number=f"LINE-{i:02d}",
            name=line_data["name"],
            plant_id=plant.id,
            plant_name=plant.name,
            design_speed=line_data["design_speed"],
            max_speed=line_data["design_speed"] * 1.2,
            min_speed=line_data["design_speed"] * 0.6,
            status=LineStatus.IDLE if i == 1 else LineStatus.RUNNING,
            current_speed=None if i == 1 else line_data["design_speed"],
            is_active=True,
        )
        session.add(line)
        lines.append(line)
    
    await session.flush()
    print(f"  ✓ Created plant: {plant.name}")
    print(f"  ✓ Created {len(lines)} production lines")
    
    # Create batches
    now = datetime.utcnow()
    batches_data = [
        {
            "line": lines[0],
            "batch_number": "BATCH-2024-001",
            "product_code": "SKU-123",
            "product_name": "Premium Sandwich",
            "status": BatchStatus.COMPLETED,
            "start": now - timedelta(days=2, hours=8),
            "end": now - timedelta(days=2, hours=2),
            "target_qty": 10000.0,
            "produced_qty": 9850.0,
            "good_qty": 9500.0,
            "scrap_qty": 350.0,
        },
        {
            "line": lines[1],
            "batch_number": "BATCH-2024-002",
            "product_code": "SKU-456",
            "product_name": "Classic Wrap",
            "status": BatchStatus.IN_PROGRESS,
            "start": now - timedelta(hours=3),
            "end": None,
            "target_qty": 8000.0,
            "produced_qty": 3500.0,
            "good_qty": 3400.0,
            "scrap_qty": 100.0,
        },
    ]
    
    for batch_data in batches_data:
        batch = ProductionBatch(
            tenant_id=tenant_id,
            batch_number=batch_data["batch_number"],
            line_id=batch_data["line"].id,
            product_code=batch_data["product_code"],
            product_name=batch_data["product_name"],
            status=batch_data["status"],
            planned_start_time=batch_data["start"],
            planned_end_time=batch_data["end"] or (batch_data["start"] + timedelta(hours=8)),
            actual_start_time=batch_data["start"],
            actual_end_time=batch_data["end"],
            target_quantity=batch_data["target_qty"],
            produced_quantity=batch_data["produced_qty"],
            good_quantity=batch_data["good_qty"],
            scrap_quantity=batch_data["scrap_qty"],
        )
        session.add(batch)
        
        # Add scrap events for completed batch
        if batch_data["status"] == BatchStatus.COMPLETED:
            await session.flush()
            
            scrap = ScrapEvent(
                tenant_id=tenant_id,
                batch_id=batch.id,
                event_time=batch_data["start"] + timedelta(hours=2),
                quantity=batch_data["scrap_qty"],
                scrap_type="quality_defect",
                scrap_reason="Temperature deviation",
                severity="medium",
                root_cause="Heating element malfunction",
                estimated_cost=batch_data["scrap_qty"] * 1.5,  # $1.50 per unit
                detected_by="operator",
            )
            session.add(scrap)
    
    await session.commit()
    print(f"  ✓ Created {len(batches_data)} batches with scrap events")


async def main():
    """Main seed function."""
    print("🌱 Starting database seeding...")
    print(f"Database: {settings.database_url}")
    print()
    
    # Create engine and session
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Seed permissions (global)
        await seed_permissions(session)
        print()
        
        # 2. Seed tenants
        tenants = await seed_tenants(session)
        print()
        
        # 3. For each tenant, seed roles and users
        for tenant_slug, tenant in tenants.items():
            print(f"📦 Setting up {tenant_slug}...")
            await seed_roles_for_tenant(session, tenant.id)
            print(f"  ✓ Created standard roles")
            
            await seed_users_for_tenant(session, tenant.id, tenant_slug)
            print()
        
        # 4. Seed PlantOps data for Akron
        if "akron" in tenants:
            await seed_plantops_data(session, tenants["akron"].id)
            print()
    
    await engine.dispose()
    
    print("✅ Database seeding completed!")
    print()
    print("📝 Sample credentials:")
    print("  Admin:    admin@akron.com / admin123")
    print("  Operator: operator@akron.com / operator123")
    print("  FSQ:      fsq@akron.com / fsq123")
    print("  Planner:  planner@akron.com / planner123")


if __name__ == "__main__":
    asyncio.run(main())

