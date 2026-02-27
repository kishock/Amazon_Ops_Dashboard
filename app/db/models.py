"""
Domain models representing database entities.
Currently uses dataclasses for simplicity; later may switch to ORM models.
"""
from dataclasses import dataclass


@dataclass
class Order:
    amazon_order_id: str
    status: str
