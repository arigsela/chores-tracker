"""
Comprehensive tests for reports Pydantic schema validation.

This test suite validates input validation, data transformation, and
error handling for all reports-related schemas.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from pydantic import ValidationError

from backend.app.schemas.reports import (
    AllowanceSummaryResponse,
    ChildAllowanceSummary,
    FamilyFinancialSummary,
    ExportResponse,
    DateRangeFilter
)


class TestChildAllowanceSummarySchema:
    """Test ChildAllowanceSummary schema validation."""
    
    def test_valid_child_allowance_summary(self):
        """Test valid child allowance summary creation."""
        # Arrange
        valid_data = {
            "id": 123,
            "username": "child1",
            "completed_chores": 15,
            "total_earned": 37.5,
            "total_adjustments": 5.0,
            "paid_out": 0.0,
            "balance_due": 42.5,
            "pending_chores_value": 8.0,
            "last_activity_date": "2025-08-18T10:30:00"
        }
        
        # Act
        summary = ChildAllowanceSummary(**valid_data)
        
        # Assert
        assert summary.id == 123
        assert summary.username == "child1"
        assert summary.completed_chores == 15
        assert summary.total_earned == 37.5
        assert summary.balance_due == 42.5
        assert summary.last_activity_date.year == 2025
    
    def test_child_allowance_zero_values(self):
        """Test child allowance with zero values."""
        # Arrange
        zero_data = {
            "id": 456,
            "username": "new_child",
            "completed_chores": 0,
            "total_earned": 0.0,
            "total_adjustments": 0.0,
            "paid_out": 0.0,
            "balance_due": 0.0,
            "pending_chores_value": 0.0,
            "last_activity_date": None
        }
        
        # Act
        summary = ChildAllowanceSummary(**zero_data)
        
        # Assert
        assert summary.completed_chores == 0
        assert summary.total_earned == 0.0
        assert summary.balance_due == 0.0
        assert summary.last_activity_date is None
    
    def test_child_allowance_negative_balance(self):
        """Test child allowance with negative balance (owes money)."""
        # Arrange
        negative_data = {
            "id": 789,
            "username": "child_with_debt",
            "completed_chores": 5,
            "total_earned": 10.0,
            "total_adjustments": -15.0,  # Big penalty
            "paid_out": 0.0,
            "balance_due": -5.0,  # Owes money
            "pending_chores_value": 3.0,
            "last_activity_date": "2025-08-17T15:45:00"
        }
        
        # Act
        summary = ChildAllowanceSummary(**negative_data)
        
        # Assert
        assert summary.total_adjustments == -15.0
        assert summary.balance_due == -5.0
    
    def test_child_allowance_invalid_id(self):
        """Test validation fails with invalid ID."""
        # Arrange
        invalid_data = {
            "id": -1,  # Invalid negative ID
            "username": "child1",
            "completed_chores": 5,
            "total_earned": 12.5,
            "total_adjustments": 0.0,
            "paid_out": 0.0,
            "balance_due": 12.5,
            "pending_chores_value": 0.0,
            "last_activity_date": None
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ChildAllowanceSummary(**invalid_data)
        
        assert "id" in str(exc_info.value)
    
    def test_child_allowance_invalid_chore_count(self):
        """Test validation fails with negative chore count."""
        # Arrange
        invalid_data = {
            "id": 123,
            "username": "child1",
            "completed_chores": -5,  # Invalid negative count
            "total_earned": 25.0,
            "total_adjustments": 0.0,
            "paid_out": 0.0,
            "balance_due": 25.0,
            "pending_chores_value": 0.0,
            "last_activity_date": None
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ChildAllowanceSummary(**invalid_data)
        
        assert "completed_chores" in str(exc_info.value)
    
    def test_child_allowance_empty_username(self):
        """Test validation fails with empty username."""
        # Arrange
        invalid_data = {
            "id": 123,
            "username": "",  # Empty username
            "completed_chores": 5,
            "total_earned": 12.5,
            "total_adjustments": 0.0,
            "paid_out": 0.0,
            "balance_due": 12.5,
            "pending_chores_value": 0.0,
            "last_activity_date": None
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ChildAllowanceSummary(**invalid_data)
        
        assert "username" in str(exc_info.value)


class TestFamilyFinancialSummarySchema:
    """Test FamilyFinancialSummary schema validation."""
    
    def test_valid_family_financial_summary(self):
        """Test valid family financial summary creation."""
        # Arrange
        now = datetime.now()
        period_start = now - timedelta(days=30)
        
        valid_data = {
            "total_children": 3,
            "total_earned": 187.5,
            "total_adjustments": 25.0,
            "total_balance_due": 212.5,
            "total_completed_chores": 75,
            "period_start": period_start.isoformat(),
            "period_end": now.isoformat()
        }
        
        # Act
        summary = FamilyFinancialSummary(**valid_data)
        
        # Assert
        assert summary.total_children == 3
        assert summary.total_earned == 187.5
        assert summary.total_balance_due == 212.5
        assert summary.total_completed_chores == 75
        assert summary.period_start.year == period_start.year
        assert summary.period_end.year == now.year
    
    def test_family_summary_zero_children(self):
        """Test family summary with no children."""
        # Arrange
        now = datetime.now()
        zero_data = {
            "total_children": 0,
            "total_earned": 0.0,
            "total_adjustments": 0.0,
            "total_balance_due": 0.0,
            "total_completed_chores": 0,
            "period_start": now.isoformat(),
            "period_end": now.isoformat()
        }
        
        # Act
        summary = FamilyFinancialSummary(**zero_data)
        
        # Assert
        assert summary.total_children == 0
        assert summary.total_earned == 0.0
        assert summary.total_completed_chores == 0
    
    def test_family_summary_negative_children_count(self):
        """Test validation fails with negative children count."""
        # Arrange
        now = datetime.now()
        invalid_data = {
            "total_children": -1,  # Invalid negative count
            "total_earned": 50.0,
            "total_adjustments": 0.0,
            "total_balance_due": 50.0,
            "total_completed_chores": 20,
            "period_start": now.isoformat(),
            "period_end": now.isoformat()
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            FamilyFinancialSummary(**invalid_data)
        
        assert "total_children" in str(exc_info.value)
    
    def test_family_summary_invalid_date_range(self):
        """Test with period_end before period_start."""
        # Arrange
        now = datetime.now()
        past = now - timedelta(days=30)
        
        invalid_data = {
            "total_children": 2,
            "total_earned": 100.0,
            "total_adjustments": 10.0,
            "total_balance_due": 110.0,
            "total_completed_chores": 40,
            "period_start": now.isoformat(),  # Start after end
            "period_end": past.isoformat()   # End before start
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            FamilyFinancialSummary(**invalid_data)
        
        # Note: Custom validator should catch this
        assert "period" in str(exc_info.value) or "date" in str(exc_info.value)


class TestAllowanceSummaryResponseSchema:
    """Test AllowanceSummaryResponse schema validation."""
    
    def test_valid_allowance_summary_response(self):
        """Test valid allowance summary response creation."""
        # Arrange
        now = datetime.now()
        
        valid_data = {
            "family_summary": {
                "total_children": 2,
                "total_earned": 75.0,
                "total_adjustments": 10.0,
                "total_balance_due": 85.0,
                "total_completed_chores": 30,
                "period_start": now.isoformat(),
                "period_end": now.isoformat()
            },
            "child_summaries": [
                {
                    "id": 101,
                    "username": "child1",
                    "completed_chores": 18,
                    "total_earned": 45.0,
                    "total_adjustments": 5.0,
                    "paid_out": 0.0,
                    "balance_due": 50.0,
                    "pending_chores_value": 7.5,
                    "last_activity_date": now.isoformat()
                },
                {
                    "id": 102,
                    "username": "child2",
                    "completed_chores": 12,
                    "total_earned": 30.0,
                    "total_adjustments": 5.0,
                    "paid_out": 0.0,
                    "balance_due": 35.0,
                    "pending_chores_value": 5.0,
                    "last_activity_date": now.isoformat()
                }
            ]
        }
        
        # Act
        response = AllowanceSummaryResponse(**valid_data)
        
        # Assert
        assert response.family_summary.total_children == 2
        assert len(response.child_summaries) == 2
        assert response.child_summaries[0].username == "child1"
        assert response.child_summaries[1].balance_due == 35.0
    
    def test_allowance_summary_empty_children(self):
        """Test allowance summary with no children."""
        # Arrange
        now = datetime.now()
        
        empty_data = {
            "family_summary": {
                "total_children": 0,
                "total_earned": 0.0,
                "total_adjustments": 0.0,
                "total_balance_due": 0.0,
                "total_completed_chores": 0,
                "period_start": now.isoformat(),
                "period_end": now.isoformat()
            },
            "child_summaries": []  # Empty list
        }
        
        # Act
        response = AllowanceSummaryResponse(**empty_data)
        
        # Assert
        assert response.family_summary.total_children == 0
        assert len(response.child_summaries) == 0
    
    def test_allowance_summary_missing_family_summary(self):
        """Test validation fails when family_summary is missing."""
        # Arrange
        invalid_data = {
            # Missing family_summary
            "child_summaries": []
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AllowanceSummaryResponse(**invalid_data)
        
        assert "family_summary" in str(exc_info.value)


class TestExportResponseSchema:
    """Test ExportResponse schema validation."""
    
    def test_valid_csv_export_response(self):
        """Test valid CSV export response creation."""
        # Arrange
        csv_content = "Child Name,Completed Chores,Total Earned\nChild1,10,25.00\nChild2,8,20.00"
        
        valid_data = {
            "content": csv_content,
            "content_type": "text/csv",
            "filename": "allowance_summary_20250818_143022.csv"
        }
        
        # Act
        response = ExportResponse(**valid_data)
        
        # Assert
        assert response.content_type == "text/csv"
        assert response.filename.endswith(".csv")
        assert "Child1" in response.content
        assert len(response.content) > 0
    
    def test_valid_json_export_response(self):
        """Test valid JSON export response creation."""
        # Arrange
        json_content = '{"family_summary": {"total_children": 2}, "child_summaries": []}'
        
        valid_data = {
            "content": json_content,
            "content_type": "application/json",
            "filename": "allowance_summary_20250818_143022.json"
        }
        
        # Act
        response = ExportResponse(**valid_data)
        
        # Assert
        assert response.content_type == "application/json"
        assert response.filename.endswith(".json")
        assert "family_summary" in response.content
    
    def test_export_response_empty_content(self):
        """Test export response with empty content."""
        # Arrange
        empty_data = {
            "content": "",  # Empty content is valid
            "content_type": "text/csv",
            "filename": "empty_export.csv"
        }
        
        # Act
        response = ExportResponse(**empty_data)
        
        # Assert
        assert response.content == ""
        assert response.content_type == "text/csv"
    
    def test_export_response_invalid_content_type(self):
        """Test validation with invalid content type."""
        # Arrange
        invalid_data = {
            "content": "some content",
            "content_type": "invalid/type",  # Invalid MIME type
            "filename": "export.txt"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ExportResponse(**invalid_data)
        
        assert "content_type" in str(exc_info.value)
    
    def test_export_response_invalid_filename(self):
        """Test validation with invalid filename."""
        # Arrange
        invalid_data = {
            "content": "some content",
            "content_type": "text/csv",
            "filename": ""  # Empty filename
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ExportResponse(**invalid_data)
        
        assert "filename" in str(exc_info.value)


class TestDateRangeFilterSchema:
    """Test DateRangeFilter schema validation."""
    
    def test_valid_date_range_filter(self):
        """Test valid date range filter creation."""
        # Arrange
        valid_data = {
            "date_from": "2025-08-01",
            "date_to": "2025-08-18"
        }
        
        # Act
        filter_obj = DateRangeFilter(**valid_data)
        
        # Assert
        assert filter_obj.date_from == "2025-08-01"
        assert filter_obj.date_to == "2025-08-18"
    
    def test_date_range_filter_optional_fields(self):
        """Test date range filter with optional fields."""
        # Arrange
        partial_data = {
            "date_from": "2025-08-01"
            # date_to is optional
        }
        
        # Act
        filter_obj = DateRangeFilter(**partial_data)
        
        # Assert
        assert filter_obj.date_from == "2025-08-01"
        assert filter_obj.date_to is None
    
    def test_date_range_filter_both_none(self):
        """Test date range filter with both fields None."""
        # Arrange
        none_data = {
            "date_from": None,
            "date_to": None
        }
        
        # Act
        filter_obj = DateRangeFilter(**none_data)
        
        # Assert
        assert filter_obj.date_from is None
        assert filter_obj.date_to is None
    
    def test_date_range_filter_invalid_format(self):
        """Test validation with invalid date format."""
        # Arrange
        invalid_data = {
            "date_from": "invalid-date",  # Invalid format
            "date_to": "2025-08-18"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DateRangeFilter(**invalid_data)
        
        assert "date_from" in str(exc_info.value)


class TestSchemaCoercionAndTransformation:
    """Test data coercion and transformation capabilities."""
    
    def test_numeric_string_coercion(self):
        """Test that numeric strings are properly coerced."""
        # Arrange
        string_data = {
            "id": "123",  # String that should be coerced to int
            "username": "child1",
            "completed_chores": "15",  # String that should be coerced to int
            "total_earned": "37.50",  # String that should be coerced to float
            "total_adjustments": "5.0",
            "paid_out": "0.0",
            "balance_due": "42.50",
            "pending_chores_value": "8.0",
            "last_activity_date": "2025-08-18T10:30:00"
        }
        
        # Act
        summary = ChildAllowanceSummary(**string_data)
        
        # Assert
        assert isinstance(summary.id, int)
        assert summary.id == 123
        assert isinstance(summary.completed_chores, int)
        assert summary.completed_chores == 15
        assert isinstance(summary.total_earned, float)
        assert summary.total_earned == 37.5
    
    def test_datetime_string_parsing(self):
        """Test datetime string parsing."""
        # Arrange
        datetime_data = {
            "total_children": 1,
            "total_earned": 25.0,
            "total_adjustments": 0.0,
            "total_balance_due": 25.0,
            "total_completed_chores": 10,
            "period_start": "2025-08-01T00:00:00",
            "period_end": "2025-08-18T23:59:59"
        }
        
        # Act
        summary = FamilyFinancialSummary(**datetime_data)
        
        # Assert
        assert isinstance(summary.period_start, datetime)
        assert summary.period_start.year == 2025
        assert summary.period_start.month == 8
        assert summary.period_start.day == 1
        assert isinstance(summary.period_end, datetime)
    
    def test_decimal_precision_preservation(self):
        """Test that decimal precision is preserved for monetary values."""
        # Arrange
        precise_data = {
            "id": 123,
            "username": "precise_child",
            "completed_chores": 1,
            "total_earned": 1.005,  # Precise decimal
            "total_adjustments": 0.333,  # Repeating decimal
            "paid_out": 0.0,
            "balance_due": 1.338,
            "pending_chores_value": 0.67,
            "last_activity_date": None
        }
        
        # Act
        summary = ChildAllowanceSummary(**precise_data)
        
        # Assert
        # Check that precise values are preserved
        assert summary.total_earned == 1.005
        assert abs(summary.total_adjustments - 0.333) < 0.0001
        assert summary.balance_due == 1.338