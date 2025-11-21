"""
Tests for AI Telemetry Service.

Tests analytics methods, logging, and metrics calculation.
"""

import uuid
from datetime import datetime, timedelta

import pytest

from src.core.telemetry.service import TelemetryService


@pytest.mark.unit
@pytest.mark.telemetry
class TestTelemetryService:
    """Test suite for telemetry service."""
    
    async def test_log_copilot_interaction(self, db_session, sample_tenant, sample_user):
        """Test logging a Copilot interaction."""
        service = TelemetryService(db_session)
        
        interaction = await service.log_copilot_interaction(
            tenant_id=sample_tenant.id,
            user_id=sample_user.id,
            workspace="plantops",
            question="Test question",
            answer="Test answer",
            tools_used=["test_tool"],
            tokens_used=100,
            duration_ms=500.0,
        )
        
        assert interaction.id is not None
        assert interaction.workspace == "plantops"
        assert interaction.tokens_used == 100
        assert interaction.tools_used == ["test_tool"]
    
    async def test_get_workspace_analytics(self, db_session, sample_copilot_interaction):
        """Test retrieving workspace analytics."""
        service = TelemetryService(db_session)
        
        analytics = await service.get_workspace_analytics(
            tenant_id=sample_copilot_interaction.tenant_id,
            workspace="plantops",
        )
        
        assert analytics["total_interactions"] >= 1
        assert analytics["unique_users"] >= 1
        assert "tool_usage" in analytics
    
    async def test_get_workspace_analytics_empty(self, db_session, sample_tenant):
        """Test analytics with no interactions."""
        service = TelemetryService(db_session)
        
        analytics = await service.get_workspace_analytics(
            tenant_id=sample_tenant.id,
            workspace="nonexistent",
        )
        
        assert analytics["total_interactions"] == 0
        assert analytics["unique_users"] == 0
    
    async def test_log_ai_suggestion(self, db_session, sample_tenant, sample_user):
        """Test logging an AI suggestion."""
        service = TelemetryService(db_session)
        
        suggestion = await service.log_ai_suggestion(
            tenant_id=sample_tenant.id,
            user_id=sample_user.id,
            suggestion_type="line_adjustment",
            suggestion_text="Adjust temperature to 180°C",
            payload={"parameter": "temperature", "value": 180},
        )
        
        assert suggestion.id is not None
        assert suggestion.suggestion_type == "line_adjustment"
        assert suggestion.applied_flag is False
    
    async def test_record_suggestion_outcome(self, db_session, sample_tenant, sample_user):
        """Test recording suggestion application outcome."""
        service = TelemetryService(db_session)
        
        # Create suggestion
        suggestion = await service.log_ai_suggestion(
            tenant_id=sample_tenant.id,
            user_id=sample_user.id,
            suggestion_type="line_adjustment",
            suggestion_text="Test suggestion",
            payload={},
        )
        
        # Record outcome
        updated = await service.record_suggestion_outcome(
            suggestion_id=suggestion.id,
            applied_by=sample_user.id,
            before_metrics={"scrap_rate": 5.0},
            after_metrics={"scrap_rate": 3.0},
        )
        
        assert updated.applied_flag is True
        assert updated.before_metrics == {"scrap_rate": 5.0}
        assert updated.after_metrics == {"scrap_rate": 3.0}
    
    async def test_get_tool_usage_stats(self, db_session, sample_copilot_interaction):
        """Test tool usage statistics."""
        service = TelemetryService(db_session)
        
        stats = await service.get_tool_usage_stats(
            tenant_id=sample_copilot_interaction.tenant_id,
        )
        
        assert "tools" in stats
        assert stats["total_tool_calls"] >= 2  # Sample has 2 tools
    
    async def test_get_user_engagement(self, db_session, sample_copilot_interaction):
        """Test user engagement metrics."""
        service = TelemetryService(db_session)
        
        engagement = await service.get_user_engagement(
            tenant_id=sample_copilot_interaction.tenant_id,
        )
        
        assert "top_users" in engagement
        assert len(engagement["top_users"]) >= 1

