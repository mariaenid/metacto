"""Re-export ORM models so Django app discovery picks them up."""

from .infrastructure.models import CommentRecord

__all__ = ["CommentRecord"]
