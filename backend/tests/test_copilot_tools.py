"""
Tests for Copilot workspace tools.

Tests tool execution, error handling, and data formatting.
"""

import uuid

import pytest

from src.ai_orchestrator.tools.plantops_tools import get_line_status, get_batch_details
from src.ai_orchestrator.tools.fsq_tools import get_lot_details


@pytest.mark.unit
@pytest.mark.copilot
class TestPlantOpsTools:
    """Test suite for PlantOps tools."""
    
    async def test_get_line_status(self, db_session, sample_tenant, sample_production_line):
        """Test getting line status."""
        context = {
            "db": db_session,
            "tenant_id": sample_tenant.id,
        }
        
        result = await get_line_status(context, str(sample_production_line.id))
        
        assert "line_id" in result
        assert "name" in result
        assert "status" in result
        assert result["name"] == "Test Line 1"
        assert result["status"] == "running"
    
    async def test_get_line_status_not_found(self, db_session, sample_tenant):
        """Test getting non-existent line."""
        context = {
            "db": db_session,
            "tenant_id": sample_tenant.id,
        }
        
        result = await get_line_status(context, str(uuid.uuid4()))
        
        assert "error" in result
    
    async def test_get_batch_details(self, db_session, sample_tenant, sample_batch):
        """Test getting batch details."""
        context = {
            "db": db_session,
            "tenant_id": sample_tenant.id,
        }
        
        result = await get_batch_details(context, str(sample_batch.id))
        
        assert "id" in result
        assert "batch_number" in result
        assert "status" in result
        assert result["batch_number"] == "BATCH-001"


@pytest.mark.unit
@pytest.mark.copilot
class TestFSQTools:
    """Test suite for FSQ tools."""
    
    async def test_get_lot_details(self, db_session, sample_tenant, sample_lot):
        """Test getting lot details."""
        context = {
            "db": db_session,
            "tenant_id": sample_tenant.id,
        }
        
        result = await get_lot_details(context, str(sample_lot.id))
        
        assert "id" in result
        assert "lot_number" in result
        assert "status" in result
        assert result["lot_number"] == "LOT-001"
    
    async def test_get_lot_details_not_found(self, db_session, sample_tenant):
        """Test getting non-existent lot."""
        context = {
            "db": db_session,
            "tenant_id": sample_tenant.id,
        }
        
        result = await get_lot_details(context, str(uuid.uuid4()))
        
        assert "error" in result

