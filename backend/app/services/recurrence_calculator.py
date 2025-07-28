"""Recurrence calculation engine for determining chore reset times."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from calendar import monthrange

from ..models.chore import RecurrenceType


class RecurrenceCalculator:
    """Service for calculating chore recurrence and reset times."""
    
    @staticmethod
    def calculate_next_available_time(
        last_completion_time: datetime,
        recurrence_type: RecurrenceType,
        recurrence_value: Optional[int] = None,
        user_timezone: Optional[timezone] = None
    ) -> Optional[datetime]:
        """
        Calculate when a chore will next be available based on its recurrence settings.
        
        Args:
            last_completion_time: When the chore was last completed
            recurrence_type: Type of recurrence (daily, weekly, monthly)
            recurrence_value: For weekly (0-6 day of week) or monthly (1-31 day of month)
            user_timezone: User's timezone for accurate calculations
            
        Returns:
            Next available datetime or None if no recurrence
        """
        if recurrence_type == RecurrenceType.NONE:
            return None
            
        # Use UTC if no timezone provided
        if user_timezone is None:
            user_timezone = timezone.utc
            
        # Convert to user's timezone for calculations
        local_time = last_completion_time.replace(tzinfo=timezone.utc).astimezone(user_timezone)
        
        if recurrence_type == RecurrenceType.DAILY:
            # Next day at midnight in user's timezone
            next_time = (local_time + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
        elif recurrence_type == RecurrenceType.WEEKLY:
            # Calculate days until target day of week
            if recurrence_value is None:
                recurrence_value = 0  # Default to Sunday
                
            # Convert Sunday=0 to Python's Monday=0 system
            # Our system: Sunday=0, Monday=1, ..., Saturday=6
            # Python weekday(): Monday=0, Tuesday=1, ..., Sunday=6
            current_day = (local_time.weekday() + 1) % 7  # Convert to our system
            days_until_target = (recurrence_value - current_day) % 7
            
            # If it's the same day, schedule for next week
            if days_until_target == 0:
                days_until_target = 7
                
            next_time = (local_time + timedelta(days=days_until_target)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
        elif recurrence_type == RecurrenceType.MONTHLY:
            # Calculate next occurrence of target day
            if recurrence_value is None:
                recurrence_value = 1  # Default to 1st of month
                
            # Start with next month
            if local_time.month == 12:
                next_month = 1
                next_year = local_time.year + 1
            else:
                next_month = local_time.month + 1
                next_year = local_time.year
                
            # Handle edge cases for days that don't exist in all months
            target_day = recurrence_value
            if target_day > 28:
                # Check if target day exists in next month
                max_day = monthrange(next_year, next_month)[1]
                if target_day > max_day:
                    # Use last day of month if target doesn't exist
                    target_day = max_day
                    
            try:
                next_time = datetime(
                    next_year, next_month, target_day,
                    0, 0, 0, 0, tzinfo=user_timezone
                )
            except ValueError:
                # Fallback to last day of month if date is invalid
                max_day = monthrange(next_year, next_month)[1]
                next_time = datetime(
                    next_year, next_month, max_day,
                    0, 0, 0, 0, tzinfo=user_timezone
                )
        else:
            return None
            
        # Convert back to UTC for storage
        return next_time.astimezone(timezone.utc)
    
    @staticmethod
    def calculate_availability_progress(
        last_completion_time: Optional[datetime],
        next_available_time: Optional[datetime],
        current_time: Optional[datetime] = None
    ) -> int:
        """
        Calculate progress percentage until a chore is available again.
        
        Args:
            last_completion_time: When the chore was last completed
            next_available_time: When the chore will be available again
            current_time: Current time (defaults to now)
            
        Returns:
            Progress percentage (0-100) where 100 means available
        """
        if not last_completion_time or not next_available_time:
            return 100  # Always available if no recurrence
            
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        else:
            # Ensure timezone aware
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)
                
        # Ensure all times are timezone aware
        if last_completion_time.tzinfo is None:
            last_completion_time = last_completion_time.replace(tzinfo=timezone.utc)
        if next_available_time.tzinfo is None:
            next_available_time = next_available_time.replace(tzinfo=timezone.utc)
            
        # If past the next available time, it's fully available
        if current_time >= next_available_time:
            return 100
            
        # Calculate total duration and elapsed time
        total_duration = (next_available_time - last_completion_time).total_seconds()
        elapsed_time = (current_time - last_completion_time).total_seconds()
        
        # Avoid division by zero
        if total_duration <= 0:
            return 100
            
        # Calculate progress
        progress = int((elapsed_time / total_duration) * 100)
        
        # Ensure within bounds
        return max(0, min(100, progress))
    
    @staticmethod
    def is_chore_available(
        last_completion_time: Optional[datetime],
        next_available_time: Optional[datetime],
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if a chore is currently available to be claimed.
        
        Args:
            last_completion_time: When the chore was last completed
            next_available_time: When the chore will be available again
            current_time: Current time (defaults to now)
            
        Returns:
            True if the chore is available, False otherwise
        """
        if not next_available_time:
            return True  # No recurrence means always available
            
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        else:
            # Ensure timezone aware
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)
                
        # Ensure next_available_time is timezone aware
        if next_available_time.tzinfo is None:
            next_available_time = next_available_time.replace(tzinfo=timezone.utc)
            
        return current_time >= next_available_time
    
    @staticmethod
    def get_recurrence_description(
        recurrence_type: RecurrenceType,
        recurrence_value: Optional[int] = None
    ) -> str:
        """
        Get a human-readable description of the recurrence pattern.
        
        Args:
            recurrence_type: Type of recurrence
            recurrence_value: Value for weekly/monthly recurrence
            
        Returns:
            Human-readable description
        """
        if recurrence_type == RecurrenceType.NONE:
            return "Does not recur"
        elif recurrence_type == RecurrenceType.DAILY:
            return "Recurs daily"
        elif recurrence_type == RecurrenceType.WEEKLY:
            days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            day_name = days[recurrence_value] if recurrence_value is not None else "Sunday"
            return f"Recurs weekly on {day_name}"
        elif recurrence_type == RecurrenceType.MONTHLY:
            day = recurrence_value if recurrence_value is not None else 1
            # Handle special cases
            if day == 1:
                suffix = "st"
            elif day == 2:
                suffix = "nd"
            elif day == 3:
                suffix = "rd"
            elif day in [21, 31]:
                suffix = "st"
            elif day == 22:
                suffix = "nd"
            elif day == 23:
                suffix = "rd"
            else:
                suffix = "th"
            return f"Recurs monthly on the {day}{suffix}"
        else:
            return "Unknown recurrence"