"""
Streaming data ingestion service for high-throughput sensor data.

Optimized for handling large volumes of sensor readings with minimal latency.
"""

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.domain.schemas import SensorReadingCreate
from src.contexts.plant_ops.infrastructure.repositories import SensorReadingRepository
from src.core.database import async_session_maker


class SensorDataBuffer:
    """
    Buffer for batching sensor readings before database insertion.
    
    Optimizes write performance by accumulating readings and inserting in bulk.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        max_age_seconds: float = 5.0,
        flush_callback: Optional[Callable] = None,
    ):
        """
        Initialize sensor data buffer.
        
        Args:
            max_size: Maximum number of readings before auto-flush
            max_age_seconds: Maximum age of oldest reading before auto-flush
            flush_callback: Optional callback function called after flush
        """
        self.max_size = max_size
        self.max_age_seconds = max_age_seconds
        self.flush_callback = flush_callback
        
        self._buffer: List[SensorReadingCreate] = []
        self._oldest_timestamp: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        
    async def add(self, reading: SensorReadingCreate) -> None:
        """
        Add a sensor reading to the buffer.
        
        Automatically flushes if buffer is full or too old.
        """
        async with self._lock:
            self._buffer.append(reading)
            
            if self._oldest_timestamp is None:
                self._oldest_timestamp = reading.timestamp
            
            # Check if buffer should be flushed
            should_flush = (
                len(self._buffer) >= self.max_size or
                (datetime.utcnow() - self._oldest_timestamp).total_seconds() >= self.max_age_seconds
            )
            
            if should_flush:
                await self._flush()
    
    async def _flush(self) -> None:
        """Flush buffer to database."""
        if not self._buffer:
            return
        
        readings = self._buffer.copy()
        self._buffer.clear()
        self._oldest_timestamp = None
        
        try:
            async with async_session_maker() as session:
                repo = SensorReadingRepository(session)
                await repo.bulk_create(readings)
                await session.commit()
            
            if self.flush_callback:
                await self.flush_callback(len(readings))
                
        except Exception as e:
            # Log error but don't raise to prevent buffer from stopping
            print(f"Error flushing sensor data buffer: {e}")
    
    async def flush(self) -> None:
        """Manually flush buffer to database."""
        async with self._lock:
            await self._flush()
    
    async def start_auto_flush(self) -> None:
        """Start background task for automatic periodic flushing."""
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._auto_flush_loop())
    
    async def stop_auto_flush(self) -> None:
        """Stop background auto-flush task."""
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self.flush()
    
    async def _auto_flush_loop(self) -> None:
        """Background loop for periodic flushing."""
        while True:
            try:
                await asyncio.sleep(self.max_age_seconds)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in auto-flush loop: {e}")


class SensorDataStreamer:
    """
    High-performance sensor data streaming service.
    
    Manages multiple buffers for different tenants and provides
    real-time data ingestion with anomaly detection.
    """
    
    def __init__(
        self,
        buffer_size: int = 1000,
        buffer_age_seconds: float = 5.0,
    ):
        """
        Initialize sensor data streamer.
        
        Args:
            buffer_size: Size of each tenant's buffer
            buffer_age_seconds: Maximum age before auto-flush
        """
        self.buffer_size = buffer_size
        self.buffer_age_seconds = buffer_age_seconds
        
        # Tenant-specific buffers
        self._buffers: Dict[UUID, SensorDataBuffer] = {}
        self._lock = asyncio.Lock()
        
        # Statistics
        self._stats = defaultdict(lambda: {
            "total_readings": 0,
            "anomalies_detected": 0,
            "flushes": 0,
        })
    
    async def ingest(
        self,
        tenant_id: UUID,
        reading: SensorReadingCreate,
    ) -> None:
        """
        Ingest a sensor reading.
        
        Args:
            tenant_id: Tenant ID for isolation
            reading: Sensor reading to ingest
        """
        # Get or create buffer for tenant
        buffer = await self._get_buffer(tenant_id)
        
        # Add to buffer
        await buffer.add(reading)
        
        # Update statistics
        self._stats[tenant_id]["total_readings"] += 1
        if reading.is_anomaly:
            self._stats[tenant_id]["anomalies_detected"] += 1
    
    async def ingest_bulk(
        self,
        tenant_id: UUID,
        readings: List[SensorReadingCreate],
    ) -> None:
        """
        Ingest multiple sensor readings in bulk.
        
        Args:
            tenant_id: Tenant ID for isolation
            readings: List of sensor readings to ingest
        """
        buffer = await self._get_buffer(tenant_id)
        
        for reading in readings:
            await buffer.add(reading)
            self._stats[tenant_id]["total_readings"] += 1
            if reading.is_anomaly:
                self._stats[tenant_id]["anomalies_detected"] += 1
    
    async def _get_buffer(self, tenant_id: UUID) -> SensorDataBuffer:
        """Get or create buffer for tenant."""
        async with self._lock:
            if tenant_id not in self._buffers:
                buffer = SensorDataBuffer(
                    max_size=self.buffer_size,
                    max_age_seconds=self.buffer_age_seconds,
                    flush_callback=self._on_flush(tenant_id),
                )
                await buffer.start_auto_flush()
                self._buffers[tenant_id] = buffer
            
            return self._buffers[tenant_id]
    
    def _on_flush(self, tenant_id: UUID) -> Callable:
        """Create flush callback for tenant."""
        async def callback(count: int):
            self._stats[tenant_id]["flushes"] += 1
        return callback
    
    async def flush_all(self) -> None:
        """Flush all tenant buffers."""
        for buffer in self._buffers.values():
            await buffer.flush()
    
    async def stop(self) -> None:
        """Stop all buffers and flush remaining data."""
        for buffer in self._buffers.values():
            await buffer.stop_auto_flush()
        
        self._buffers.clear()
    
    def get_stats(self, tenant_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get streaming statistics.
        
        Args:
            tenant_id: Optional tenant ID to get specific stats
            
        Returns:
            Statistics dictionary
        """
        if tenant_id:
            return dict(self._stats.get(tenant_id, {}))
        
        # Aggregate stats across all tenants
        total_stats = {
            "total_readings": 0,
            "anomalies_detected": 0,
            "flushes": 0,
            "active_tenants": len(self._buffers),
        }
        
        for stats in self._stats.values():
            total_stats["total_readings"] += stats["total_readings"]
            total_stats["anomalies_detected"] += stats["anomalies_detected"]
            total_stats["flushes"] += stats["flushes"]
        
        return total_stats


# Global streamer instance
_streamer: Optional[SensorDataStreamer] = None


def get_streamer() -> SensorDataStreamer:
    """Get global sensor data streamer instance."""
    global _streamer
    if _streamer is None:
        _streamer = SensorDataStreamer()
    return _streamer


async def shutdown_streamer() -> None:
    """Shutdown global streamer and flush all data."""
    global _streamer
    if _streamer is not None:
        await _streamer.stop()
        _streamer = None
