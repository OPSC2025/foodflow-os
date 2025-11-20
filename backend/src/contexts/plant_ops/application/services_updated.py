"""
Updated PlantOps application services with integrated anomaly detection.

This file shows the integration points for anomaly detection in the sensor service.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.domain.schemas import (
    SensorCreate,
    SensorReadingCreate,
    SensorUpdate,
)
from src.contexts.plant_ops.infrastructure.repositories import (
    SensorReadingRepository,
    SensorRepository,
)
from src.core.events import DomainEventPublisher
from src.core.ml.anomaly_detection import get_anomaly_service


class SensorService:
    """Service for managing sensors and sensor readings with anomaly detection."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SensorRepository(session)
        self.reading_repo = SensorReadingRepository(session)
        self.event_publisher = DomainEventPublisher(session)
        self.anomaly_service = get_anomaly_service()
    
    async def create_sensor(
        self,
        tenant_id: UUID,
        data: SensorCreate,
    ) -> UUID:
        """Create a new sensor."""
        sensor_id = await self.repo.create(tenant_id, data)
        
        # Publish event
        await self.event_publisher.publish(
            "SensorCreated",
            tenant_id=tenant_id,
            sensor_id=sensor_id,
            sensor_code=data.sensor_code,
            sensor_type=data.sensor_type,
        )
        
        return sensor_id
    
    async def record_reading(
        self,
        tenant_id: UUID,
        reading: SensorReadingCreate,
    ) -> UUID:
        """
        Record a sensor reading with anomaly detection.
        
        Automatically detects anomalies using ML and statistical methods.
        """
        # Get sensor configuration
        sensor = await self.repo.get_by_id(tenant_id, reading.sensor_id)
        if not sensor:
            raise ValueError(f"Sensor {reading.sensor_id} not found")
        
        # Check for anomalies
        updated_reading = self.anomaly_service.check_reading(
            reading,
            sensor_min=sensor.min_value,
            sensor_max=sensor.max_value,
        )
        
        # Save reading
        reading_id = await self.reading_repo.create(tenant_id, updated_reading)
        
        # Publish event if anomaly detected
        if updated_reading.is_anomaly:
            await self.event_publisher.publish(
                "SensorAnomalyDetected",
                tenant_id=tenant_id,
                sensor_id=reading.sensor_id,
                reading_id=reading_id,
                value=reading.value,
                anomaly_score=updated_reading.anomaly_score,
                timestamp=reading.timestamp,
            )
        
        return reading_id
    
    async def record_readings_bulk(
        self,
        tenant_id: UUID,
        readings: List[SensorReadingCreate],
    ) -> int:
        """
        Record multiple sensor readings in bulk with anomaly detection.
        
        Optimized for high-throughput ingestion.
        """
        if not readings:
            return 0
        
        # Get sensor configurations for all unique sensors
        sensor_ids = list(set(r.sensor_id for r in readings))
        sensors = await self.repo.get_by_ids(tenant_id, sensor_ids)
        
        sensor_configs = {
            s.id: {"min": s.min_value, "max": s.max_value}
            for s in sensors
        }
        
        # Check all readings for anomalies
        updated_readings = self.anomaly_service.check_batch(readings, sensor_configs)
        
        # Save all readings
        count = await self.reading_repo.bulk_create(updated_readings)
        
        # Publish events for anomalies
        anomalies = [r for r in updated_readings if r.is_anomaly]
        for reading in anomalies:
            await self.event_publisher.publish(
                "SensorAnomalyDetected",
                tenant_id=tenant_id,
                sensor_id=reading.sensor_id,
                value=reading.value,
                anomaly_score=reading.anomaly_score,
                timestamp=reading.timestamp,
            )
        
        return count
    
    async def get_sensor_stats(self, tenant_id: UUID, sensor_id: UUID) -> dict:
        """
        Get real-time statistics for a sensor.
        
        Includes both database stats and ML model stats.
        """
        # Get database stats
        db_stats = await self.reading_repo.get_statistics(
            tenant_id,
            sensor_id,
            start_time=datetime.utcnow().replace(hour=0, minute=0, second=0),
        )
        
        # Get ML model stats
        ml_stats = self.anomaly_service.update_sensor_stats(sensor_id)
        
        return {
            **db_stats,
            "ml_stats": ml_stats,
        }
    
    async def retrain_anomaly_model(self, tenant_id: UUID, sensor_id: UUID) -> None:
        """
        Retrain anomaly detection model for a sensor.
        
        Useful after sensor recalibration or process changes.
        """
        # Verify sensor exists
        sensor = await self.repo.get_by_id(tenant_id, sensor_id)
        if not sensor:
            raise ValueError(f"Sensor {sensor_id} not found")
        
        # Retrain model
        self.anomaly_service.retrain_sensor(sensor_id)
        
        # Publish event
        await self.event_publisher.publish(
            "SensorModelRetrained",
            tenant_id=tenant_id,
            sensor_id=sensor_id,
            timestamp=datetime.utcnow(),
        )
