"""
Provides a database session generator for dependency injection.
The real implementation would yield a SQLAlchemy session or similar.
"""
from collections.abc import Generator


def get_db() -> Generator[None, None, None]:
    yield
