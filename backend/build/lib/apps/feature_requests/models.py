"""Re-export ORM models so Django app discovery picks them up."""
from .infrastructure.models import FeatureRequestRecord, VoteRecord

__all__ = ["FeatureRequestRecord", "VoteRecord"]
