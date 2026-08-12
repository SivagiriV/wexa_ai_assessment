import logging
from contextlib import contextmanager
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError

from .config import settings

logger = logging.getLogger("skillpath.db")

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        if not settings.COGNODB_URI or not settings.COGNODB_PASSWORD:
            raise RuntimeError(
                "CognoDB connection is not configured. Set COGNODB_URI and "
                "COGNODB_PASSWORD (see .env.example)."
            )
        _driver = GraphDatabase.driver(
            settings.COGNODB_URI,
            auth=(settings.COGNODB_USER, settings.COGNODB_PASSWORD),
        )
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def verify_connectivity() -> tuple[bool, str]:
    """Used by the /api/health endpoint so the UI can show a clear
    'database unreachable' state instead of a generic 500."""
    try:
        get_driver().verify_connectivity()
        return True, "connected"
    except AuthError:
        return False, "authentication failed - check COGNODB_PASSWORD"
    except ServiceUnavailable:
        return False, "database unreachable - check COGNODB_URI / instance status"
    except RuntimeError as e:
        return False, str(e)
    except Exception as e:  # noqa: BLE001
        return False, f"unexpected error: {e}"


@contextmanager
def get_session():
    driver = get_driver()
    session = driver.session(database=settings.COGNODB_DATABASE)
    try:
        yield session
    finally:
        session.close()


def run_query(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Runs a parameterised Cypher query and returns a list of plain dicts.
    Every caller in this codebase passes parameters here rather than
    string-formatting values into the query."""
    params = params or {}
    try:
        with get_session() as session:
            result = session.run(query, params)
            return [record.data() for record in result]
    except (ServiceUnavailable, AuthError) as e:
        logger.error("CognoDB connection error: %s", e)
        raise ConnectionError("The graph database is currently unreachable.") from e
    except Neo4jError as e:
        logger.error("Cypher error: %s", e)
        raise
