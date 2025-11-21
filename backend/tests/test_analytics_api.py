"""
Tests for Analytics API endpoints.

Tests analytics endpoint responses, query parameters, and data accuracy.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.telemetry
class TestAnalyticsAPI:
    """Test suite for analytics API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_workspace_analytics(self, client: AsyncClient, sample_copilot_interaction, auth_headers):
        """Test workspace analytics endpoint."""
        response = await client.get(
            "/api/v1/analytics/workspace",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "workspace" in data
        assert "total_interactions" in data
        assert "unique_users" in data
        assert data["total_interactions"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_workspace_analytics_filtered(self, client: AsyncClient, sample_copilot_interaction, auth_headers):
        """Test workspace analytics with workspace filter."""
        response = await client.get(
            "/api/v1/analytics/workspace?workspace=plantops",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["workspace"] == "plantops"
    
    @pytest.mark.asyncio
    async def test_get_tool_usage_stats(self, client: AsyncClient, sample_copilot_interaction, auth_headers):
        """Test tool usage statistics endpoint."""
        response = await client.get(
            "/api/v1/analytics/tools/usage",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tools" in data
        assert "total_tool_calls" in data
    
    @pytest.mark.asyncio
    async def test_get_user_engagement(self, client: AsyncClient, sample_copilot_interaction, auth_headers):
        """Test user engagement endpoint."""
        response = await client.get(
            "/api/v1/analytics/users/engagement",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "top_users" in data
        assert isinstance(data["top_users"], list)
    
    @pytest.mark.asyncio
    async def test_get_cost_analytics(self, client: AsyncClient, sample_copilot_interaction, auth_headers):
        """Test cost analytics endpoint."""
        response = await client.get(
            "/api/v1/analytics/cost",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_tokens" in data
        assert "estimated_cost_usd" in data
        assert data["estimated_cost_usd"] >= 0
    
    @pytest.mark.asyncio
    async def test_get_analytics_overview(self, client: AsyncClient, sample_copilot_interaction, auth_headers):
        """Test analytics overview endpoint."""
        response = await client.get(
            "/api/v1/analytics/overview",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "workspace_breakdown" in data
        assert "top_tools" in data
        assert "top_users" in data

