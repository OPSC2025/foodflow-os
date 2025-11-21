"""
AI Service Client for Backend

HTTP client for calling AI service endpoints with:
- Retry logic with exponential backoff
- Circuit breaker pattern for resilience
- Automatic tenant context injection
- Request/response logging
- Telemetry integration
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.core.config import get_settings
from src.core.logging import logger


settings = get_settings()


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by temporarily blocking requests
    to a failing service.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that triggers the breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise CircuitBreakerError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        if self.state == "half_open":
            self.state = "closed"
            logger.info("Circuit breaker closed after successful recovery")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout


class AIServiceClient:
    """
    Client for calling FoodFlow AI Service endpoints.
    
    Provides type-safe wrappers for all AI endpoints with automatic:
    - Tenant context injection
    - Retry on transient failures
    - Circuit breaker protection
    - Request/response logging
    - Telemetry integration
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize AI service client.
        
        Args:
            base_url: AI service base URL (default from settings)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url or getattr(settings, 'AI_SERVICE_URL', 'http://localhost:8001')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=httpx.HTTPError,
        )
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        tenant_id: UUID,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to AI service with retry and circuit breaker.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            tenant_id: Tenant ID for context
            payload: Request payload
            
        Returns:
            Response JSON
            
        Raises:
            CircuitBreakerError: If circuit is open
            httpx.HTTPError: On HTTP errors
        """
        # Circuit breaker check
        if self.circuit_breaker.state == "open":
            if not self.circuit_breaker._should_attempt_reset():
                raise CircuitBreakerError("AI service circuit breaker is open")
        
        start_time = datetime.utcnow()
        
        try:
            # Make request
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=payload,
                headers={"x-tenant-id": str(tenant_id)},
            )
            response.raise_for_status()
            
            # Log success
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(
                f"AI service call successful: {method} {endpoint} ({duration_ms:.2f}ms)",
                extra={
                    "tenant_id": str(tenant_id),
                    "endpoint": endpoint,
                    "duration_ms": duration_ms,
                }
            )
            
            # Circuit breaker success
            self.circuit_breaker._on_success()
            
            return response.json()
        
        except httpx.HTTPError as e:
            # Log failure
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(
                f"AI service call failed: {method} {endpoint} - {str(e)}",
                extra={
                    "tenant_id": str(tenant_id),
                    "endpoint": endpoint,
                    "duration_ms": duration_ms,
                    "error": str(e),
                }
            )
            
            # Circuit breaker failure
            self.circuit_breaker._on_failure()
            
            raise e
    
    # PlantOps endpoints
    
    async def analyze_scrap(
        self,
        tenant_id: UUID,
        plant_id: UUID,
        line_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Analyze scrap patterns for a production line."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/plantops/analyze-scrap",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "plant_id": str(plant_id),
                "line_id": str(line_id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
    
    async def suggest_trial(
        self,
        tenant_id: UUID,
        line_id: UUID,
        sku_id: str,
        current_parameters: Dict[str, Any],
        optimization_goal: str = "reduce_scrap",
    ) -> Dict[str, Any]:
        """Suggest optimal trial parameters."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/plantops/suggest-trial",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "line_id": str(line_id),
                "sku_id": sku_id,
                "current_parameters": current_parameters,
                "optimization_goal": optimization_goal,
            },
        )
    
    async def compare_batch(
        self,
        tenant_id: UUID,
        batch_id: UUID,
    ) -> Dict[str, Any]:
        """Compare batch to similar historical batches."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/plantops/compare-batch",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "batch_id": str(batch_id),
            },
        )
    
    async def compute_line_efficiency(
        self,
        tenant_id: UUID,
        line_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Calculate line efficiency metrics and money leaks."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/plantops/compute-line-efficiency",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "line_id": str(line_id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
    
    # FSQ endpoints
    
    async def compute_lot_risk(
        self,
        tenant_id: UUID,
        lot_id: UUID,
    ) -> Dict[str, Any]:
        """Calculate risk score for a production lot."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/fsq/compute-lot-risk",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "lot_id": str(lot_id),
            },
        )
    
    async def compute_supplier_risk(
        self,
        tenant_id: UUID,
        supplier_id: UUID,
    ) -> Dict[str, Any]:
        """Assess supplier risk level."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/fsq/compute-supplier-risk",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "supplier_id": str(supplier_id),
            },
        )
    
    async def ccp_drift_summary(
        self,
        tenant_id: UUID,
        plant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Analyze CCP drift over time."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/fsq/ccp-drift-summary",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "plant_id": str(plant_id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
    
    async def run_mock_recall(
        self,
        tenant_id: UUID,
        scope_type: str,
        scope_id: UUID,
    ) -> Dict[str, Any]:
        """Simulate a recall scenario."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/fsq/run-mock-recall",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "scope_type": scope_type,
                "scope_id": str(scope_id),
            },
        )
    
    async def answer_compliance_question(
        self,
        tenant_id: UUID,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        doc_ids: Optional[List[UUID]] = None,
        lot_ids: Optional[List[UUID]] = None,
    ) -> Dict[str, Any]:
        """Answer compliance/FSQ questions using RAG."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/fsq/answer-compliance-question",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "question": question,
                "context": context,
                "doc_ids": [str(d) for d in doc_ids] if doc_ids else None,
                "lot_ids": [str(l) for l in lot_ids] if lot_ids else None,
            },
        )
    
    # Planning endpoints
    
    async def generate_forecast(
        self,
        tenant_id: UUID,
        horizon_weeks: int,
        grouping: str,
        sku_ids: Optional[List[str]] = None,
        category_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate demand forecast."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/planning/generate-forecast",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "horizon_weeks": horizon_weeks,
                "grouping": grouping,
                "sku_ids": sku_ids,
                "category_ids": category_ids,
            },
        )
    
    async def generate_production_plan(
        self,
        tenant_id: UUID,
        forecast_version_id: UUID,
        horizon_weeks: int,
        plant_ids: List[UUID],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate production plan."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/planning/generate-production-plan",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "forecast_version_id": str(forecast_version_id),
                "horizon_weeks": horizon_weeks,
                "plant_ids": [str(p) for p in plant_ids],
                "constraints": constraints,
            },
        )
    
    async def recommend_safety_stocks(
        self,
        tenant_id: UUID,
        sku_ids: List[str],
        location_ids: List[UUID],
        service_level: float = 0.95,
    ) -> Dict[str, Any]:
        """Recommend safety stock levels."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/planning/recommend-safety-stocks",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "sku_ids": sku_ids,
                "location_ids": [str(l) for l in location_ids],
                "service_level": service_level,
            },
        )
    
    # Brand endpoints
    
    async def compute_margin_bridge(
        self,
        tenant_id: UUID,
        brand_id: UUID,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime,
    ) -> Dict[str, Any]:
        """Generate margin bridge analysis."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/brand/compute-margin-bridge",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "brand_id": str(brand_id),
                "period1_start": period1_start.isoformat(),
                "period1_end": period1_end.isoformat(),
                "period2_start": period2_start.isoformat(),
                "period2_end": period2_end.isoformat(),
            },
        )
    
    async def compute_copacker_risk(
        self,
        tenant_id: UUID,
        copacker_id: UUID,
    ) -> Dict[str, Any]:
        """Evaluate co-packer risk."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/brand/compute-copacker-risk",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "copacker_id": str(copacker_id),
            },
        )
    
    # Retail endpoints
    
    async def forecast_retail_demand(
        self,
        tenant_id: UUID,
        banner_id: UUID,
        store_ids: List[UUID],
        sku_ids: List[str],
        horizon_weeks: int,
    ) -> Dict[str, Any]:
        """Generate store-level demand forecast."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/retail/forecast-retail-demand",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "banner_id": str(banner_id),
                "store_ids": [str(s) for s in store_ids],
                "sku_ids": sku_ids,
                "horizon_weeks": horizon_weeks,
            },
        )
    
    async def recommend_replenishment(
        self,
        tenant_id: UUID,
        banner_id: UUID,
        store_ids: Optional[List[UUID]] = None,
        sku_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate replenishment recommendations."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/retail/recommend-replenishment",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "banner_id": str(banner_id),
                "store_ids": [str(s) for s in store_ids] if store_ids else None,
                "sku_ids": sku_ids,
            },
        )
    
    async def detect_osa_issues(
        self,
        tenant_id: UUID,
        category_id: Optional[str] = None,
        banner_id: Optional[UUID] = None,
        min_severity: str = "medium",
    ) -> Dict[str, Any]:
        """Detect on-shelf availability issues."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/retail/detect-osa-issues",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "category_id": category_id,
                "banner_id": str(banner_id) if banner_id else None,
                "min_severity": min_severity,
            },
        )
    
    async def evaluate_promo(
        self,
        tenant_id: UUID,
        promo_id: UUID,
    ) -> Dict[str, Any]:
        """Evaluate promotion effectiveness."""
        return await self._make_request(
            method="POST",
            endpoint="/api/v1/retail/evaluate-promo",
            tenant_id=tenant_id,
            payload={
                "tenant_id": str(tenant_id),
                "promo_id": str(promo_id),
            },
        )


# Singleton instance
_ai_client: Optional[AIServiceClient] = None


def get_ai_client() -> AIServiceClient:
    """Get singleton AI service client instance."""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIServiceClient()
    return _ai_client


async def close_ai_client():
    """Close AI service client."""
    global _ai_client
    if _ai_client is not None:
        await _ai_client.close()
        _ai_client = None

