"""Tests for the recurrence calculation engine."""
import pytest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from backend.app.services.recurrence_calculator import RecurrenceCalculator
from backend.app.models.chore import RecurrenceType


class TestRecurrenceCalculator:
    """Test cases for RecurrenceCalculator."""
    
    def test_no_recurrence(self):
        """Test that no recurrence returns None."""
        last_completion = datetime(2024, 12, 20, 10, 0, 0, tzinfo=timezone.utc)
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.NONE
        )
        
        assert next_time is None
    
    def test_daily_recurrence_utc(self):
        """Test daily recurrence in UTC."""
        last_completion = datetime(2024, 12, 20, 15, 30, 0, tzinfo=timezone.utc)
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.DAILY
        )
        
        # Should be next day at midnight UTC
        expected = datetime(2024, 12, 21, 0, 0, 0, tzinfo=timezone.utc)
        assert next_time == expected
    
    def test_daily_recurrence_with_timezone(self):
        """Test daily recurrence with specific timezone."""
        # 10 PM EST on Dec 20
        est = ZoneInfo("America/New_York")
        last_completion = datetime(2024, 12, 21, 3, 0, 0, tzinfo=timezone.utc)  # 10 PM EST
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.DAILY,
            user_timezone=est
        )
        
        # Should be midnight EST on Dec 21, which is 5 AM UTC
        expected = datetime(2024, 12, 21, 5, 0, 0, tzinfo=timezone.utc)
        assert next_time == expected
    
    def test_weekly_recurrence_same_day(self):
        """Test weekly recurrence when completed on the target day."""
        # Completed on a Monday (Python weekday 0)
        last_completion = datetime(2024, 12, 23, 10, 0, 0, tzinfo=timezone.utc)  # Monday
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.WEEKLY,
            recurrence_value=1  # Monday in our system (Sunday=0)
        )
        
        # Should be next Monday
        expected = datetime(2024, 12, 30, 0, 0, 0, tzinfo=timezone.utc)
        assert next_time == expected
    
    def test_weekly_recurrence_different_day(self):
        """Test weekly recurrence for a different day."""
        # Completed on a Monday, target is Thursday
        last_completion = datetime(2024, 12, 23, 10, 0, 0, tzinfo=timezone.utc)  # Monday
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.WEEKLY,
            recurrence_value=4  # Thursday in our system (Sunday=0)
        )
        
        # Should be this Thursday
        expected = datetime(2024, 12, 26, 0, 0, 0, tzinfo=timezone.utc)
        assert next_time == expected
    
    def test_weekly_recurrence_wrap_around(self):
        """Test weekly recurrence that wraps to next week."""
        # Completed on a Friday, target is Monday
        last_completion = datetime(2024, 12, 27, 10, 0, 0, tzinfo=timezone.utc)  # Friday
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.WEEKLY,
            recurrence_value=1  # Monday in our system (Sunday=0)
        )
        
        # Should be next Monday
        expected = datetime(2024, 12, 30, 0, 0, 0, tzinfo=timezone.utc)
        assert next_time == expected
    
    def test_monthly_recurrence_regular_day(self):
        """Test monthly recurrence for a regular day."""
        last_completion = datetime(2024, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.MONTHLY,
            recurrence_value=15
        )
        
        # Should be January 15
        expected = datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        assert next_time == expected
    
    def test_monthly_recurrence_end_of_month(self):
        """Test monthly recurrence for day 31."""
        last_completion = datetime(2024, 1, 31, 10, 0, 0, tzinfo=timezone.utc)
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.MONTHLY,
            recurrence_value=31
        )
        
        # February doesn't have 31 days, should use last day (Feb 29 in 2024)
        expected = datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc)
        assert next_time == expected
    
    def test_monthly_recurrence_february_edge_case(self):
        """Test monthly recurrence from February to March."""
        last_completion = datetime(2024, 2, 29, 10, 0, 0, tzinfo=timezone.utc)
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.MONTHLY,
            recurrence_value=31
        )
        
        # March has 31 days
        expected = datetime(2024, 3, 31, 0, 0, 0, tzinfo=timezone.utc)
        assert next_time == expected
    
    def test_monthly_recurrence_year_wrap(self):
        """Test monthly recurrence from December to January."""
        last_completion = datetime(2024, 12, 15, 10, 0, 0, tzinfo=timezone.utc)
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.MONTHLY,
            recurrence_value=15
        )
        
        # Should be January 15 of next year
        expected = datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        assert next_time == expected
    
    def test_availability_progress_no_recurrence(self):
        """Test progress calculation with no recurrence."""
        progress = RecurrenceCalculator.calculate_availability_progress(
            None,
            None
        )
        
        assert progress == 100
    
    def test_availability_progress_halfway(self):
        """Test progress calculation at halfway point."""
        last_completion = datetime(2024, 12, 20, 0, 0, 0, tzinfo=timezone.utc)
        next_available = datetime(2024, 12, 21, 0, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 12, 20, 12, 0, 0, tzinfo=timezone.utc)
        
        progress = RecurrenceCalculator.calculate_availability_progress(
            last_completion,
            next_available,
            current_time
        )
        
        assert progress == 50
    
    def test_availability_progress_complete(self):
        """Test progress calculation when fully available."""
        last_completion = datetime(2024, 12, 20, 0, 0, 0, tzinfo=timezone.utc)
        next_available = datetime(2024, 12, 21, 0, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 12, 21, 1, 0, 0, tzinfo=timezone.utc)
        
        progress = RecurrenceCalculator.calculate_availability_progress(
            last_completion,
            next_available,
            current_time
        )
        
        assert progress == 100
    
    def test_availability_progress_just_started(self):
        """Test progress calculation right after completion."""
        last_completion = datetime(2024, 12, 20, 0, 0, 0, tzinfo=timezone.utc)
        next_available = datetime(2024, 12, 21, 0, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 12, 20, 0, 1, 0, tzinfo=timezone.utc)
        
        progress = RecurrenceCalculator.calculate_availability_progress(
            last_completion,
            next_available,
            current_time
        )
        
        assert progress == 0
    
    def test_is_chore_available_no_recurrence(self):
        """Test availability check with no recurrence."""
        is_available = RecurrenceCalculator.is_chore_available(
            None,
            None
        )
        
        assert is_available is True
    
    def test_is_chore_available_before_reset(self):
        """Test availability check before reset time."""
        last_completion = datetime(2024, 12, 20, 0, 0, 0, tzinfo=timezone.utc)
        next_available = datetime(2024, 12, 21, 0, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 12, 20, 23, 59, 0, tzinfo=timezone.utc)
        
        is_available = RecurrenceCalculator.is_chore_available(
            last_completion,
            next_available,
            current_time
        )
        
        assert is_available is False
    
    def test_is_chore_available_after_reset(self):
        """Test availability check after reset time."""
        last_completion = datetime(2024, 12, 20, 0, 0, 0, tzinfo=timezone.utc)
        next_available = datetime(2024, 12, 21, 0, 0, 0, tzinfo=timezone.utc)
        current_time = datetime(2024, 12, 21, 0, 1, 0, tzinfo=timezone.utc)
        
        is_available = RecurrenceCalculator.is_chore_available(
            last_completion,
            next_available,
            current_time
        )
        
        assert is_available is True
    
    def test_recurrence_descriptions(self):
        """Test human-readable recurrence descriptions."""
        # No recurrence
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.NONE)
        assert desc == "Does not recur"
        
        # Daily
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.DAILY)
        assert desc == "Recurs daily"
        
        # Weekly
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.WEEKLY, 0)
        assert desc == "Recurs weekly on Sunday"
        
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.WEEKLY, 3)
        assert desc == "Recurs weekly on Wednesday"  # 3 = Wednesday in our system
        
        # Monthly
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.MONTHLY, 1)
        assert desc == "Recurs monthly on the 1st"
        
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.MONTHLY, 2)
        assert desc == "Recurs monthly on the 2nd"
        
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.MONTHLY, 3)
        assert desc == "Recurs monthly on the 3rd"
        
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.MONTHLY, 15)
        assert desc == "Recurs monthly on the 15th"
        
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.MONTHLY, 21)
        assert desc == "Recurs monthly on the 21st"
        
        desc = RecurrenceCalculator.get_recurrence_description(RecurrenceType.MONTHLY, 31)
        assert desc == "Recurs monthly on the 31st"
    
    def test_timezone_naive_handling(self):
        """Test that timezone-naive datetimes are handled correctly."""
        # Test with naive datetime
        last_completion = datetime(2024, 12, 20, 10, 0, 0)  # No timezone
        
        next_time = RecurrenceCalculator.calculate_next_available_time(
            last_completion,
            RecurrenceType.DAILY
        )
        
        # Should still work and return UTC
        assert next_time.tzinfo == timezone.utc
        assert next_time.date() == datetime(2024, 12, 21).date()
    
    def test_progress_with_naive_datetimes(self):
        """Test progress calculation with naive datetimes."""
        last_completion = datetime(2024, 12, 20, 0, 0, 0)  # Naive
        next_available = datetime(2024, 12, 21, 0, 0, 0)   # Naive
        current_time = datetime(2024, 12, 20, 12, 0, 0)    # Naive
        
        progress = RecurrenceCalculator.calculate_availability_progress(
            last_completion,
            next_available,
            current_time
        )
        
        assert progress == 50