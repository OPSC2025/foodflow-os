"""
PlantOps context service layer with business logic.

Services orchestrate operations across repositories and implement business rules.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.domain.models import (
    BatchStatus,
    LineEvent,
    LineStatus,
    ProductionBatch,
    ProductionLine,
    ScrapEvent,
    Sensor,
    SensorReading,
)
from src.contexts.plant_ops.domain.schemas import (
    LineEventCreate,
    ProductionBatchCreate,
    ProductionBatchUpdate,
    ProductionLineCreate,
    ProductionLineUpdate,
    ScrapEventCreate,
    SensorCreate,
    SensorReadingCreate,
    SensorUpdate,
)
from src.contexts.plant_ops.infrastructure.repositories import (
    LineEventRepository,
    ProductionBatchRepository,
    ProductionLineRepository,
    ScrapEventRepository,
    SensorReadingRepository,
    SensorRepository,
)
from src.core.events import (
    AnomalyDetectedEvent,
    BatchCompletedEvent,
    BatchCreatedEvent,
    BatchStartedEvent,
    EventPublisher,
    LineDowntimeEvent,
    ScrapDetectedEvent,
)


class ProductionLineService:
    """Service for production line operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = ProductionLineRepository(session, tenant_id)
        self.event_publisher = EventPublisher(session, tenant_id)
    
    async def create_line(self, data: ProductionLineCreate) -> ProductionLine:
        """Create a new production line."""
        # Check for duplicate line number
        existing = await self.repo.get_by_line_number(data.line_number)
        if existing:
            raise ValueError(f"Line number '{data.line_number}' already exists")
        
        line = ProductionLine(**data.model_dump())
        line = await self.repo.create(line)
        
        return line
    
    async def get_line(self, line_id: uuid.UUID) -> Optional[ProductionLine]:
        """Get a production line by ID."""
        return await self.repo.get_by_id(line_id)
    
    async def get_line_by_number(self, line_number: str) -> Optional[ProductionLine]:
        """Get a production line by line number."""
        return await self.repo.get_by_line_number(line_number)
    
    async def list_lines(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[ProductionLine], int]:
        """List production lines with pagination."""
        lines = await self.repo.list(skip, limit, status, is_active)
        total = await self.repo.count(status, is_active)
        return lines, total
    
    async def update_line(
        self,
        line_id: uuid.UUID,
        data: ProductionLineUpdate,
    ) -> ProductionLine:
        """Update a production line."""
        line = await self.repo.get_by_id(line_id)
        if not line:
            raise ValueError(f"Line with ID {line_id} not found")
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(line, field, value)
        
        line = await self.repo.update(line)
        
        return line
    
    async def update_line_status(
        self,
        line_id: uuid.UUID,
        new_status: str,
        reason: Optional[str] = None,
    ) -> ProductionLine:
        """Update line status and create event."""
        line = await self.repo.get_by_id(line_id)
        if not line:
            raise ValueError(f"Line with ID {line_id} not found")
        
        previous_status = line.status
        line.status = new_status
        line = await self.repo.update(line)
        
        # Create line event
        event_repo = LineEventRepository(self.session, self.tenant_id)
        line_event = LineEvent(
            line_id=line_id,
            event_type="status_change",
            event_time=datetime.utcnow(),
            previous_status=previous_status,
            new_status=new_status,
            description=reason,
        )
        await event_repo.create(line_event)
        
        # Publish domain event for downtime
        if new_status == LineStatus.DOWNTIME:
            await self.event_publisher.publish(
                LineDowntimeEvent(
                    line_id=str(line_id),
                    line_number=line.line_number,
                    reason=reason or "unknown",
                    timestamp=datetime.utcnow(),
                )
            )
        
        return line
    
    async def delete_line(self, line_id: uuid.UUID) -> bool:
        """Delete a production line."""
        return await self.repo.delete(line_id)


class ProductionBatchService:
    """Service for production batch operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = ProductionBatchRepository(session, tenant_id)
        self.line_repo = ProductionLineRepository(session, tenant_id)
        self.event_publisher = EventPublisher(session, tenant_id)
    
    async def create_batch(self, data: ProductionBatchCreate) -> ProductionBatch:
        """Create a new production batch."""
        # Check for duplicate batch number
        existing = await self.repo.get_by_batch_number(data.batch_number)
        if existing:
            raise ValueError(f"Batch number '{data.batch_number}' already exists")
        
        # Verify line exists
        line = await self.line_repo.get_by_id(data.line_id)
        if not line:
            raise ValueError(f"Line with ID {data.line_id} not found")
        
        batch = ProductionBatch(**data.model_dump())
        batch = await self.repo.create(batch)
        
        # Publish domain event
        await self.event_publisher.publish(
            BatchCreatedEvent(
                batch_id=str(batch.id),
                batch_number=batch.batch_number,
                line_id=str(batch.line_id),
                product_code=batch.product_code,
                target_quantity=float(batch.target_quantity),
                timestamp=datetime.utcnow(),
            )
        )
        
        return batch
    
    async def get_batch(self, batch_id: uuid.UUID) -> Optional[ProductionBatch]:
        """Get a production batch by ID."""
        return await self.repo.get_by_id(batch_id)
    
    async def get_batch_by_number(self, batch_number: str) -> Optional[ProductionBatch]:
        """Get a production batch by batch number."""
        return await self.repo.get_by_batch_number(batch_number)
    
    async def list_batches(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[ProductionBatch], int]:
        """List production batches with pagination."""
        batches = await self.repo.list(skip, limit, line_id, status, start_date, end_date)
        total = await self.repo.count(line_id, status, start_date, end_date)
        return batches, total
    
    async def start_batch(self, batch_id: uuid.UUID) -> ProductionBatch:
        """Start a production batch."""
        batch = await self.repo.get_by_id(batch_id)
        if not batch:
            raise ValueError(f"Batch with ID {batch_id} not found")
        
        if batch.status != BatchStatus.PLANNED:
            raise ValueError(f"Batch must be in PLANNED status to start (current: {batch.status})")
        
        # Check if line has another batch running
        current_batch = await self.repo.get_current_batch_for_line(batch.line_id)
        if current_batch and current_batch.id != batch_id:
            raise ValueError(f"Line already has batch {current_batch.batch_number} in progress")
        
        # Update batch
        batch.status = BatchStatus.IN_PROGRESS
        batch.actual_start_time = datetime.utcnow()
        batch = await self.repo.update(batch)
        
        # Update line
        line = await self.line_repo.get_by_id(batch.line_id)
        if line:
            line.status = LineStatus.RUNNING
            line.current_batch_id = batch.id
            await self.line_repo.update(line)
        
        # Publish domain event
        await self.event_publisher.publish(
            BatchStartedEvent(
                batch_id=str(batch.id),
                batch_number=batch.batch_number,
                line_id=str(batch.line_id),
                timestamp=datetime.utcnow(),
            )
        )
        
        return batch
    
    async def complete_batch(self, batch_id: uuid.UUID) -> ProductionBatch:
        """Complete a production batch."""
        batch = await self.repo.get_by_id(batch_id)
        if not batch:
            raise ValueError(f"Batch with ID {batch_id} not found")
        
        if batch.status != BatchStatus.IN_PROGRESS:
            raise ValueError(f"Batch must be IN_PROGRESS to complete (current: {batch.status})")
        
        # Update batch
        batch.status = BatchStatus.COMPLETED
        batch.actual_end_time = datetime.utcnow()
        
        # Calculate OEE if not already set
        if batch.oee is None:
            batch = self._calculate_oee(batch)
        
        batch = await self.repo.update(batch)
        
        # Update line
        line = await self.line_repo.get_by_id(batch.line_id)
        if line:
            line.status = LineStatus.IDLE
            line.current_batch_id = None
            await self.line_repo.update(line)
        
        # Publish domain event
        await self.event_publisher.publish(
            BatchCompletedEvent(
                batch_id=str(batch.id),
                batch_number=batch.batch_number,
                line_id=str(batch.line_id),
                produced_quantity=float(batch.produced_quantity),
                good_quantity=float(batch.good_quantity),
                scrap_quantity=float(batch.scrap_quantity),
                oee=float(batch.oee) if batch.oee else None,
                timestamp=datetime.utcnow(),
            )
        )
        
        return batch
    
    async def update_batch(
        self,
        batch_id: uuid.UUID,
        data: ProductionBatchUpdate,
    ) -> ProductionBatch:
        """Update a production batch."""
        batch = await self.repo.get_by_id(batch_id)
        if not batch:
            raise ValueError(f"Batch with ID {batch_id} not found")
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(batch, field, value)
        
        # Recalculate OEE if relevant fields changed
        if any(k in update_data for k in ["availability", "performance", "quality"]):
            batch = self._calculate_oee(batch)
        
        batch = await self.repo.update(batch)
        
        return batch
    
    def _calculate_oee(self, batch: ProductionBatch) -> ProductionBatch:
        """Calculate OEE from availability, performance, and quality."""
        if batch.availability and batch.performance and batch.quality:
            oee = (
                float(batch.availability)
                * float(batch.performance)
                * float(batch.quality)
                / 10000  # Divide by 10000 because each is a percentage
            )
            batch.oee = Decimal(str(oee))
        return batch


class ScrapEventService:
    """Service for scrap event operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = ScrapEventRepository(session, tenant_id)
        self.batch_repo = ProductionBatchRepository(session, tenant_id)
        self.event_publisher = EventPublisher(session, tenant_id)
    
    async def create_scrap_event(self, data: ScrapEventCreate) -> ScrapEvent:
        """Create a new scrap event."""
        # Verify batch exists
        batch = await self.batch_repo.get_by_id(data.batch_id)
        if not batch:
            raise ValueError(f"Batch with ID {data.batch_id} not found")
        
        event = ScrapEvent(**data.model_dump())
        event = await self.repo.create(event)
        
        # Update batch scrap quantity
        batch.scrap_quantity += Decimal(str(data.quantity))
        await self.batch_repo.update(batch)
        
        # Publish domain event
        await self.event_publisher.publish(
            ScrapDetectedEvent(
                batch_id=str(batch.id),
                batch_number=batch.batch_number,
                scrap_type=event.scrap_type,
                quantity=float(event.quantity),
                severity=event.severity or "medium",
                timestamp=datetime.utcnow(),
            )
        )
        
        return event
    
    async def get_scrap_event(self, event_id: uuid.UUID) -> Optional[ScrapEvent]:
        """Get a scrap event by ID."""
        return await self.repo.get_by_id(event_id)
    
    async def list_scrap_events(
        self,
        skip: int = 0,
        limit: int = 100,
        batch_id: Optional[uuid.UUID] = None,
        scrap_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> tuple[list[ScrapEvent], int]:
        """List scrap events with pagination."""
        events = await self.repo.list(skip, limit, batch_id, scrap_type, start_time, end_time)
        total = await self.repo.count(batch_id, scrap_type, start_time, end_time)
        return events, total


class SensorService:
    """Service for sensor operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = SensorRepository(session, tenant_id)
        self.reading_repo = SensorReadingRepository(session, tenant_id)
        self.line_repo = ProductionLineRepository(session, tenant_id)
        self.event_publisher = EventPublisher(session, tenant_id)
    
    async def create_sensor(self, data: SensorCreate) -> Sensor:
        """Create a new sensor."""
        # Check for duplicate sensor code
        existing = await self.repo.get_by_sensor_code(data.sensor_code)
        if existing:
            raise ValueError(f"Sensor code '{data.sensor_code}' already exists")
        
        # Verify line exists
        line = await self.line_repo.get_by_id(data.line_id)
        if not line:
            raise ValueError(f"Line with ID {data.line_id} not found")
        
        sensor = Sensor(**data.model_dump())
        sensor = await self.repo.create(sensor)
        
        return sensor
    
    async def get_sensor(self, sensor_id: uuid.UUID) -> Optional[Sensor]:
        """Get a sensor by ID."""
        return await self.repo.get_by_id(sensor_id)
    
    async def get_sensor_by_code(self, sensor_code: str) -> Optional[Sensor]:
        """Get a sensor by sensor code."""
        return await self.repo.get_by_sensor_code(sensor_code)
    
    async def list_sensors(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[uuid.UUID] = None,
        sensor_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Sensor], int]:
        """List sensors with pagination."""
        sensors = await self.repo.list(skip, limit, line_id, sensor_type, is_active)
        total = await self.repo.count(line_id, sensor_type, is_active)
        return sensors, total
    
    async def update_sensor(
        self,
        sensor_id: uuid.UUID,
        data: SensorUpdate,
    ) -> Sensor:
        """Update a sensor."""
        sensor = await self.repo.get_by_id(sensor_id)
        if not sensor:
            raise ValueError(f"Sensor with ID {sensor_id} not found")
        
        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sensor, field, value)
        
        sensor = await self.repo.update(sensor)
        
        return sensor
    
    async def record_reading(
        self,
        data: SensorReadingCreate,
        check_anomaly: bool = True,
    ) -> SensorReading:
        """Record a sensor reading."""
        # Verify sensor exists
        sensor = await self.repo.get_by_id(data.sensor_id)
        if not sensor:
            raise ValueError(f"Sensor with ID {data.sensor_id} not found")
        
        reading = SensorReading(**data.model_dump())
        
        # Check for anomaly if enabled
        if check_anomaly and sensor.min_value and sensor.max_value:
            if reading.value < float(sensor.min_value) or reading.value > float(sensor.max_value):
                reading.is_anomaly = True
        
        reading = await self.reading_repo.create(reading)
        
        # Update sensor last reading
        sensor.last_reading_time = reading.timestamp
        sensor.last_reading_value = Decimal(str(reading.value))
        await self.repo.update(sensor)
        
        # Publish anomaly event if detected
        if reading.is_anomaly:
            await self.event_publisher.publish(
                AnomalyDetectedEvent(
                    sensor_id=str(sensor.id),
                    sensor_code=sensor.sensor_code,
                    value=reading.value,
                    expected_range=f"{sensor.min_value}-{sensor.max_value}",
                    timestamp=reading.timestamp,
                )
            )
        
        return reading
    
    async def record_readings_bulk(
        self,
        readings: list[SensorReadingCreate],
        check_anomaly: bool = True,
    ) -> list[SensorReading]:
        """Record multiple sensor readings in bulk."""
        # Convert to model instances
        reading_models = []
        for data in readings:
            # Verify sensor exists (cached in practice)
            sensor = await self.repo.get_by_id(data.sensor_id)
            if not sensor:
                continue  # Skip invalid sensors
            
            reading = SensorReading(**data.model_dump())
            
            # Check for anomaly
            if check_anomaly and sensor.min_value and sensor.max_value:
                if reading.value < float(sensor.min_value) or reading.value > float(sensor.max_value):
                    reading.is_anomaly = True
            
            reading_models.append(reading)
        
        # Bulk insert
        readings = await self.reading_repo.create_bulk(reading_models)
        
        return readings
    
    async def get_sensor_readings(
        self,
        sensor_id: uuid.UUID,
        skip: int = 0,
        limit: int = 1000,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> tuple[list[SensorReading], int]:
        """Get sensor readings with pagination."""
        readings = await self.reading_repo.list(
            skip, limit, sensor_id=sensor_id, start_time=start_time, end_time=end_time
        )
        total = await self.reading_repo.count(
            sensor_id=sensor_id, start_time=start_time, end_time=end_time
        )
        return readings, total
