"""
Shared FastAPI dependencies for API routes
"""
from typing import Optional
from fastapi import Query


class PaginationParams:
    """Pagination dependency for list endpoints"""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


class RiskFilterParams:
    """Filter parameters for risk endpoints"""
    def __init__(
        self,
        hazard: Optional[str] = Query(None, description="Filter by hazard type: flood, heat"),
        ward_id: Optional[str] = Query(None, description="Filter by ward ID"),
        risk_category: Optional[str] = Query(None, description="Filter by risk category: low, moderate, high, critical"),
        min_risk: Optional[float] = Query(None, ge=0, le=100, description="Minimum risk score"),
        sort_by: str = Query("final_combined_risk", description="Sort field"),
        sort_order: str = Query("desc", description="Sort order: asc, desc"),
    ):
        self.hazard = hazard
        self.ward_id = ward_id
        self.risk_category = risk_category
        self.min_risk = min_risk
        self.sort_by = sort_by
        self.sort_order = sort_order
