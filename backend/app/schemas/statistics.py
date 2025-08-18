from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import date


class WeeklyDataPoint(BaseModel):
    """Individual week statistics."""
    week_start: str = Field(..., description="Week start date (ISO format)")
    week_end: str = Field(..., description="Week end date (ISO format)")
    completed_chores: int = Field(..., description="Number of chores completed this week")
    total_earned: float = Field(..., description="Total amount earned this week")
    total_adjustments: float = Field(..., description="Total adjustments this week")
    net_amount: float = Field(..., description="Net amount (earned + adjustments)")
    active_children: int = Field(..., description="Number of children who completed chores")
    average_per_chore: float = Field(..., description="Average earnings per chore")


class WeeklySummary(BaseModel):
    """Summary statistics for weekly data."""
    total_chores: int = Field(..., description="Total chores across all weeks")
    total_earned: float = Field(..., description="Total earnings across all weeks")
    total_adjustments: float = Field(..., description="Total adjustments across all weeks")
    average_per_week: float = Field(..., description="Average chores per week")
    trend_direction: str = Field(..., description="Trend direction: increasing, decreasing, stable")


class WeeklyStatsResponse(BaseModel):
    """Response model for weekly statistics."""
    weeks_analyzed: int = Field(..., description="Number of weeks analyzed")
    weekly_data: List[WeeklyDataPoint] = Field(..., description="Weekly data points")
    summary: WeeklySummary = Field(..., description="Summary statistics")


class MonthlyDataPoint(BaseModel):
    """Individual month statistics."""
    month: str = Field(..., description="Month name and year (e.g., 'August 2025')")
    year: int = Field(..., description="Year")
    month_number: int = Field(..., description="Month number (1-12)")
    completed_chores: int = Field(..., description="Number of chores completed this month")
    total_earned: float = Field(..., description="Total amount earned this month")
    total_adjustments: float = Field(..., description="Total adjustments this month")
    net_amount: float = Field(..., description="Net amount (earned + adjustments)")
    active_children: int = Field(..., description="Number of children who completed chores")
    average_per_chore: float = Field(..., description="Average earnings per chore")


class MonthlySummary(BaseModel):
    """Summary statistics for monthly data."""
    total_chores: int = Field(..., description="Total chores across all months")
    total_earned: float = Field(..., description="Total earnings across all months")
    total_adjustments: float = Field(..., description="Total adjustments across all months")
    average_per_month: float = Field(..., description="Average chores per month")
    trend_direction: str = Field(..., description="Trend direction: increasing, decreasing, stable")


class MonthlyStatsResponse(BaseModel):
    """Response model for monthly statistics."""
    months_analyzed: int = Field(..., description="Number of months analyzed")
    monthly_data: List[MonthlyDataPoint] = Field(..., description="Monthly data points")
    summary: MonthlySummary = Field(..., description="Summary statistics")


class TrendData(BaseModel):
    """Trend analysis for a specific metric."""
    direction: str = Field(..., description="Trend direction: increasing, decreasing, stable")
    growth_rate: float = Field(..., description="Growth rate percentage")
    consistency_score: float = Field(..., description="Consistency score (0-100)")


class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis."""
    period: str = Field(..., description="Analysis period: weekly or monthly")
    periods_analyzed: int = Field(..., description="Number of periods analyzed")
    chore_completion_trend: TrendData = Field(..., description="Chore completion trend")
    earnings_trend: TrendData = Field(..., description="Earnings trend")
    insights: List[str] = Field(..., description="Generated insights")
    data_points: List[Dict[str, Any]] = Field(..., description="Raw data points")


class PeriodStats(BaseModel):
    """Statistics for a specific period."""
    completed_chores: int = Field(..., description="Chores completed in period")
    total_earned: float = Field(..., description="Total earned in period")
    total_adjustments: float = Field(..., description="Total adjustments in period")


class ComparisonChanges(BaseModel):
    """Changes between comparison periods."""
    chores_change: float = Field(..., description="Percentage change in chores")
    earnings_change: float = Field(..., description="Percentage change in earnings")
    adjustments_change: float = Field(..., description="Percentage change in adjustments")


class ComparisonStatsResponse(BaseModel):
    """Response model for comparison statistics."""
    comparison_type: str = Field(..., description="Type of comparison")
    current_period: PeriodStats = Field(..., description="Current period statistics")
    previous_period: PeriodStats = Field(..., description="Previous period statistics")
    changes: ComparisonChanges = Field(..., description="Percentage changes")
    insights: List[str] = Field(..., description="Generated insights")


class ChildPerformanceStats(BaseModel):
    """Performance statistics for individual child."""
    child_id: int = Field(..., description="Child user ID")
    child_name: str = Field(..., description="Child username")
    completed_chores: int = Field(..., description="Total chores completed")
    total_earned: float = Field(..., description="Total amount earned")
    average_per_chore: float = Field(..., description="Average earnings per chore")
    completion_rate: float = Field(..., description="Chore completion rate percentage")
    last_activity: Optional[str] = Field(None, description="Last activity date")


class FamilyPerformanceResponse(BaseModel):
    """Response model for family performance overview."""
    period_start: str = Field(..., description="Analysis period start")
    period_end: str = Field(..., description="Analysis period end")
    family_totals: PeriodStats = Field(..., description="Family total statistics")
    child_performance: List[ChildPerformanceStats] = Field(..., description="Individual child performance")
    top_performer: Optional[ChildPerformanceStats] = Field(None, description="Top performing child")
    most_consistent: Optional[ChildPerformanceStats] = Field(None, description="Most consistent child")


class StatisticsFilters(BaseModel):
    """Filters for statistics queries."""
    start_date: Optional[str] = Field(None, description="Start date filter (ISO format)")
    end_date: Optional[str] = Field(None, description="End date filter (ISO format)")
    child_id: Optional[int] = Field(None, description="Filter by specific child")
    include_adjustments: bool = Field(True, description="Include adjustments in calculations")
    min_chore_count: int = Field(0, description="Minimum chore count threshold")