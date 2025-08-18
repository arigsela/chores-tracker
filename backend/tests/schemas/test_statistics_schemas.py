"""
Comprehensive tests for statistics Pydantic schema validation.

This test suite validates input validation, data transformation, and
error handling for all statistics-related schemas.
"""
import pytest
from datetime import datetime
from typing import Dict, Any
from pydantic import ValidationError

from backend.app.schemas.statistics import (
    WeeklyStatsResponse,
    MonthlyStatsResponse,
    TrendAnalysisResponse,
    ComparisonStatsResponse
)


class TestWeeklyStatsResponseSchema:
    """Test WeeklyStatsResponse schema validation."""
    
    def test_valid_weekly_stats_response(self):
        """Test valid weekly stats response creation."""
        # Arrange
        valid_data = {
            "weeks_analyzed": 4,
            "weekly_data": [
                {
                    "week_start": "2025-08-12",
                    "week_end": "2025-08-18",
                    "completed_chores": 10,
                    "total_earned": 25.5,
                    "total_adjustments": 2.0,
                    "net_amount": 27.5,
                    "active_children": 2,
                    "average_per_chore": 2.55
                }
            ],
            "summary": {
                "total_chores": 10,
                "total_earned": 25.5,
                "total_adjustments": 2.0,
                "average_per_week": 2.5,
                "trend_direction": "increasing"
            }
        }
        
        # Act
        response = WeeklyStatsResponse(**valid_data)
        
        # Assert
        assert response.weeks_analyzed == 4
        assert len(response.weekly_data) == 1
        assert response.summary["trend_direction"] == "increasing"
        assert response.weekly_data[0]["total_earned"] == 25.5
    
    def test_weekly_stats_with_zero_values(self):
        """Test weekly stats with zero earnings and chores."""
        # Arrange
        zero_data = {
            "weeks_analyzed": 2,
            "weekly_data": [
                {
                    "week_start": "2025-08-12",
                    "week_end": "2025-08-18", 
                    "completed_chores": 0,
                    "total_earned": 0.0,
                    "total_adjustments": 0.0,
                    "net_amount": 0.0,
                    "active_children": 0,
                    "average_per_chore": 0.0
                }
            ],
            "summary": {
                "total_chores": 0,
                "total_earned": 0.0,
                "total_adjustments": 0.0,
                "average_per_week": 0.0,
                "trend_direction": "stable"
            }
        }
        
        # Act
        response = WeeklyStatsResponse(**zero_data)
        
        # Assert
        assert response.summary["total_earned"] == 0.0
        assert response.summary["trend_direction"] == "stable"
    
    def test_weekly_stats_invalid_trend_direction(self):
        """Test validation fails with invalid trend direction."""
        # Arrange
        invalid_data = {
            "weeks_analyzed": 1,
            "weekly_data": [],
            "summary": {
                "total_chores": 5,
                "total_earned": 10.0,
                "total_adjustments": 0.0,
                "average_per_week": 5.0,
                "trend_direction": "invalid_trend"  # Invalid value
            }
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WeeklyStatsResponse(**invalid_data)
        
        assert "trend_direction" in str(exc_info.value)
    
    def test_weekly_stats_negative_weeks_analyzed(self):
        """Test validation fails with negative weeks analyzed."""
        # Arrange
        invalid_data = {
            "weeks_analyzed": -1,  # Invalid negative value
            "weekly_data": [],
            "summary": {
                "total_chores": 0,
                "total_earned": 0.0,
                "total_adjustments": 0.0,
                "average_per_week": 0.0,
                "trend_direction": "stable"
            }
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WeeklyStatsResponse(**invalid_data)
        
        assert "weeks_analyzed" in str(exc_info.value)
    
    def test_weekly_stats_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        # Arrange
        incomplete_data = {
            "weeks_analyzed": 2,
            # Missing weekly_data and summary
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WeeklyStatsResponse(**incomplete_data)
        
        error_str = str(exc_info.value)
        assert "weekly_data" in error_str
        assert "summary" in error_str


class TestMonthlyStatsResponseSchema:
    """Test MonthlyStatsResponse schema validation."""
    
    def test_valid_monthly_stats_response(self):
        """Test valid monthly stats response creation."""
        # Arrange
        valid_data = {
            "months_analyzed": 6,
            "monthly_data": [
                {
                    "month": "August 2025",
                    "year": 2025,
                    "month_number": 8,
                    "completed_chores": 45,
                    "total_earned": 112.5,
                    "total_adjustments": 15.0,
                    "net_amount": 127.5,
                    "active_children": 3,
                    "average_per_chore": 2.5
                }
            ],
            "summary": {
                "total_chores": 45,
                "total_earned": 112.5,
                "total_adjustments": 15.0,
                "average_per_month": 7.5,
                "trend_direction": "increasing"
            }
        }
        
        # Act
        response = MonthlyStatsResponse(**valid_data)
        
        # Assert
        assert response.months_analyzed == 6
        assert response.monthly_data[0]["year"] == 2025
        assert response.monthly_data[0]["month_number"] == 8
        assert response.summary["average_per_month"] == 7.5
    
    def test_monthly_stats_invalid_month_number(self):
        """Test validation with invalid month number."""
        # Arrange
        invalid_data = {
            "months_analyzed": 1,
            "monthly_data": [
                {
                    "month": "Invalid Month 2025",
                    "year": 2025,
                    "month_number": 13,  # Invalid month number
                    "completed_chores": 10,
                    "total_earned": 25.0,
                    "total_adjustments": 0.0,
                    "net_amount": 25.0,
                    "active_children": 1,
                    "average_per_chore": 2.5
                }
            ],
            "summary": {
                "total_chores": 10,
                "total_earned": 25.0,
                "total_adjustments": 0.0,
                "average_per_month": 10.0,
                "trend_direction": "stable"
            }
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MonthlyStatsResponse(**invalid_data)
        
        assert "month_number" in str(exc_info.value)
    
    def test_monthly_stats_invalid_year(self):
        """Test validation with invalid year."""
        # Arrange
        invalid_data = {
            "months_analyzed": 1,
            "monthly_data": [
                {
                    "month": "August 1899",
                    "year": 1899,  # Year too old
                    "month_number": 8,
                    "completed_chores": 10,
                    "total_earned": 25.0,
                    "total_adjustments": 0.0,
                    "net_amount": 25.0,
                    "active_children": 1,
                    "average_per_chore": 2.5
                }
            ],
            "summary": {
                "total_chores": 10,
                "total_earned": 25.0,
                "total_adjustments": 0.0,
                "average_per_month": 10.0,
                "trend_direction": "stable"
            }
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            MonthlyStatsResponse(**invalid_data)
        
        assert "year" in str(exc_info.value)


class TestTrendAnalysisResponseSchema:
    """Test TrendAnalysisResponse schema validation."""
    
    def test_valid_trend_analysis_response(self):
        """Test valid trend analysis response creation."""
        # Arrange
        valid_data = {
            "period": "monthly",
            "periods_analyzed": 6,
            "chore_completion_trend": {
                "direction": "increasing",
                "growth_rate": 25.5,
                "consistency_score": 78.2
            },
            "earnings_trend": {
                "direction": "stable",
                "growth_rate": 5.1,
                "consistency_score": 85.7
            },
            "insights": [
                "Chore completion is trending upward over the past monthlys",
                "Family earnings are stable with good consistency"
            ],
            "data_points": [
                {
                    "period": "July 2025",
                    "completed_chores": 40,
                    "total_earned": 100.0,
                    "net_amount": 105.0
                }
            ]
        }
        
        # Act
        response = TrendAnalysisResponse(**valid_data)
        
        # Assert
        assert response.period == "monthly"
        assert response.chore_completion_trend["direction"] == "increasing"
        assert response.earnings_trend["consistency_score"] == 85.7
        assert len(response.insights) == 2
    
    def test_trend_analysis_invalid_period(self):
        """Test validation fails with invalid period."""
        # Arrange
        invalid_data = {
            "period": "yearly",  # Invalid period
            "periods_analyzed": 2,
            "chore_completion_trend": {
                "direction": "stable",
                "growth_rate": 0.0,
                "consistency_score": 90.0
            },
            "earnings_trend": {
                "direction": "stable", 
                "growth_rate": 0.0,
                "consistency_score": 90.0
            },
            "insights": [],
            "data_points": []
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TrendAnalysisResponse(**invalid_data)
        
        assert "period" in str(exc_info.value)
    
    def test_trend_analysis_invalid_growth_rate(self):
        """Test validation with extreme growth rate values."""
        # Arrange
        valid_data = {
            "period": "weekly",
            "periods_analyzed": 8,
            "chore_completion_trend": {
                "direction": "increasing",
                "growth_rate": 999999.0,  # Extreme but valid value
                "consistency_score": 50.0
            },
            "earnings_trend": {
                "direction": "decreasing",
                "growth_rate": -95.5,  # Valid negative growth
                "consistency_score": 60.0
            },
            "insights": ["Extreme volatility detected"],
            "data_points": []
        }
        
        # Act - Should not raise exception for extreme but valid values
        response = TrendAnalysisResponse(**valid_data)
        
        # Assert
        assert response.chore_completion_trend["growth_rate"] == 999999.0
        assert response.earnings_trend["growth_rate"] == -95.5
    
    def test_trend_analysis_consistency_score_boundaries(self):
        """Test consistency score boundary validation."""
        # Arrange
        invalid_data = {
            "period": "monthly",
            "periods_analyzed": 3,
            "chore_completion_trend": {
                "direction": "stable",
                "growth_rate": 0.0,
                "consistency_score": 150.0  # Invalid > 100
            },
            "earnings_trend": {
                "direction": "stable",
                "growth_rate": 0.0,
                "consistency_score": -10.0  # Invalid < 0
            },
            "insights": [],
            "data_points": []
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TrendAnalysisResponse(**invalid_data)
        
        error_str = str(exc_info.value)
        assert "consistency_score" in error_str


class TestComparisonStatsResponseSchema:
    """Test ComparisonStatsResponse schema validation."""
    
    def test_valid_comparison_stats_response(self):
        """Test valid comparison stats response creation."""
        # Arrange
        valid_data = {
            "comparison_type": "this_vs_last_month",
            "current_period": {
                "completed_chores": 25,
                "total_earned": 62.5,
                "total_adjustments": 5.0,
                "period_label": "This Month"
            },
            "previous_period": {
                "completed_chores": 20,
                "total_earned": 50.0,
                "total_adjustments": 2.0,
                "period_label": "Last Month"
            },
            "changes": {
                "chores_change": 25.0,
                "earnings_change": 25.0,
                "adjustments_change": 150.0
            },
            "insights": [
                "Great improvement! Chore completion increased by 25.0%",
                "Family earnings increased significantly by 25.0%"
            ]
        }
        
        # Act
        response = ComparisonStatsResponse(**valid_data)
        
        # Assert
        assert response.comparison_type == "this_vs_last_month"
        assert response.changes["chores_change"] == 25.0
        assert len(response.insights) == 2
    
    def test_comparison_stats_invalid_comparison_type(self):
        """Test validation fails with invalid comparison type."""
        # Arrange
        invalid_data = {
            "comparison_type": "invalid_comparison",  # Invalid type
            "current_period": {
                "completed_chores": 10,
                "total_earned": 25.0,
                "total_adjustments": 0.0,
                "period_label": "Current"
            },
            "previous_period": {
                "completed_chores": 8,
                "total_earned": 20.0,
                "total_adjustments": 0.0,
                "period_label": "Previous"
            },
            "changes": {
                "chores_change": 25.0,
                "earnings_change": 25.0,
                "adjustments_change": 0.0
            },
            "insights": []
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ComparisonStatsResponse(**invalid_data)
        
        assert "comparison_type" in str(exc_info.value)
    
    def test_comparison_stats_negative_chores(self):
        """Test validation with negative chore counts."""
        # Arrange
        invalid_data = {
            "comparison_type": "this_vs_last_week",
            "current_period": {
                "completed_chores": -5,  # Invalid negative chores
                "total_earned": 25.0,
                "total_adjustments": 0.0,
                "period_label": "This Week"
            },
            "previous_period": {
                "completed_chores": 10,
                "total_earned": 30.0,
                "total_adjustments": 0.0,
                "period_label": "Last Week"
            },
            "changes": {
                "chores_change": -150.0,
                "earnings_change": -16.67,
                "adjustments_change": 0.0
            },
            "insights": []
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ComparisonStatsResponse(**invalid_data)
        
        assert "completed_chores" in str(exc_info.value)


class TestSchemaEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_insights_list(self):
        """Test schemas handle empty insights lists correctly."""
        # Arrange
        data_with_empty_insights = {
            "period": "weekly",
            "periods_analyzed": 1,
            "chore_completion_trend": {
                "direction": "stable",
                "growth_rate": 0.0,
                "consistency_score": 100.0
            },
            "earnings_trend": {
                "direction": "stable",
                "growth_rate": 0.0,
                "consistency_score": 100.0
            },
            "insights": [],  # Empty list
            "data_points": []
        }
        
        # Act
        response = TrendAnalysisResponse(**data_with_empty_insights)
        
        # Assert
        assert response.insights == []
        assert len(response.insights) == 0
    
    def test_very_large_monetary_values(self):
        """Test schemas handle very large monetary values."""
        # Arrange
        large_values_data = {
            "weeks_analyzed": 1,
            "weekly_data": [
                {
                    "week_start": "2025-08-12",
                    "week_end": "2025-08-18",
                    "completed_chores": 1000,
                    "total_earned": 999999.99,  # Very large amount
                    "total_adjustments": 100000.00,
                    "net_amount": 1099999.99,
                    "active_children": 50,
                    "average_per_chore": 999.99
                }
            ],
            "summary": {
                "total_chores": 1000,
                "total_earned": 999999.99,
                "total_adjustments": 100000.00,
                "average_per_week": 1000.0,
                "trend_direction": "increasing"
            }
        }
        
        # Act
        response = WeeklyStatsResponse(**large_values_data)
        
        # Assert
        assert response.weekly_data[0]["total_earned"] == 999999.99
        assert response.summary["total_adjustments"] == 100000.00
    
    def test_very_small_decimal_values(self):
        """Test schemas handle very small decimal values."""
        # Arrange
        small_values_data = {
            "months_analyzed": 1,
            "monthly_data": [
                {
                    "month": "August 2025",
                    "year": 2025,
                    "month_number": 8,
                    "completed_chores": 1,
                    "total_earned": 0.01,  # Very small amount
                    "total_adjustments": 0.001,  # Fractional cent
                    "net_amount": 0.011,
                    "active_children": 1,
                    "average_per_chore": 0.01
                }
            ],
            "summary": {
                "total_chores": 1,
                "total_earned": 0.01,
                "total_adjustments": 0.001,
                "average_per_month": 1.0,
                "trend_direction": "stable"
            }
        }
        
        # Act
        response = MonthlyStatsResponse(**small_values_data)
        
        # Assert
        assert response.monthly_data[0]["total_earned"] == 0.01
        assert response.monthly_data[0]["total_adjustments"] == 0.001
    
    def test_unicode_text_in_insights(self):
        """Test schemas handle unicode text in insights."""
        # Arrange
        unicode_data = {
            "comparison_type": "this_vs_last_month", 
            "current_period": {
                "completed_chores": 10,
                "total_earned": 25.0,
                "total_adjustments": 0.0,
                "period_label": "This Month"
            },
            "previous_period": {
                "completed_chores": 8,
                "total_earned": 20.0,
                "total_adjustments": 0.0,
                "period_label": "Last Month"
            },
            "changes": {
                "chores_change": 25.0,
                "earnings_change": 25.0,
                "adjustments_change": 0.0
            },
            "insights": [
                "Great progress! 🎉 Completion increased by 25%",
                "Earnings are growing steadily 📈",
                "Keep up the excellent work! 💪"
            ]
        }
        
        # Act
        response = ComparisonStatsResponse(**unicode_data)
        
        # Assert
        assert "🎉" in response.insights[0]
        assert "📈" in response.insights[1]
        assert "💪" in response.insights[2]