from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_orders_extension_columns() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if not inspector.has_table("orders"):
            return

        existing_columns = {column["name"] for column in inspector.get_columns("orders")}
        float_type = "DOUBLE PRECISION" if connection.dialect.name == "postgresql" else "FLOAT"
        statements: list[str] = []

        if "buyer" not in existing_columns:
            statements.append("ALTER TABLE orders ADD COLUMN buyer VARCHAR(100)")
        if "amount" not in existing_columns:
            statements.append(f"ALTER TABLE orders ADD COLUMN amount {float_type}")
        if "cost" not in existing_columns:
            statements.append(f"ALTER TABLE orders ADD COLUMN cost {float_type}")

        for statement in statements:
            connection.execute(text(statement))
