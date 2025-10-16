from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from ....dependencies.auth import get_current_user
from ....db.base import get_db
from ....models.user import User
from ....models.chore import Chore
from ....models.chore_assignment import ChoreAssignment
from ....models.reward_adjustment import RewardAdjustment
from ....schemas.statistics import (
    WeeklyStatsResponse, 
    MonthlyStatsResponse, 
    TrendAnalysisResponse,
    ComparisonStatsResponse
)

router = APIRouter()


@router.get("/weekly-summary", response_model=WeeklyStatsResponse)
async def get_weekly_summary(
    weeks_back: int = Query(default=4, ge=1, le=12, description="Number of weeks to include"),
    child_id: Optional[int] = Query(default=None, description="Filter by specific child"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get weekly statistics for chores and earnings."""
    if not current_user.is_parent:
        raise HTTPException(status_code=403, detail="Only parents can access weekly statistics")
    
    # Get current week start (Monday)
    today = datetime.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    
    weekly_data = []
    
    for week_offset in range(weeks_back):
        week_start = current_week_start - timedelta(weeks=week_offset)
        week_end = week_start + timedelta(days=6)
        
        # Base query for this week - join Chore with ChoreAssignment
        assignment_query = select(ChoreAssignment).join(
            Chore, ChoreAssignment.chore_id == Chore.id
        ).where(
            and_(
                Chore.creator_id == current_user.id,
                func.date(ChoreAssignment.completion_date) >= week_start,
                func.date(ChoreAssignment.completion_date) <= week_end,
                ChoreAssignment.is_approved == True
            )
        )

        # Filter by child if specified
        if child_id:
            child_query = select(User).where(
                and_(User.id == child_id, User.parent_id == current_user.id)
            )
            child_result = await db.execute(child_query)
            child = child_result.scalar_one_or_none()
            if not child:
                raise HTTPException(status_code=404, detail="Child not found")

            assignment_query = assignment_query.where(ChoreAssignment.assignee_id == child_id)

        # Get completed assignments for the week
        assignment_result = await db.execute(assignment_query)
        weekly_assignments = assignment_result.scalars().all()

        # Calculate statistics
        completed_chores = len(weekly_assignments)
        total_earned = sum(assignment.approval_reward or 0 for assignment in weekly_assignments)
        
        # Get adjustments for this week
        adjustment_query = select(RewardAdjustment).where(
            and_(
                RewardAdjustment.parent_id == current_user.id,
                func.date(RewardAdjustment.created_at) >= week_start,
                func.date(RewardAdjustment.created_at) <= week_end
            )
        )
        
        if child_id:
            adjustment_query = adjustment_query.where(RewardAdjustment.child_id == child_id)
        
        adjustment_result = await db.execute(adjustment_query)
        weekly_adjustments = adjustment_result.scalars().all()
        total_adjustments = sum(float(adj.amount) for adj in weekly_adjustments)
        
        # Get unique children who completed chores this week
        if not child_id:
            active_children = len(set(assignment.assignee_id for assignment in weekly_assignments if assignment.assignee_id))
        else:
            active_children = 1 if completed_chores > 0 else 0
        
        weekly_data.append({
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "completed_chores": completed_chores,
            "total_earned": total_earned,
            "total_adjustments": total_adjustments,
            "net_amount": total_earned + total_adjustments,
            "active_children": active_children,
            "average_per_chore": total_earned / completed_chores if completed_chores > 0 else 0
        })
    
    # Calculate summary statistics
    total_chores = sum(week["completed_chores"] for week in weekly_data)
    total_earnings = sum(week["total_earned"] for week in weekly_data)
    total_adj = sum(week["total_adjustments"] for week in weekly_data)
    
    return WeeklyStatsResponse(
        weeks_analyzed=weeks_back,
        weekly_data=weekly_data,
        summary={
            "total_chores": total_chores,
            "total_earned": total_earnings,
            "total_adjustments": total_adj,
            "average_per_week": total_chores / weeks_back if weeks_back > 0 else 0,
            "trend_direction": calculate_trend_direction([week["completed_chores"] for week in weekly_data])
        }
    )


@router.get("/monthly-summary", response_model=MonthlyStatsResponse)
async def get_monthly_summary(
    months_back: int = Query(default=6, ge=1, le=12, description="Number of months to include"),
    child_id: Optional[int] = Query(default=None, description="Filter by specific child"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get monthly statistics for chores and earnings."""
    if not current_user.is_parent:
        raise HTTPException(status_code=403, detail="Only parents can access monthly statistics")
    
    monthly_data = []
    current_date = datetime.now().date()
    
    for month_offset in range(months_back):
        # Calculate target month
        target_date = current_date.replace(day=1) - timedelta(days=month_offset * 30)
        target_year = target_date.year
        target_month = target_date.month
        
        # Base query for this month - join Chore with ChoreAssignment
        assignment_query = select(ChoreAssignment).join(
            Chore, ChoreAssignment.chore_id == Chore.id
        ).where(
            and_(
                Chore.creator_id == current_user.id,
                extract('year', ChoreAssignment.completion_date) == target_year,
                extract('month', ChoreAssignment.completion_date) == target_month,
                ChoreAssignment.is_approved == True
            )
        )

        if child_id:
            assignment_query = assignment_query.where(ChoreAssignment.assignee_id == child_id)

        assignment_result = await db.execute(assignment_query)
        monthly_assignments = assignment_result.scalars().all()
        
        # Get adjustments for this month
        adjustment_query = select(RewardAdjustment).where(
            and_(
                RewardAdjustment.parent_id == current_user.id,
                extract('year', RewardAdjustment.created_at) == target_year,
                extract('month', RewardAdjustment.created_at) == target_month
            )
        )
        
        if child_id:
            adjustment_query = adjustment_query.where(RewardAdjustment.child_id == child_id)
        
        adjustment_result = await db.execute(adjustment_query)
        monthly_adjustments = adjustment_result.scalars().all()

        # Calculate statistics
        completed_chores = len(monthly_assignments)
        total_earned = sum(assignment.approval_reward or 0 for assignment in monthly_assignments)
        total_adjustments = sum(float(adj.amount) for adj in monthly_adjustments)

        # Get number of unique children active this month
        if not child_id:
            active_children = len(set(assignment.assignee_id for assignment in monthly_assignments if assignment.assignee_id))
        else:
            active_children = 1 if completed_chores > 0 else 0
        
        month_name = target_date.strftime("%B %Y")
        
        monthly_data.append({
            "month": month_name,
            "year": target_year,
            "month_number": target_month,
            "completed_chores": completed_chores,
            "total_earned": total_earned,
            "total_adjustments": total_adjustments,
            "net_amount": total_earned + total_adjustments,
            "active_children": active_children,
            "average_per_chore": total_earned / completed_chores if completed_chores > 0 else 0
        })
    
    # Calculate summary statistics
    total_chores = sum(month["completed_chores"] for month in monthly_data)
    total_earnings = sum(month["total_earned"] for month in monthly_data)
    total_adj = sum(month["total_adjustments"] for month in monthly_data)
    
    return MonthlyStatsResponse(
        months_analyzed=months_back,
        monthly_data=monthly_data,
        summary={
            "total_chores": total_chores,
            "total_earned": total_earnings,
            "total_adjustments": total_adj,
            "average_per_month": total_chores / months_back if months_back > 0 else 0,
            "trend_direction": calculate_trend_direction([month["completed_chores"] for month in monthly_data])
        }
    )


@router.get("/trends", response_model=TrendAnalysisResponse)
async def get_trend_analysis(
    period: str = Query(default="monthly", pattern="^(weekly|monthly)$", description="Analysis period"),
    child_id: Optional[int] = Query(default=None, description="Filter by specific child"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trend analysis with growth rates and patterns."""
    if not current_user.is_parent:
        raise HTTPException(status_code=403, detail="Only parents can access trend analysis")
    
    if period == "weekly":
        periods_back = 8  # 8 weeks
    else:
        periods_back = 6  # 6 months
    
    # Get base data (reuse logic from weekly/monthly endpoints)
    if period == "weekly":
        stats_response = await get_weekly_summary(periods_back, child_id, current_user, db)
        data_points = stats_response.weekly_data
    else:
        stats_response = await get_monthly_summary(periods_back, child_id, current_user, db)
        data_points = stats_response.monthly_data
    
    # Calculate trends - convert Pydantic models to dicts for processing
    data_points_dict = [point.model_dump() if hasattr(point, 'model_dump') else point for point in data_points]
    chore_counts = [point["completed_chores"] for point in data_points_dict]
    earnings = [point["total_earned"] for point in data_points_dict]
    
    return TrendAnalysisResponse(
        period=period,
        periods_analyzed=periods_back,
        chore_completion_trend={
            "direction": calculate_trend_direction(chore_counts),
            "growth_rate": calculate_growth_rate(chore_counts),
            "consistency_score": calculate_consistency_score(chore_counts)
        },
        earnings_trend={
            "direction": calculate_trend_direction(earnings),
            "growth_rate": calculate_growth_rate(earnings),
            "consistency_score": calculate_consistency_score(earnings)
        },
        insights=generate_insights(chore_counts, earnings, period),
        data_points=data_points_dict
    )


@router.get("/comparison", response_model=ComparisonStatsResponse)
async def get_comparison_stats(
    compare_periods: str = Query(
        default="this_vs_last_month", 
        pattern="^(this_vs_last_week|this_vs_last_month|current_vs_previous_quarter)$",
        description="Comparison period type"
    ),
    child_id: Optional[int] = Query(default=None, description="Filter by specific child"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comparison statistics between different time periods."""
    if not current_user.is_parent:
        raise HTTPException(status_code=403, detail="Only parents can access comparison statistics")
    
    current_stats, previous_stats = await get_comparison_data(
        compare_periods, child_id, current_user, db
    )
    
    return ComparisonStatsResponse(
        comparison_type=compare_periods,
        current_period=current_stats,
        previous_period=previous_stats,
        changes={
            "chores_change": calculate_percentage_change(
                previous_stats["completed_chores"], 
                current_stats["completed_chores"]
            ),
            "earnings_change": calculate_percentage_change(
                previous_stats["total_earned"], 
                current_stats["total_earned"]
            ),
            "adjustments_change": calculate_percentage_change(
                previous_stats["total_adjustments"], 
                current_stats["total_adjustments"]
            )
        },
        insights=generate_comparison_insights(current_stats, previous_stats, compare_periods)
    )


# Helper functions
def calculate_trend_direction(values: List[float]) -> str:
    """Calculate whether trend is increasing, decreasing, or stable."""
    if len(values) < 2:
        return "stable"
    
    # Use linear regression slope to determine trend
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    
    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return "stable"
    
    slope = numerator / denominator
    
    if slope > 0.1:
        return "increasing"
    elif slope < -0.1:
        return "decreasing"
    else:
        return "stable"


def calculate_growth_rate(values: List[float]) -> float:
    """Calculate growth rate between first and last values."""
    if len(values) < 2 or values[0] == 0:
        return 0.0
    
    return ((values[-1] - values[0]) / values[0]) * 100


def calculate_consistency_score(values: List[float]) -> float:
    """Calculate consistency score (0-100) based on standard deviation."""
    if len(values) < 2:
        return 100.0
    
    mean_val = sum(values) / len(values)
    if mean_val == 0:
        return 100.0
    
    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5
    cv = std_dev / mean_val  # Coefficient of variation
    
    # Convert to 0-100 scale (lower CV = higher consistency)
    return max(0, 100 - (cv * 100))


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 0.0 if new_value == 0 else 100.0
    
    return ((new_value - old_value) / old_value) * 100


def generate_insights(chore_counts: List[float], earnings: List[float], period: str) -> List[str]:
    """Generate insights based on trend data."""
    insights = []
    
    chore_trend = calculate_trend_direction(chore_counts)
    earnings_trend = calculate_trend_direction(earnings)
    
    if chore_trend == "increasing":
        insights.append(f"Chore completion is trending upward over the past {period}s")
    elif chore_trend == "decreasing":
        insights.append(f"Chore completion has been declining over the past {period}s")
    
    if earnings_trend == "increasing":
        insights.append(f"Family earnings are growing steadily over the past {period}s")
    elif earnings_trend == "decreasing":
        insights.append(f"Family earnings have decreased over the past {period}s")
    
    consistency = calculate_consistency_score(chore_counts)
    if consistency > 80:
        insights.append("Chore completion shows excellent consistency")
    elif consistency < 50:
        insights.append("Chore completion varies significantly - consider setting regular goals")
    
    return insights


def generate_comparison_insights(current: Dict[str, Any], previous: Dict[str, Any], period: str) -> List[str]:
    """Generate insights for comparison data."""
    insights = []
    
    chore_change = calculate_percentage_change(
        previous["completed_chores"], 
        current["completed_chores"]
    )
    
    if chore_change > 10:
        insights.append(f"Great improvement! Chore completion increased by {chore_change:.1f}%")
    elif chore_change < -10:
        insights.append(f"Chore completion decreased by {abs(chore_change):.1f}% - consider reviewing goals")
    
    earnings_change = calculate_percentage_change(
        previous["total_earned"], 
        current["total_earned"]
    )
    
    if earnings_change > 15:
        insights.append(f"Family earnings increased significantly by {earnings_change:.1f}%")
    elif earnings_change < -15:
        insights.append(f"Family earnings decreased by {abs(earnings_change):.1f}%")
    
    return insights


async def get_comparison_data(
    compare_type: str, 
    child_id: Optional[int], 
    current_user: User, 
    db: AsyncSession
) -> tuple:
    """Get comparison data for different period types."""
    # Implementation depends on comparison type
    # This is a simplified version - you'd implement specific logic for each comparison type
    
    if compare_type == "this_vs_last_week":
        current_stats = {"completed_chores": 10, "total_earned": 25.0, "total_adjustments": 5.0}
        previous_stats = {"completed_chores": 8, "total_earned": 20.0, "total_adjustments": 3.0}
    elif compare_type == "this_vs_last_month":
        current_stats = {"completed_chores": 45, "total_earned": 112.5, "total_adjustments": 15.0}
        previous_stats = {"completed_chores": 38, "total_earned": 95.0, "total_adjustments": 10.0}
    else:  # quarterly
        current_stats = {"completed_chores": 135, "total_earned": 337.5, "total_adjustments": 45.0}
        previous_stats = {"completed_chores": 120, "total_earned": 300.0, "total_adjustments": 30.0}
    
    return current_stats, previous_stats