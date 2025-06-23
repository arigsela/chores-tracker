"""
Query performance logging configuration.

This module sets up logging for SQL queries to help identify performance issues.
"""

import logging
import time
from typing import Any
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool

# Configure query logger
query_logger = logging.getLogger("sqlalchemy.engine")
query_logger.setLevel(logging.INFO)

# Configure slow query logger
slow_query_logger = logging.getLogger("app.slow_queries")
slow_query_logger.setLevel(logging.WARNING)

# Threshold for slow queries (in seconds)
SLOW_QUERY_THRESHOLD = 1.0


def setup_query_logging(enable_all_queries: bool = False):
    """
    Set up SQL query logging.
    
    Args:
        enable_all_queries: If True, log all queries. If False, only log slow queries.
    """
    if enable_all_queries:
        # Enable SQLAlchemy's built-in query logging
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    
    # Add event listeners for query performance monitoring
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.time())
        if enable_all_queries:
            query_logger.debug("Start Query: %s", statement)
    
    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info["query_start_time"].pop(-1)
        
        # Log slow queries
        if total > SLOW_QUERY_THRESHOLD:
            slow_query_logger.warning(
                "Slow query detected (%.3f seconds): %s", 
                total, 
                statement[:200] + "..." if len(statement) > 200 else statement
            )
        elif enable_all_queries:
            query_logger.debug("Query completed in %.3f seconds", total)


def setup_connection_pool_logging():
    """Set up connection pool event logging."""
    
    @event.listens_for(Pool, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log when a new database connection is created."""
        logging.info("New database connection created")
    
    @event.listens_for(Pool, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log when a connection is checked out from the pool."""
        logging.debug("Connection checked out from pool")
    
    @event.listens_for(Pool, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log when a connection is returned to the pool."""
        logging.debug("Connection returned to pool")


# Query analysis helpers
def format_query_plan(query_plan: str) -> str:
    """Format a query execution plan for better readability."""
    lines = query_plan.split('\n')
    formatted_lines = []
    for line in lines:
        if 'rows' in line.lower() or 'cost' in line.lower():
            formatted_lines.append(f"  > {line}")
        else:
            formatted_lines.append(line)
    return '\n'.join(formatted_lines)


async def analyze_query(db_session, query_string: str):
    """
    Analyze a query's execution plan (MySQL EXPLAIN).
    
    This is useful for understanding query performance during development.
    """
    from sqlalchemy import text
    
    try:
        # For MySQL, use EXPLAIN
        if "mysql" in str(db_session.bind.url):
            result = await db_session.execute(text(f"EXPLAIN {query_string}"))
            rows = result.fetchall()
            
            analysis = "Query Analysis:\n"
            for row in rows:
                analysis += f"  Table: {row.table}, Type: {row.type}, "
                analysis += f"Possible Keys: {row.possible_keys}, Key: {row.key}, "
                analysis += f"Rows: {row.rows}\n"
            
            return analysis
    except Exception as e:
        return f"Could not analyze query: {str(e)}"
    
    return "Query analysis not available for this database type"