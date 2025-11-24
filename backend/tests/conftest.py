import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import httpx

# Set testing flag before importing app
os.environ["TESTING"] = "true"

from backend.app.main import app
from backend.app.db.base import Base, get_db
from backend.app.models.user import User
from backend.app.models.chore import Chore
from backend.app.core.security.password import get_password_hash
from backend.app.core.security.jwt import create_access_token
from backend.app.middleware.rate_limit import reset_limiter
from prometheus_client import REGISTRY

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create async engine for testing
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test."""
    async with test_engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session to use for testing
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Return a FastAPI test client with overridden dependencies."""
    # Reset rate limiter before each test
    reset_limiter()

    async def override_get_db():
        yield db_session

    # Override metrics access check for testing (bypass IP whitelist)
    async def override_metrics_access():
        """Allow all access to /metrics in tests."""
        return None  # No exception = access granted

    # Import metrics module to register all metrics with Prometheus
    from backend.app.core import metrics  # noqa: F401

    from backend.app.core.metrics_auth import check_metrics_access
    import backend.app.core.metrics_auth as metrics_auth_module
    from backend.app.core.metrics_auth import MetricsAccessControl

    # Initialize metrics access control for testing (allow all)
    if metrics_auth_module.metrics_access_control is None:
        metrics_auth_module.metrics_access_control = MetricsAccessControl(
            allowed_ips=["127.0.0.1", "0.0.0.0/0"],  # Allow all IPs in tests
            auth_token=None
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[check_metrics_access] = override_metrics_access
    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_parent_user(db_session):
    """Create a test parent user."""
    parent_user = User(
        email="parent@example.com",
        username="parent_user",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_parent=True
    )
    db_session.add(parent_user)
    await db_session.commit()
    await db_session.refresh(parent_user)
    return parent_user


@pytest_asyncio.fixture(scope="function")
async def test_child_user(db_session, test_parent_user):
    """Create a test child user."""
    child_user = User(
        email="child@example.com",
        username="child_user",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_parent=False,
        parent_id=test_parent_user.id
    )
    db_session.add(child_user)
    await db_session.commit()
    await db_session.refresh(child_user)
    return child_user


@pytest_asyncio.fixture(scope="function")
async def parent_token(test_parent_user):
    """Create a token for the parent user."""
    return create_access_token(subject=test_parent_user.id)


@pytest_asyncio.fixture(scope="function")
async def child_token(test_child_user):
    """Create a token for the child user."""
    return create_access_token(subject=test_child_user.id)


@pytest_asyncio.fixture(scope="function")
async def test_chore(db_session, test_parent_user, test_child_user):
    """Create a test chore with fixed reward and single assignment."""
    from backend.app.models.chore_assignment import ChoreAssignment

    chore = Chore(
        title="Clean room",
        description="Make sure to vacuum and dust",
        reward=5.00,
        is_range_reward=False,
        cooldown_days=0,
        is_recurring=False,
        is_disabled=False,
        assignment_mode="single",
        creator_id=test_parent_user.id
    )
    db_session.add(chore)
    await db_session.flush()  # Get chore.id before creating assignment

    # Create assignment for the child
    assignment = ChoreAssignment(
        chore_id=chore.id,
        assignee_id=test_child_user.id,
        is_completed=False,
        is_approved=False
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore


@pytest_asyncio.fixture(scope="function")
async def test_range_chore(db_session, test_parent_user, test_child_user):
    """Create a test chore with range-based reward and single assignment."""
    from backend.app.models.chore_assignment import ChoreAssignment

    chore = Chore(
        title="Take out trash",
        description="Empty all trash cans and take to the curb",
        reward=3.00,  # Default reward
        is_range_reward=True,
        min_reward=2.00,
        max_reward=4.00,
        cooldown_days=7,  # Weekly cooldown
        is_recurring=True,
        is_disabled=False,
        assignment_mode="single",
        creator_id=test_parent_user.id
    )
    db_session.add(chore)
    await db_session.flush()

    # Create assignment for the child
    assignment = ChoreAssignment(
        chore_id=chore.id,
        assignee_id=test_child_user.id,
        is_completed=False,
        is_approved=False
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore


@pytest_asyncio.fixture(scope="function")
async def test_disabled_chore(db_session, test_parent_user, test_child_user):
    """Create a test disabled chore with single assignment."""
    from backend.app.models.chore_assignment import ChoreAssignment

    chore = Chore(
        title="Mow lawn",
        description="Mow the front and back lawn",
        reward=10.00,
        is_range_reward=False,
        cooldown_days=14,  # Bi-weekly cooldown
        is_recurring=True,
        is_disabled=True,
        assignment_mode="single",
        creator_id=test_parent_user.id
    )
    db_session.add(chore)
    await db_session.flush()

    # Create assignment for the child
    assignment = ChoreAssignment(
        chore_id=chore.id,
        assignee_id=test_child_user.id,
        is_completed=False,
        is_approved=False
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(chore)
    return chore


@pytest_asyncio.fixture(scope="function")
async def reward_adjustment_data():
    """Sample reward adjustment data for testing."""
    return {
        "child_id": 2,
        "amount": "5.00",
        "reason": "Completed extra chores this week"
    }


@pytest_asyncio.fixture(scope="function")
async def test_reward_adjustment(db_session, test_parent_user, test_child_user):
    """Create a test reward adjustment."""
    from backend.app.models.reward_adjustment import RewardAdjustment
    
    adjustment = RewardAdjustment(
        parent_id=test_parent_user.id,
        child_id=test_child_user.id,
        amount=10.00,
        reason="Good behavior bonus"
    )
    db_session.add(adjustment)
    await db_session.commit()
    await db_session.refresh(adjustment)
    return adjustment


@pytest_asyncio.fixture(scope="function")
async def parent_with_multiple_children(db_session):
    """Create parent with multiple children for testing."""
    # Create parent
    parent = User(
        email="multiparent@example.com",
        username="multi_parent",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_parent=True
    )
    db_session.add(parent)
    await db_session.commit()
    
    # Create 3 children
    children = []
    for i in range(3):
        child = User(
            email=f"child{i+1}@example.com",
            username=f"child_{i+1}",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_parent=False,
            parent_id=parent.id
        )
        db_session.add(child)
        children.append(child)
    
    await db_session.commit()
    for child in children:
        await db_session.refresh(child)
    await db_session.refresh(parent)
    
    return {"parent": parent, "children": children}


@pytest_asyncio.fixture(scope="function")
async def adjustment_history(db_session, test_parent_user, test_child_user):
    """Create sample adjustment history for testing."""
    from backend.app.models.reward_adjustment import RewardAdjustment
    from decimal import Decimal
    from datetime import datetime, timedelta
    
    adjustments = []
    # Create 5 adjustments with different amounts and dates
    adjustment_data = [
        (Decimal("10.00"), "Initial bonus", 5),
        (Decimal("5.00"), "Good behavior", 4),
        (Decimal("-3.00"), "Minor penalty", 3),
        (Decimal("15.00"), "Excellent week", 2),
        (Decimal("-2.00"), "Late to dinner", 1)
    ]
    
    for amount, reason, days_ago in adjustment_data:
        adjustment = RewardAdjustment(
            parent_id=test_parent_user.id,
            child_id=test_child_user.id,
            amount=amount,
            reason=reason,
            created_at=datetime.utcnow() - timedelta(days=days_ago)
        )
        db_session.add(adjustment)
        adjustments.append(adjustment)
    
    await db_session.commit()
    for adj in adjustments:
        await db_session.refresh(adj)

    return adjustments


# ============================================================================
# PROMETHEUS METRICS TESTING UTILITIES
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def reset_prometheus_registry():
    """
    Prometheus registry cleanup (currently disabled).

    NOTE: Registry cleanup is DISABLED because:
    1. Our tests use before/after metric comparisons (metrics_parser)
    2. This approach works even with accumulated metrics
    3. Unregistering collectors breaks subsequent tests
    4. Test isolation is achieved through relative measurements

    If we need to re-enable registry cleanup in the future, we would need
    to re-register all metric collectors after cleanup, not just unregister them.
    """
    yield

    # Cleanup DISABLED - see note above
    # collectors = list(REGISTRY._collector_to_names.keys())
    # for collector in collectors:
    #     try:
    #         REGISTRY.unregister(collector)
    #     except Exception:
    #         pass


def parse_prometheus_metrics(content: str) -> dict:
    """
    Parse Prometheus metrics text format into a structured dictionary.

    Critical Fix: Addresses Test Issue #3 from comprehensive review.
    Enables proper value assertions instead of just checking if metric names exist.

    Args:
        content: Raw Prometheus metrics output (text format)

    Returns:
        Dictionary mapping metric names to their values and labels:
        {
            'metric_name': {
                'label_combo_1': value,
                'label_combo_2': value,
                ...
            }
        }

    Example:
        >>> content = '''
        ... # HELP chores_created_total Total chores created
        ... # TYPE chores_created_total counter
        ... chores_created_total{mode="single"} 5.0
        ... chores_created_total{mode="unassigned"} 3.0
        ... '''
        >>> metrics = parse_prometheus_metrics(content)
        >>> metrics['chores_created_total']['single']
        5.0
        >>> metrics['chores_created_total']['unassigned']
        3.0
    """
    metrics = {}

    for line in content.split('\n'):
        # Skip comments and empty lines
        if line.startswith('#') or not line.strip():
            continue

        # Skip if no space (malformed line)
        if ' ' not in line:
            continue

        try:
            # Split metric name+labels from value
            metric_part, value_str = line.rsplit(' ', 1)

            # Parse metric name and labels
            if '{' in metric_part:
                # Has labels: metric_name{label1="value1",label2="value2"}
                metric_name, labels_str = metric_part.split('{', 1)
                labels_str = labels_str.rstrip('}')

                # Parse labels into a simple key (first label value for simplicity)
                # For more complex cases, you could parse all labels
                if '=' in labels_str:
                    # Extract first label value
                    label_value = labels_str.split('="')[1].split('"')[0]
                else:
                    label_value = 'default'
            else:
                # No labels: just metric_name
                metric_name = metric_part
                label_value = 'default'

            # Convert value to float
            value = float(value_str)

            # Store in dictionary
            if metric_name not in metrics:
                metrics[metric_name] = {}
            metrics[metric_name][label_value] = value

        except (ValueError, IndexError):
            # Skip malformed lines
            continue

    return metrics


@pytest.fixture
def metrics_parser():
    """
    Fixture that provides the parse_prometheus_metrics function.

    Usage in tests:
        def test_metric_increments(client, metrics_parser):
            response = await client.get("/metrics")
            before = metrics_parser(response.text)

            # Perform action that should increment metric
            await client.post("/api/v1/chores", ...)

            response = await client.get("/metrics")
            after = metrics_parser(response.text)

            assert after['chores_created_total']['single'] == before.get('chores_created_total', {}).get('single', 0) + 1
    """
    return parse_prometheus_metrics 