"""
PlantOps context repository layer for database operations.

Repositories provide data access abstraction and encapsulate database queries.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.contexts.plant_ops.domain.models import (
    LineEvent,
    ProductionBatch,
    ProductionLine,
    ScrapEvent,
    Sensor,
    SensorReading,
)


class ProductionLineRepository:
    """Repository for ProductionLine operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create(self, line: ProductionLine) -> ProductionLine:
        """Create a new production line."""
        line.tenant_id = self.tenant_id
        self.session.add(line)
        await self.session.flush()
        await self.session.refresh(line)
        return line
    
    async def get_by_id(self, line_id: uuid.UUID) -> Optional[ProductionLine]:
        """Get a production line by ID."""
        stmt = select(ProductionLine).where(
            and_(
                ProductionLine.id == line_id,
                ProductionLine.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_line_number(self, line_number: str) -> Optional[ProductionLine]:
        """Get a production line by line number."""
        stmt = select(ProductionLine).where(
            and_(
                ProductionLine.line_number == line_number,
                ProductionLine.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[ProductionLine]:
        """List production lines with optional filters."""
        stmt = select(ProductionLine).where(ProductionLine.tenant_id == self.tenant_id)
        
        if status:
            stmt = stmt.where(ProductionLine.status == status)
        if is_active is not None:
            stmt = stmt.where(ProductionLine.is_active == is_active)
        
        stmt = stmt.order_by(ProductionLine.line_number).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count(
        self,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count production lines with optional filters."""
        stmt = select(func.count(ProductionLine.id)).where(
            ProductionLine.tenant_id == self.tenant_id
        )
        
        if status:
            stmt = stmt.where(ProductionLine.status == status)
        if is_active is not None:
            stmt = stmt.where(ProductionLine.is_active == is_active)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def update(self, line: ProductionLine) -> ProductionLine:
        """Update a production line."""
        await self.session.flush()
        await self.session.refresh(line)
        return line
    
    async def delete(self, line_id: uuid.UUID) -> bool:
        """Delete a production line."""
        line = await self.get_by_id(line_id)
        if line:
            await self.session.delete(line)
            await self.session.flush()
            return True
        return False


class ProductionBatchRepository:
    """Repository for ProductionBatch operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create(self, batch: ProductionBatch) -> ProductionBatch:
        """Create a new production batch."""
        batch.tenant_id = self.tenant_id
        self.session.add(batch)
        await self.session.flush()
        await self.session.refresh(batch)
        return batch
    
    async def get_by_id(self, batch_id: uuid.UUID) -> Optional[ProductionBatch]:
        """Get a production batch by ID."""
        stmt = (
            select(ProductionBatch)
            .options(selectinload(ProductionBatch.line))
            .where(
                and_(
                    ProductionBatch.id == batch_id,
                    ProductionBatch.tenant_id == self.tenant_id,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_batch_number(self, batch_number: str) -> Optional[ProductionBatch]:
        """Get a production batch by batch number."""
        stmt = (
            select(ProductionBatch)
            .options(selectinload(ProductionBatch.line))
            .where(
                and_(
                    ProductionBatch.batch_number == batch_number,
                    ProductionBatch.tenant_id == self.tenant_id,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[ProductionBatch]:
        """List production batches with optional filters."""
        stmt = (
            select(ProductionBatch)
            .options(selectinload(ProductionBatch.line))
            .where(ProductionBatch.tenant_id == self.tenant_id)
        )
        
        if line_id:
            stmt = stmt.where(ProductionBatch.line_id == line_id)
        if status:
            stmt = stmt.where(ProductionBatch.status == status)
        if start_date:
            stmt = stmt.where(ProductionBatch.actual_start_time >= start_date)
        if end_date:
            stmt = stmt.where(ProductionBatch.actual_start_time <= end_date)
        
        stmt = stmt.order_by(desc(ProductionBatch.actual_start_time)).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count(
        self,
        line_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count production batches with optional filters."""
        stmt = select(func.count(ProductionBatch.id)).where(
            ProductionBatch.tenant_id == self.tenant_id
        )
        
        if line_id:
            stmt = stmt.where(ProductionBatch.line_id == line_id)
        if status:
            stmt = stmt.where(ProductionBatch.status == status)
        if start_date:
            stmt = stmt.where(ProductionBatch.actual_start_time >= start_date)
        if end_date:
            stmt = stmt.where(ProductionBatch.actual_start_time <= end_date)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def get_current_batch_for_line(self, line_id: uuid.UUID) -> Optional[ProductionBatch]:
        """Get the current in-progress batch for a line."""
        stmt = (
            select(ProductionBatch)
            .options(selectinload(ProductionBatch.line))
            .where(
                and_(
                    ProductionBatch.line_id == line_id,
                    ProductionBatch.tenant_id == self.tenant_id,
                    ProductionBatch.status == "in_progress",
                )
            )
            .order_by(desc(ProductionBatch.actual_start_time))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update(self, batch: ProductionBatch) -> ProductionBatch:
        """Update a production batch."""
        await self.session.flush()
        await self.session.refresh(batch)
        return batch
    
    async def delete(self, batch_id: uuid.UUID) -> bool:
        """Delete a production batch."""
        batch = await self.get_by_id(batch_id)
        if batch:
            await self.session.delete(batch)
            await self.session.flush()
            return True
        return False


class LineEventRepository:
    """Repository for LineEvent operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create(self, event: LineEvent) -> LineEvent:
        """Create a new line event."""
        event.tenant_id = self.tenant_id
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event
    
    async def get_by_id(self, event_id: uuid.UUID) -> Optional[LineEvent]:
        """Get a line event by ID."""
        stmt = select(LineEvent).where(
            and_(
                LineEvent.id == event_id,
                LineEvent.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[uuid.UUID] = None,
        batch_id: Optional[uuid.UUID] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[LineEvent]:
        """List line events with optional filters."""
        stmt = select(LineEvent).where(LineEvent.tenant_id == self.tenant_id)
        
        if line_id:
            stmt = stmt.where(LineEvent.line_id == line_id)
        if batch_id:
            stmt = stmt.where(LineEvent.batch_id == batch_id)
        if event_type:
            stmt = stmt.where(LineEvent.event_type == event_type)
        if start_time:
            stmt = stmt.where(LineEvent.event_time >= start_time)
        if end_time:
            stmt = stmt.where(LineEvent.event_time <= end_time)
        
        stmt = stmt.order_by(desc(LineEvent.event_time)).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count(
        self,
        line_id: Optional[uuid.UUID] = None,
        batch_id: Optional[uuid.UUID] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Count line events with optional filters."""
        stmt = select(func.count(LineEvent.id)).where(
            LineEvent.tenant_id == self.tenant_id
        )
        
        if line_id:
            stmt = stmt.where(LineEvent.line_id == line_id)
        if batch_id:
            stmt = stmt.where(LineEvent.batch_id == batch_id)
        if event_type:
            stmt = stmt.where(LineEvent.event_type == event_type)
        if start_time:
            stmt = stmt.where(LineEvent.event_time >= start_time)
        if end_time:
            stmt = stmt.where(LineEvent.event_time <= end_time)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()


class ScrapEventRepository:
    """Repository for ScrapEvent operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create(self, event: ScrapEvent) -> ScrapEvent:
        """Create a new scrap event."""
        event.tenant_id = self.tenant_id
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event
    
    async def get_by_id(self, event_id: uuid.UUID) -> Optional[ScrapEvent]:
        """Get a scrap event by ID."""
        stmt = select(ScrapEvent).where(
            and_(
                ScrapEvent.id == event_id,
                ScrapEvent.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        batch_id: Optional[uuid.UUID] = None,
        scrap_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[ScrapEvent]:
        """List scrap events with optional filters."""
        stmt = select(ScrapEvent).where(ScrapEvent.tenant_id == self.tenant_id)
        
        if batch_id:
            stmt = stmt.where(ScrapEvent.batch_id == batch_id)
        if scrap_type:
            stmt = stmt.where(ScrapEvent.scrap_type == scrap_type)
        if start_time:
            stmt = stmt.where(ScrapEvent.event_time >= start_time)
        if end_time:
            stmt = stmt.where(ScrapEvent.event_time <= end_time)
        
        stmt = stmt.order_by(desc(ScrapEvent.event_time)).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count(
        self,
        batch_id: Optional[uuid.UUID] = None,
        scrap_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Count scrap events with optional filters."""
        stmt = select(func.count(ScrapEvent.id)).where(
            ScrapEvent.tenant_id == self.tenant_id
        )
        
        if batch_id:
            stmt = stmt.where(ScrapEvent.batch_id == batch_id)
        if scrap_type:
            stmt = stmt.where(ScrapEvent.scrap_type == scrap_type)
        if start_time:
            stmt = stmt.where(ScrapEvent.event_time >= start_time)
        if end_time:
            stmt = stmt.where(ScrapEvent.event_time <= end_time)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()


class SensorRepository:
    """Repository for Sensor operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create(self, sensor: Sensor) -> Sensor:
        """Create a new sensor."""
        sensor.tenant_id = self.tenant_id
        self.session.add(sensor)
        await self.session.flush()
        await self.session.refresh(sensor)
        return sensor
    
    async def get_by_id(self, sensor_id: uuid.UUID) -> Optional[Sensor]:
        """Get a sensor by ID."""
        stmt = select(Sensor).where(
            and_(
                Sensor.id == sensor_id,
                Sensor.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_sensor_code(self, sensor_code: str) -> Optional[Sensor]:
        """Get a sensor by sensor code."""
        stmt = select(Sensor).where(
            and_(
                Sensor.sensor_code == sensor_code,
                Sensor.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[uuid.UUID] = None,
        sensor_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Sensor]:
        """List sensors with optional filters."""
        stmt = select(Sensor).where(Sensor.tenant_id == self.tenant_id)
        
        if line_id:
            stmt = stmt.where(Sensor.line_id == line_id)
        if sensor_type:
            stmt = stmt.where(Sensor.sensor_type == sensor_type)
        if is_active is not None:
            stmt = stmt.where(Sensor.is_active == is_active)
        
        stmt = stmt.order_by(Sensor.sensor_code).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count(
        self,
        line_id: Optional[uuid.UUID] = None,
        sensor_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count sensors with optional filters."""
        stmt = select(func.count(Sensor.id)).where(Sensor.tenant_id == self.tenant_id)
        
        if line_id:
            stmt = stmt.where(Sensor.line_id == line_id)
        if sensor_type:
            stmt = stmt.where(Sensor.sensor_type == sensor_type)
        if is_active is not None:
            stmt = stmt.where(Sensor.is_active == is_active)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def update(self, sensor: Sensor) -> Sensor:
        """Update a sensor."""
        await self.session.flush()
        await self.session.refresh(sensor)
        return sensor
    
    async def delete(self, sensor_id: uuid.UUID) -> bool:
        """Delete a sensor."""
        sensor = await self.get_by_id(sensor_id)
        if sensor:
            await self.session.delete(sensor)
            await self.session.flush()
            return True
        return False


class SensorReadingRepository:
    """Repository for SensorReading operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
    
    async def create(self, reading: SensorReading) -> SensorReading:
        """Create a new sensor reading."""
        reading.tenant_id = self.tenant_id
        self.session.add(reading)
        await self.session.flush()
        await self.session.refresh(reading)
        return reading
    
    async def create_bulk(self, readings: list[SensorReading]) -> list[SensorReading]:
        """Create multiple sensor readings in bulk."""
        for reading in readings:
            reading.tenant_id = self.tenant_id
        self.session.add_all(readings)
        await self.session.flush()
        return readings
    
    async def get_by_id(self, reading_id: uuid.UUID) -> Optional[SensorReading]:
        """Get a sensor reading by ID."""
        stmt = select(SensorReading).where(
            and_(
                SensorReading.id == reading_id,
                SensorReading.tenant_id == self.tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 1000,
        sensor_id: Optional[uuid.UUID] = None,
        batch_id: Optional[uuid.UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        is_anomaly: Optional[bool] = None,
    ) -> list[SensorReading]:
        """List sensor readings with optional filters."""
        stmt = select(SensorReading).where(SensorReading.tenant_id == self.tenant_id)
        
        if sensor_id:
            stmt = stmt.where(SensorReading.sensor_id == sensor_id)
        if batch_id:
            stmt = stmt.where(SensorReading.batch_id == batch_id)
        if start_time:
            stmt = stmt.where(SensorReading.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(SensorReading.timestamp <= end_time)
        if is_anomaly is not None:
            stmt = stmt.where(SensorReading.is_anomaly == is_anomaly)
        
        stmt = stmt.order_by(desc(SensorReading.timestamp)).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count(
        self,
        sensor_id: Optional[uuid.UUID] = None,
        batch_id: Optional[uuid.UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        is_anomaly: Optional[bool] = None,
    ) -> int:
        """Count sensor readings with optional filters."""
        stmt = select(func.count(SensorReading.id)).where(
            SensorReading.tenant_id == self.tenant_id
        )
        
        if sensor_id:
            stmt = stmt.where(SensorReading.sensor_id == sensor_id)
        if batch_id:
            stmt = stmt.where(SensorReading.batch_id == batch_id)
        if start_time:
            stmt = stmt.where(SensorReading.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(SensorReading.timestamp <= end_time)
        if is_anomaly is not None:
            stmt = stmt.where(SensorReading.is_anomaly == is_anomaly)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def get_latest_for_sensor(
        self,
        sensor_id: uuid.UUID,
        limit: int = 100,
    ) -> list[SensorReading]:
        """Get the latest readings for a sensor."""
        stmt = (
            select(SensorReading)
            .where(
                and_(
                    SensorReading.sensor_id == sensor_id,
                    SensorReading.tenant_id == self.tenant_id,
                )
            )
            .order_by(desc(SensorReading.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
