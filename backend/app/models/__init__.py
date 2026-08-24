"""SQLModel / SQLAlchemy models.

Import concrete models here so Alembic and metadata discovery pick them up.
"""

from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeChunk
from app.models.vehicle import (
    BodyType,
    Condition,
    FuelType,
    Transmission,
    Vehicle,
)

__all__ = [
    "BodyType",
    "Condition",
    "Conversation",
    "FuelType",
    "KnowledgeChunk",
    "Message",
    "Transmission",
    "Vehicle",
]
