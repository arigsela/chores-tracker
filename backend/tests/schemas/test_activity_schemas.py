"""
Comprehensive tests for activity Pydantic schema validation.

This test suite validates input validation, data transformation, and
error handling for all activity-related schemas.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from backend.app.schemas.activity import (
    ActivityResponse,
    ActivityCreate,
    ActivityListResponse,
    ActivitySummaryResponse,
    ActivityTypes
)


class TestActivityCreateSchema:
    """Test ActivityCreate schema validation."""
    
    def test_valid_activity_create(self):
        """Test valid activity creation."""
        # Arrange
        valid_data = {
            "activity_type": "chore_completed",
            "description": "Child completed 'Clean Room' chore",
            "user_id": 123,
            "target_user_id": 456,
            "activity_data": {
                "chore_id": 789,
                "original_reward": 5.0,
                "completion_time": "2025-08-18T10:25:00"
            }
        }
        
        # Act
        activity = ActivityCreate(**valid_data)
        
        # Assert
        assert activity.activity_type == "chore_completed"
        assert activity.description == "Child completed 'Clean Room' chore"
        assert activity.user_id == 123
        assert activity.target_user_id == 456
        assert activity.activity_data["chore_id"] == 789
        assert activity.activity_data["original_reward"] == 5.0
    
    def test_activity_create_minimal_data(self):
        """Test activity creation with minimal required data."""
        # Arrange
        minimal_data = {
            "activity_type": "user_login",
            "description": "User logged in",
            "user_id": 789
            # Optional fields omitted
        }
        
        # Act
        activity = ActivityCreate(**minimal_data)
        
        # Assert
        assert activity.activity_type == "user_login"
        assert activity.description == "User logged in"
        assert activity.user_id == 789
        assert activity.target_user_id is None
        assert activity.activity_data is None
    
    def test_activity_create_empty_activity_type(self):
        """Test validation fails with empty activity type."""
        # Arrange
        invalid_data = {
            "activity_type": "",  # Empty string
            "description": "Valid description",
            "user_id": 123
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivityCreate(**invalid_data)
        
        assert "activity_type" in str(exc_info.value)
    
    def test_activity_create_long_activity_type(self):
        """Test validation fails with activity type too long."""
        # Arrange
        invalid_data = {
            "activity_type": "a" * 51,  # Exceeds 50 character limit
            "description": "Valid description",
            "user_id": 123
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivityCreate(**invalid_data)
        
        assert "activity_type" in str(exc_info.value)
    
    def test_activity_create_empty_description(self):
        """Test validation fails with empty description."""
        # Arrange
        invalid_data = {
            "activity_type": "chore_approved",
            "description": "",  # Empty description
            "user_id": 123
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivityCreate(**invalid_data)
        
        assert "description" in str(exc_info.value)
    
    def test_activity_create_long_description(self):
        """Test validation fails with description too long."""
        # Arrange
        invalid_data = {
            "activity_type": "chore_approved",
            "description": "a" * 501,  # Exceeds 500 character limit
            "user_id": 123
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivityCreate(**invalid_data)
        
        assert "description" in str(exc_info.value)
    
    def test_activity_create_negative_user_id(self):
        """Test validation with negative user ID."""
        # Arrange
        invalid_data = {
            "activity_type": "chore_created",
            "description": "Created new chore",
            "user_id": -1  # Negative ID
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivityCreate(**invalid_data)
        
        assert "user_id" in str(exc_info.value)
    
    def test_activity_create_complex_activity_data(self):
        """Test activity creation with complex activity data."""
        # Arrange
        complex_data = {
            "activity_type": "chore_approved",
            "description": "Parent approved chore with bonus",
            "user_id": 100,
            "target_user_id": 123,
            "activity_data": {
                "chore_id": 456,
                "chore_title": "Do Dishes",
                "original_reward": 3.50,
                "approved_reward": 4.00,
                "approval_reason": "Excellent job, extra bonus",
                "completion_date": "2025-08-18T11:30:00",
                "difficulty_level": "medium",
                "nested_object": {
                    "metadata": {
                        "quality_score": 9.5,
                        "time_taken_minutes": 25
                    }
                },
                "tags": ["dishes", "kitchen", "bonus"]
            }
        }
        
        # Act
        activity = ActivityCreate(**complex_data)
        
        # Assert
        assert activity.activity_data["original_reward"] == 3.50
        assert activity.activity_data["approved_reward"] == 4.00
        assert activity.activity_data["nested_object"]["metadata"]["quality_score"] == 9.5
        assert "dishes" in activity.activity_data["tags"]


class TestActivityResponseSchema:
    """Test ActivityResponse schema validation."""
    
    def test_valid_activity_response(self):
        """Test valid activity response creation."""
        # Arrange
        valid_data = {
            "id": 1,
            "activity_type": "chore_completed",
            "description": "Child completed chore",
            "user_id": 123,
            "target_user_id": 456,
            "created_at": "2025-08-18T10:30:00",
            "activity_data": {
                "chore_id": 789,
                "reward": 5.0
            }
        }
        
        # Act
        response = ActivityResponse(**valid_data)
        
        # Assert
        assert response.id == 1
        assert response.activity_type == "chore_completed"
        assert response.user_id == 123
        assert response.target_user_id == 456
        assert response.created_at.year == 2025
        assert response.activity_data["chore_id"] == 789
        assert response.user is None  # Optional relationship
        assert response.target_user is None  # Optional relationship
    
    def test_activity_response_with_user_relationships(self):
        """Test activity response with user relationship data."""
        # Arrange
        valid_data = {
            "id": 2,
            "activity_type": "chore_approved",
            "description": "Parent approved chore",
            "user_id": 100,
            "target_user_id": 123,
            "created_at": "2025-08-18T10:35:00",
            "activity_data": {"approved_reward": 5.0},
            "user": {
                "id": 100,
                "username": "parent1",
                "email": "parent@test.com",
                "is_parent": True
            },
            "target_user": {
                "id": 123,
                "username": "child1",
                "email": "child1@test.com",
                "is_parent": False
            }
        }
        
        # Act
        response = ActivityResponse(**valid_data)
        
        # Assert
        assert response.user is not None
        assert response.user.username == "parent1"
        assert response.target_user is not None
        assert response.target_user.username == "child1"
    
    def test_activity_response_invalid_id(self):
        """Test validation fails with negative ID."""
        # Arrange
        invalid_data = {
            "id": -1,  # Invalid negative ID
            "activity_type": "chore_created",
            "description": "Created chore",
            "user_id": 123,
            "created_at": "2025-08-18T10:30:00"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivityResponse(**invalid_data)
        
        assert "id" in str(exc_info.value)
    
    def test_activity_response_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        # Arrange
        incomplete_data = {
            "id": 1,
            "activity_type": "chore_completed"
            # Missing description, user_id, created_at
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivityResponse(**incomplete_data)
        
        error_str = str(exc_info.value)
        assert "description" in error_str
        assert "user_id" in error_str
        assert "created_at" in error_str


class TestActivityListResponseSchema:
    """Test ActivityListResponse schema validation."""
    
    def test_valid_activity_list_response(self):
        """Test valid activity list response creation."""
        # Arrange
        valid_data = {
            "activities": [
                {
                    "id": 1,
                    "activity_type": "chore_completed",
                    "description": "Child completed chore",
                    "user_id": 123,
                    "created_at": "2025-08-18T10:30:00"
                },
                {
                    "id": 2,
                    "activity_type": "chore_approved",
                    "description": "Parent approved chore",
                    "user_id": 100,
                    "created_at": "2025-08-18T10:35:00"
                }
            ],
            "total_count": 25,
            "has_more": True
        }
        
        # Act
        response = ActivityListResponse(**valid_data)
        
        # Assert
        assert len(response.activities) == 2
        assert response.total_count == 25
        assert response.has_more is True
        assert response.activities[0].activity_type == "chore_completed"
        assert response.activities[1].activity_type == "chore_approved"
    
    def test_activity_list_response_empty_activities(self):
        """Test activity list response with no activities."""
        # Arrange
        empty_data = {
            "activities": [],  # Empty list
            "total_count": 0,
            "has_more": False
        }
        
        # Act
        response = ActivityListResponse(**empty_data)
        
        # Assert
        assert len(response.activities) == 0
        assert response.total_count == 0
        assert response.has_more is False
    
    def test_activity_list_response_optional_total_count(self):
        """Test activity list response with optional total_count."""
        # Arrange
        no_count_data = {
            "activities": [
                {
                    "id": 1,
                    "activity_type": "user_login",
                    "description": "User logged in",
                    "user_id": 123,
                    "created_at": "2025-08-18T09:15:00"
                }
            ],
            "has_more": False
            # total_count omitted
        }
        
        # Act
        response = ActivityListResponse(**no_count_data)
        
        # Assert
        assert len(response.activities) == 1
        assert response.total_count is None
        assert response.has_more is False
    
    def test_activity_list_response_negative_total_count(self):
        """Test validation with negative total count."""
        # Arrange
        invalid_data = {
            "activities": [],
            "total_count": -5,  # Invalid negative count
            "has_more": False
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivityListResponse(**invalid_data)
        
        assert "total_count" in str(exc_info.value)


class TestActivitySummaryResponseSchema:
    """Test ActivitySummaryResponse schema validation."""
    
    def test_valid_activity_summary_response(self):
        """Test valid activity summary response creation."""
        # Arrange
        valid_data = {
            "activity_counts": {
                "chore_completed": 25,
                "chore_approved": 20,
                "chore_rejected": 3,
                "chore_created": 15,
                "adjustment_applied": 5
            },
            "total_activities": 68,
            "period_days": 30
        }
        
        # Act
        response = ActivitySummaryResponse(**valid_data)
        
        # Assert
        assert response.activity_counts["chore_completed"] == 25
        assert response.activity_counts["chore_approved"] == 20
        assert response.total_activities == 68
        assert response.period_days == 30
        assert len(response.activity_counts) == 5
    
    def test_activity_summary_response_empty_counts(self):
        """Test activity summary response with empty activity counts."""
        # Arrange
        empty_data = {
            "activity_counts": {},  # Empty dict
            "total_activities": 0,
            "period_days": 7
        }
        
        # Act
        response = ActivitySummaryResponse(**empty_data)
        
        # Assert
        assert len(response.activity_counts) == 0
        assert response.total_activities == 0
        assert response.period_days == 7
    
    def test_activity_summary_response_negative_counts(self):
        """Test validation with negative activity counts."""
        # Arrange
        invalid_data = {
            "activity_counts": {
                "chore_completed": -5  # Invalid negative count
            },
            "total_activities": 10,
            "period_days": 7
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivitySummaryResponse(**invalid_data)
        
        # Note: May depend on whether we have custom validators for negative counts
        assert "activity_counts" in str(exc_info.value) or "negative" in str(exc_info.value)
    
    def test_activity_summary_response_negative_total(self):
        """Test validation fails with negative total activities."""
        # Arrange
        invalid_data = {
            "activity_counts": {"chore_completed": 10},
            "total_activities": -10,  # Invalid negative total
            "period_days": 7
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivitySummaryResponse(**invalid_data)
        
        assert "total_activities" in str(exc_info.value)
    
    def test_activity_summary_response_zero_period_days(self):
        """Test validation fails with zero period days."""
        # Arrange
        invalid_data = {
            "activity_counts": {"chore_completed": 5},
            "total_activities": 5,
            "period_days": 0  # Invalid zero period
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ActivitySummaryResponse(**invalid_data)
        
        assert "period_days" in str(exc_info.value)


class TestActivityTypesConstants:
    """Test ActivityTypes constants and methods."""
    
    def test_activity_types_constants(self):
        """Test all activity type constants are defined."""
        # Assert
        assert ActivityTypes.CHORE_COMPLETED == "chore_completed"
        assert ActivityTypes.CHORE_APPROVED == "chore_approved"
        assert ActivityTypes.CHORE_REJECTED == "chore_rejected"
        assert ActivityTypes.CHORE_CREATED == "chore_created"
        assert ActivityTypes.ADJUSTMENT_APPLIED == "adjustment_applied"
    
    def test_get_all_types(self):
        """Test get_all_types method returns all activity types."""
        # Act
        all_types = ActivityTypes.get_all_types()
        
        # Assert
        assert isinstance(all_types, list)
        assert len(all_types) == 5
        assert "chore_completed" in all_types
        assert "chore_approved" in all_types
        assert "chore_rejected" in all_types
        assert "chore_created" in all_types
        assert "adjustment_applied" in all_types
    
    def test_get_type_descriptions(self):
        """Test get_type_descriptions method returns descriptions."""
        # Act
        descriptions = ActivityTypes.get_type_descriptions()
        
        # Assert
        assert isinstance(descriptions, dict)
        assert len(descriptions) == 5
        assert descriptions["chore_completed"] == "Child completed a chore"
        assert descriptions["chore_approved"] == "Parent approved a completed chore"
        assert descriptions["chore_rejected"] == "Parent rejected a completed chore"
        assert descriptions["chore_created"] == "Parent created a new chore"
        assert descriptions["adjustment_applied"] == "Parent applied a reward adjustment"
    
    def test_activity_types_consistency(self):
        """Test consistency between constants and methods."""
        # Arrange
        all_types = ActivityTypes.get_all_types()
        descriptions = ActivityTypes.get_type_descriptions()
        
        # Assert
        # All types should have descriptions
        for activity_type in all_types:
            assert activity_type in descriptions
        
        # All descriptions should correspond to types
        for activity_type in descriptions.keys():
            assert activity_type in all_types


class TestSchemaEdgeCasesAndIntegration:
    """Test edge cases and cross-schema integration."""
    
    def test_unicode_text_handling(self):
        """Test schemas handle unicode text correctly."""
        # Arrange
        unicode_data = {
            "activity_type": "chore_completed",
            "description": "🎉 Child completed chore with emoji! 🌟",
            "user_id": 123,
            "activity_data": {
                "completion_note": "Great job! 👍",
                "special_characters": "äöü ñ ç ⭐"
            }
        }
        
        # Act
        activity = ActivityCreate(**unicode_data)
        
        # Assert
        assert "🎉" in activity.description
        assert "🌟" in activity.description
        assert "👍" in activity.activity_data["completion_note"]
        assert "äöü" in activity.activity_data["special_characters"]
        assert "⭐" in activity.activity_data["special_characters"]
    
    def test_large_activity_data_object(self):
        """Test activity with very large activity_data object."""
        # Arrange
        large_activity_data = {}
        for i in range(100):
            large_activity_data[f"key_{i}"] = f"value_{i}" * 10  # Create large data
        
        large_data = {
            "activity_type": "system_backup",
            "description": "System performed backup with detailed logging",
            "user_id": 1,
            "activity_data": large_activity_data
        }
        
        # Act
        activity = ActivityCreate(**large_data)
        
        # Assert
        assert len(activity.activity_data) == 100
        assert "key_50" in activity.activity_data
        assert activity.activity_data["key_0"].startswith("value_0")
    
    def test_nested_activity_data_structures(self):
        """Test activity with deeply nested activity_data."""
        # Arrange
        nested_data = {
            "activity_type": "chore_approved",
            "description": "Complex approval with nested metadata",
            "user_id": 100,
            "activity_data": {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "deep_value": "Found it!",
                                "numbers": [1, 2, 3, 4, 5],
                                "boolean": True
                            }
                        }
                    }
                },
                "array_of_objects": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"}
                ]
            }
        }
        
        # Act
        activity = ActivityCreate(**nested_data)
        
        # Assert
        assert activity.activity_data["level1"]["level2"]["level3"]["level4"]["deep_value"] == "Found it!"
        assert activity.activity_data["level1"]["level2"]["level3"]["level4"]["boolean"] is True
        assert len(activity.activity_data["array_of_objects"]) == 2
        assert activity.activity_data["array_of_objects"][0]["name"] == "Item 1"
    
    def test_activity_data_with_none_values(self):
        """Test activity with activity_data containing None values."""
        # Arrange
        none_data = {
            "activity_type": "chore_rejected",
            "description": "Parent rejected chore completion",
            "user_id": 100,
            "activity_data": {
                "rejection_reason": "Task not completed properly",
                "original_reward": 5.0,
                "approved_reward": None,  # None value
                "notes": None,
                "quality_score": None
            }
        }
        
        # Act
        activity = ActivityCreate(**none_data)
        
        # Assert
        assert activity.activity_data["approved_reward"] is None
        assert activity.activity_data["notes"] is None
        assert activity.activity_data["quality_score"] is None
        assert activity.activity_data["rejection_reason"] == "Task not completed properly"
        assert activity.activity_data["original_reward"] == 5.0
    
    def test_datetime_string_coercion(self):
        """Test that datetime strings are properly parsed."""
        # Arrange
        datetime_data = {
            "id": 1,
            "activity_type": "chore_completed",
            "description": "Child completed chore",
            "user_id": 123,
            "created_at": "2025-08-18T10:30:00.123456"  # String with microseconds
        }
        
        # Act
        response = ActivityResponse(**datetime_data)
        
        # Assert
        assert isinstance(response.created_at, datetime)
        assert response.created_at.year == 2025
        assert response.created_at.month == 8
        assert response.created_at.day == 18
        assert response.created_at.hour == 10
        assert response.created_at.minute == 30
    
    def test_string_to_number_coercion(self):
        """Test that numeric strings are properly coerced."""
        # Arrange
        string_data = {
            "activity_type": "chore_approved",
            "description": "Chore approved",
            "user_id": "123",  # String that should be coerced to int
            "target_user_id": "456"  # String that should be coerced to int
        }
        
        # Act
        activity = ActivityCreate(**string_data)
        
        # Assert
        assert isinstance(activity.user_id, int)
        assert activity.user_id == 123
        assert isinstance(activity.target_user_id, int)
        assert activity.target_user_id == 456