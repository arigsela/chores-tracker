"""
Prometheus metrics for chores-tracker application.

This module defines custom business metrics that track key application
events and states. These metrics complement the automatic HTTP metrics
provided by prometheus-fastapi-instrumentator.
"""
from prometheus_client import Counter, Gauge, Histogram

# ============================================================================
# CHORE METRICS
# ============================================================================

chores_created_total = Counter(
    'chores_created_total',
    'Total number of chores created',
    ['mode']  # single, multi_independent, unassigned
)

chores_completed_total = Counter(
    'chores_completed_total',
    'Total number of chore assignments completed by children',
    ['mode']  # single, multi_independent, unassigned
)

chores_approved_total = Counter(
    'chores_approved_total',
    'Total number of chore assignments approved by parents',
    ['mode']  # single, multi_independent, unassigned
)

chores_rejected_total = Counter(
    'chores_rejected_total',
    'Total number of chore assignments rejected by parents',
    ['mode']  # single, multi_independent, unassigned
)

chore_completion_time_seconds = Histogram(
    'chore_completion_time_seconds',
    'Time taken from chore assignment creation to completion (seconds)',
    ['mode'],
    buckets=[
        3600,      # 1 hour
        43200,     # 12 hours
        86400,     # 1 day
        259200,    # 3 days
        604800,    # 1 week
        1209600,   # 2 weeks
        float('inf')
    ]
)

# ============================================================================
# ASSIGNMENT METRICS
# ============================================================================

assignments_created_total = Counter(
    'assignments_created_total',
    'Total number of chore assignments created',
    ['mode']  # single, multi_independent, unassigned
)

assignments_claimed_total = Counter(
    'assignments_claimed_total',
    'Total number of unassigned pool chores claimed by children'
)

pending_approvals_count = Gauge(
    'pending_approvals_count',
    'Current number of completed chores awaiting parent approval'
)

# ============================================================================
# USER METRICS
# ============================================================================

user_registrations_total = Counter(
    'user_registrations_total',
    'Total number of user registrations',
    ['role']  # parent, child
)

user_logins_total = Counter(
    'user_logins_total',
    'Total number of successful user logins',
    ['role']  # parent, child
)

user_login_failures_total = Counter(
    'user_login_failures_total',
    'Total number of failed login attempts'
)

active_users_count = Gauge(
    'active_users_count',
    'Current number of users with active sessions'
)

# ============================================================================
# FAMILY METRICS
# ============================================================================

families_created_total = Counter(
    'families_created_total',
    'Total number of families created'
)

family_joins_total = Counter(
    'family_joins_total',
    'Total number of parents joining existing families via invite code'
)

families_active_count = Gauge(
    'families_active_count',
    'Current number of active families with at least one parent'
)

# ============================================================================
# REWARD METRICS
# ============================================================================

reward_adjustments_total = Counter(
    'reward_adjustments_total',
    'Total number of manual reward adjustments',
    ['type']  # bonus, penalty
)

reward_adjustments_amount = Histogram(
    'reward_adjustments_amount',
    'Distribution of reward adjustment amounts',
    ['type'],  # bonus, penalty
    buckets=[5, 10, 25, 50, 100, float('inf')]
)

rewards_paid_total = Counter(
    'rewards_paid_total',
    'Total amount of rewards approved and paid to children'
)

# ============================================================================
# ERROR METRICS
# ============================================================================

api_errors_total = Counter(
    'api_errors_total',
    'Total number of API errors',
    ['endpoint', 'status_code', 'error_type']
)

database_errors_total = Counter(
    'database_errors_total',
    'Total number of database operation errors',
    ['operation']  # select, insert, update, delete
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def record_chore_creation(mode: str) -> None:
    """
    Record a chore creation event.

    Args:
        mode: Assignment mode (single, multi_independent, unassigned)
    """
    try:
        chores_created_total.labels(mode=mode).inc()
    except Exception as e:
        # Never let metrics errors affect business logic
        print(f"Error recording chore creation metric: {e}")


def record_chore_completion(mode: str, completion_time_seconds: float = None) -> None:
    """
    Record a chore completion event.

    Args:
        mode: Assignment mode
        completion_time_seconds: Optional time from creation to completion
    """
    try:
        chores_completed_total.labels(mode=mode).inc()
        if completion_time_seconds is not None:
            chore_completion_time_seconds.labels(mode=mode).observe(completion_time_seconds)
    except Exception as e:
        print(f"Error recording chore completion metric: {e}")


def record_chore_approval(mode: str, reward_amount: float = None) -> None:
    """
    Record a chore approval event.

    Args:
        mode: Assignment mode
        reward_amount: Optional reward amount approved
    """
    try:
        chores_approved_total.labels(mode=mode).inc()
        if reward_amount is not None:
            rewards_paid_total.inc(reward_amount)
    except Exception as e:
        print(f"Error recording chore approval metric: {e}")


def record_chore_rejection(mode: str) -> None:
    """
    Record a chore rejection event.

    Args:
        mode: Assignment mode
    """
    try:
        chores_rejected_total.labels(mode=mode).inc()
    except Exception as e:
        print(f"Error recording chore rejection metric: {e}")


def record_user_registration(role: str) -> None:
    """
    Record a user registration event.

    Args:
        role: User role (parent or child)
    """
    try:
        user_registrations_total.labels(role=role).inc()
    except Exception as e:
        print(f"Error recording user registration metric: {e}")


def record_user_login(role: str, success: bool = True) -> None:
    """
    Record a user login attempt.

    Args:
        role: User role (parent or child)
        success: Whether login was successful
    """
    try:
        if success:
            user_logins_total.labels(role=role).inc()
        else:
            user_login_failures_total.inc()
    except Exception as e:
        print(f"Error recording user login metric: {e}")


def record_family_event(event_type: str) -> None:
    """
    Record a family-related event.

    Args:
        event_type: Type of event (created, joined)
    """
    try:
        if event_type == 'created':
            families_created_total.inc()
        elif event_type == 'joined':
            family_joins_total.inc()
    except Exception as e:
        print(f"Error recording family event metric: {e}")


def record_reward_adjustment(adjustment_type: str, amount: float) -> None:
    """
    Record a manual reward adjustment.

    Args:
        adjustment_type: Type of adjustment (bonus or penalty)
        amount: Adjustment amount (absolute value)
    """
    try:
        reward_adjustments_total.labels(type=adjustment_type).inc()
        reward_adjustments_amount.labels(type=adjustment_type).observe(abs(amount))
    except Exception as e:
        print(f"Error recording reward adjustment metric: {e}")


def record_api_error(endpoint: str, status_code: int, error_type: str) -> None:
    """
    Record an API error.

    Args:
        endpoint: API endpoint path
        status_code: HTTP status code
        error_type: Error classification (e.g., 'not_found', 'validation')
    """
    try:
        api_errors_total.labels(
            endpoint=endpoint,
            status_code=str(status_code),
            error_type=error_type
        ).inc()
    except Exception as e:
        print(f"Error recording API error metric: {e}")


def update_pending_approvals(count: int) -> None:
    """
    Update the pending approvals gauge.

    Args:
        count: Current number of pending approvals
    """
    try:
        pending_approvals_count.set(count)
    except Exception as e:
        print(f"Error updating pending approvals metric: {e}")


def update_active_users(count: int) -> None:
    """
    Update the active users gauge.

    Args:
        count: Current number of users with active sessions
    """
    try:
        active_users_count.set(count)
    except Exception as e:
        print(f"Error updating active users metric: {e}")


def update_active_families(count: int) -> None:
    """
    Update the active families gauge.

    Args:
        count: Current number of active families
    """
    try:
        families_active_count.set(count)
    except Exception as e:
        print(f"Error updating active families metric: {e}")
