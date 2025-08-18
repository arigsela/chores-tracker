"""
Pydantic schemas for reports and financial summaries.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ChildAllowanceSummary(BaseModel):
    """Enhanced child allowance summary with additional reporting fields."""
    id: int
    username: str
    completed_chores: int = Field(description="Number of approved chores")
    total_earned: float = Field(description="Total earnings from approved chores")
    total_adjustments: float = Field(description="Sum of all adjustments (bonuses/penalties)")
    paid_out: float = Field(default=0.0, description="Amount already paid out")
    balance_due: float = Field(description="Current balance owed to child")
    pending_chores_value: float = Field(default=0.0, description="Value of pending approval chores")
    last_activity_date: Optional[datetime] = Field(None, description="Date of last chore completion")


class FamilyFinancialSummary(BaseModel):
    """Family-wide financial summary for parent reporting."""
    total_children: int = Field(description="Number of children in family")
    total_earned: float = Field(description="Total earnings across all children")
    total_adjustments: float = Field(description="Total adjustments across all children")
    total_balance_due: float = Field(description="Total balance owed across all children")
    total_completed_chores: int = Field(description="Total approved chores across all children")
    period_start: Optional[datetime] = Field(None, description="Start of reporting period")
    period_end: Optional[datetime] = Field(None, description="End of reporting period")


class AllowanceSummaryResponse(BaseModel):
    """Comprehensive allowance summary response."""
    family_summary: FamilyFinancialSummary = Field(description="Family-wide financial totals")
    child_summaries: List[ChildAllowanceSummary] = Field(description="Per-child financial breakdown")


class ExportResponse(BaseModel):
    """Response model for exported data."""
    content: str = Field(description="Exported content as string")
    content_type: str = Field(description="MIME type of exported content")
    filename: str = Field(description="Suggested filename for download")


class DateRangeFilter(BaseModel):
    """Date range filter for reports."""
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    child_id: Optional[int] = Field(None, description="Filter to specific child")


class ActivityReportSummary(BaseModel):
    """Activity-based reporting summary."""
    period_start: datetime
    period_end: datetime
    total_activities: int
    chores_created: int
    chores_completed: int
    chores_approved: int
    chores_rejected: int
    adjustments_applied: int


class FinancialTrend(BaseModel):
    """Financial trend data point."""
    date: datetime
    earnings: float
    adjustments: float
    balance: float


class PerformanceMetrics(BaseModel):
    """Child performance metrics."""
    child_id: int
    child_name: str
    completion_rate: float = Field(description="Percentage of assigned chores completed")
    average_earnings_per_chore: float
    total_chores_assigned: int
    total_chores_completed: int
    most_frequent_chore_type: Optional[str] = None