"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., description="User query", min_length=1, max_length=500)
    scheme: Optional[str] = Field(None, description="Optional mutual fund scheme name")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str = Field(..., description="Generated answer")
    source: str = Field(..., description="Source URL")
    scheme: Optional[str] = Field(None, description="Mutual fund scheme if applicable")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    route: str = Field(..., description="Processing route used")
    include_url: bool = Field(..., description="Whether URL was included")


class SchemeInfo(BaseModel):
    """Model for mutual fund scheme information."""
    name: str
    category: Optional[str] = None
    source_file: Optional[str] = None


class SchemesResponse(BaseModel):
    """Response model for schemes endpoint."""
    schemes: list[SchemeInfo]


class HealthResponse(BaseModel):
    """Response model for health endpoint."""
    status: str
    version: str
    orchestrator_ready: bool


class FeedbackRequest(BaseModel):
    """Request model for feedback endpoint."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    rating: str = Field(..., description="User rating (thumbs_up/thumbs_down)")
    comment: Optional[str] = Field(None, description="Optional user comment")


class FeedbackResponse(BaseModel):
    """Response model for feedback endpoint."""
    status: str
    message: str


class NavResponse(BaseModel):
    """Response model for NAV lookup."""
    scheme: str = Field(..., description="Scheme query provided by the user")
    matched_scheme: Optional[str] = Field(None, description="Best matched scheme name from NAV source")
    nav: Optional[float] = Field(None, description="Latest NAV value")
    nav_date: Optional[str] = Field(None, description="NAV date as provided by source (dd-MMM-yyyy)")
    source_url: str = Field(..., description="Source URL for NAV data")
    note: Optional[str] = Field(None, description="Optional message when NAV cannot be found")
