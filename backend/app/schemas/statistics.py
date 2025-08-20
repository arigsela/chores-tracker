from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
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
    
    @field_validator('trend_direction')
    @classmethod
    def validate_trend_direction(cls, v):
        """Validate trend direction is one of allowed values."""
        valid_trends = {"increasing", "decreasing", "stable"}
        if v not in valid_trends:
            raise ValueError(f"trend_direction must be one of: {', '.join(valid_trends)}")
        return v


class WeeklyStatsResponse(BaseModel):
    """Response model for weekly statistics."""
    weeks_analyzed: int = Field(..., gt=0, description="Number of weeks analyzed (must be positive)")
    weekly_data: List[WeeklyDataPoint] = Field(..., description="Weekly data points")
    summary: WeeklySummary = Field(..., description="Summary statistics")


class MonthlyDataPoint(BaseModel):
    """Individual month statistics."""
    month: str = Field(..., description="Month name and year (e.g., 'August 2025')")
    year: int = Field(..., ge=1900, le=2100, description="Year (must be between 1900-2100)")
    month_number: int = Field(..., ge=1, le=12, description="Month number (1-12)")
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
    
    @field_validator('trend_direction')
    @classmethod
    def validate_trend_direction(cls, v):
        """Validate trend direction is one of allowed values."""
        valid_trends = {"increasing", "decreasing", "stable"}
        if v not in valid_trends:
            raise ValueError(f"trend_direction must be one of: {', '.join(valid_trends)}")
        return v


class MonthlyStatsResponse(BaseModel):
    """Response model for monthly statistics."""
    months_analyzed: int = Field(..., description="Number of months analyzed")
    monthly_data: List[MonthlyDataPoint] = Field(..., description="Monthly data points")
    summary: MonthlySummary = Field(..., description="Summary statistics")


class TrendData(BaseModel):
    """Trend analysis for a specific metric."""
    direction: str = Field(..., description="Trend direction: increasing, decreasing, stable")
    growth_rate: float = Field(..., description="Growth rate percentage")
    consistency_score: float = Field(..., ge=0, le=100, description="Consistency score (0-100)")
    
    @field_validator('direction')
    @classmethod
    def validate_direction(cls, v):
        """Validate direction is one of allowed values."""
        valid_directions = {"increasing", "decreasing", "stable"}
        if v not in valid_directions:
            raise ValueError(f"direction must be one of: {', '.join(valid_directions)}")
        return v


class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis."""
    period: str = Field(..., description="Analysis period: weekly or monthly")
    periods_analyzed: int = Field(..., description="Number of periods analyzed")
    chore_completion_trend: TrendData = Field(..., description="Chore completion trend")
    earnings_trend: TrendData = Field(..., description="Earnings trend")
    insights: List[str] = Field(..., description="Generated insights")
    data_points: List[Dict[str, Any]] = Field(..., description="Raw data points")
    
    @field_validator('period')
    @classmethod
    def validate_period(cls, v):
        """Validate period is one of allowed values."""
        valid_periods = {"weekly", "monthly"}
        if v not in valid_periods:
            raise ValueError(f"period must be one of: {', '.join(valid_periods)}")
        return v


class PeriodStats(BaseModel):
    """Statistics for a specific period."""
    completed_chores: int = Field(..., ge=0, description="Chores completed in period (must be non-negative)")
    total_earned: float = Field(..., description="Total earned in period")
    total_adjustments: float = Field(..., description="Total adjustments in period")
    period_label: Optional[str] = Field(None, description="Label for this period")


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
    
    @field_validator('comparison_type')
    @classmethod
    def validate_comparison_type(cls, v):
        """Validate comparison type is one of allowed values."""
        valid_types = {"this_vs_last_week", "this_vs_last_month", "week_over_week", "month_over_month"}
        if v not in valid_types:
            raise ValueError(f"comparison_type must be one of: {', '.join(valid_types)}")
        return v


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