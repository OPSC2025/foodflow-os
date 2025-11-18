"""
Core events module for domain event publishing and handling.

Implements the transactional outbox pattern for reliable event publishing.
Events are first stored in the database, then published to the event bus.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Index, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Base, TimestampMixin


class EventStatus(str, Enum):
    """Event processing status."""
    
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


class DomainEvent(BaseModel):
    """
    Base class for all domain events.
    
    Domain events represent something that happened in the system that
    other parts of the system might be interested in.
    """
    
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    aggregate_type: str
    aggregate_id: uuid.UUID
    tenant_id: uuid.UUID
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v),
        }


class OutboxEvent(Base, TimestampMixin):
    """
    Outbox event table for transactional outbox pattern.
    
    Events are first written to this table in the same transaction as the
    business logic, then a background worker publishes them to the event bus.
    """
    
    __tablename__ = "outbox_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Event identification
    event_type = Column(String(255), nullable=False, index=True)
    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Event data
    payload = Column(JSONB, nullable=False)
    metadata = Column(JSONB, nullable=True)
    
    # Processing status
    status = Column(String(20), nullable=False, default=EventStatus.PENDING, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(String(20), nullable=False, default="0")
    
    # Timestamps
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_outbox_events_status_created", "status", "created_at"),
        Index("ix_outbox_events_tenant_aggregate", "tenant_id", "aggregate_type", "aggregate_id"),
    )


class EventPublisher:
    """
    Event publisher for domain events.
    
    Implements the transactional outbox pattern to ensure reliable event publishing.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize event publisher.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a domain event.
        
        The event is first written to the outbox table in the same transaction
        as the business logic. A background worker will later publish it to the
        event bus.
        
        Args:
            event: Domain event to publish
        """
        outbox_event = OutboxEvent(
            id=event.event_id,
            tenant_id=event.tenant_id,
            event_type=event.event_type,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            payload=event.payload,
            metadata=event.metadata,
            occurred_at=event.occurred_at,
            status=EventStatus.PENDING,
        )
        
        self.session.add(outbox_event)
        # Note: commit is handled by the calling code to maintain transaction boundary
    
    async def publish_many(self, events: List[DomainEvent]) -> None:
        """
        Publish multiple domain events.
        
        Args:
            events: List of domain events to publish
        """
        for event in events:
            await self.publish(event)


class EventStore:
    """
    Event store for querying published events.
    
    Provides methods to query the event history for aggregates.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize event store.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def get_events_for_aggregate(
        self,
        tenant_id: uuid.UUID,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        from_date: Optional[datetime] = None,
    ) -> List[OutboxEvent]:
        """
        Get all events for a specific aggregate.
        
        Args:
            tenant_id: Tenant ID
            aggregate_type: Type of aggregate (e.g., "ProductionBatch")
            aggregate_id: ID of the aggregate
            from_date: Optional filter for events after this date
            
        Returns:
            List of outbox events
        """
        query = select(OutboxEvent).where(
            OutboxEvent.tenant_id == tenant_id,
            OutboxEvent.aggregate_type == aggregate_type,
            OutboxEvent.aggregate_id == aggregate_id,
        )
        
        if from_date:
            query = query.where(OutboxEvent.occurred_at >= from_date)
        
        query = query.order_by(OutboxEvent.occurred_at.asc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_events_by_type(
        self,
        tenant_id: uuid.UUID,
        event_type: str,
        limit: int = 100,
    ) -> List[OutboxEvent]:
        """
        Get events by type.
        
        Args:
            tenant_id: Tenant ID
            event_type: Event type to filter by
            limit: Maximum number of events to return
            
        Returns:
            List of outbox events
        """
        query = (
            select(OutboxEvent)
            .where(
                OutboxEvent.tenant_id == tenant_id,
                OutboxEvent.event_type == event_type,
            )
            .order_by(OutboxEvent.occurred_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_pending_events(
        self,
        limit: int = 100,
        max_retries: int = 3,
    ) -> List[OutboxEvent]:
        """
        Get pending events that need to be published.
        
        Args:
            limit: Maximum number of events to return
            max_retries: Maximum number of retries before giving up
            
        Returns:
            List of pending outbox events
        """
        query = (
            select(OutboxEvent)
            .where(
                OutboxEvent.status == EventStatus.PENDING,
                OutboxEvent.retry_count < str(max_retries),
            )
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def mark_as_published(self, event_id: uuid.UUID) -> None:
        """
        Mark an event as successfully published.
        
        Args:
            event_id: ID of the event
        """
        query = select(OutboxEvent).where(OutboxEvent.id == event_id)
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        
        if event:
            event.status = EventStatus.PUBLISHED
            event.published_at = datetime.utcnow()
            await self.session.commit()
    
    async def mark_as_failed(
        self,
        event_id: uuid.UUID,
        error_message: str,
    ) -> None:
        """
        Mark an event as failed.
        
        Args:
            event_id: ID of the event
            error_message: Error message describing the failure
        """
        query = select(OutboxEvent).where(OutboxEvent.id == event_id)
        result = await self.session.execute(query)
        event = result.scalar_one_or_none()
        
        if event:
            event.retry_count = str(int(event.retry_count) + 1)
            event.error_message = error_message
            
            # Mark as failed if max retries exceeded
            if int(event.retry_count) >= 3:
                event.status = EventStatus.FAILED
            
            await self.session.commit()


# Common domain events for PlantOps context

class BatchCreatedEvent(DomainEvent):
    """Event raised when a production batch is created."""
    
    event_type: str = "plant_ops.batch.created"
    aggregate_type: str = "ProductionBatch"


class BatchStartedEvent(DomainEvent):
    """Event raised when a production batch is started."""
    
    event_type: str = "plant_ops.batch.started"
    aggregate_type: str = "ProductionBatch"


class BatchCompletedEvent(DomainEvent):
    """Event raised when a production batch is completed."""
    
    event_type: str = "plant_ops.batch.completed"
    aggregate_type: str = "ProductionBatch"


class ScrapDetectedEvent(DomainEvent):
    """Event raised when scrap is detected."""
    
    event_type: str = "plant_ops.scrap.detected"
    aggregate_type: str = "ProductionBatch"


class AnomalyDetectedEvent(DomainEvent):
    """Event raised when an anomaly is detected by AI."""
    
    event_type: str = "plant_ops.anomaly.detected"
    aggregate_type: str = "ProductionBatch"


class LineDowntimeEvent(DomainEvent):
    """Event raised when a production line goes down."""
    
    event_type: str = "plant_ops.line.downtime"
    aggregate_type: str = "ProductionLine"
