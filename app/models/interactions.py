from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class UserSeries(Base):
    """
    Junction table for User <-> Series interactions.
    Stores 'Starred' (Want to Read) status.
    """
    __tablename__ = "user_series"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    series_id = Column(Integer, ForeignKey("series.id", ondelete="CASCADE"), primary_key=True)

    is_starred = Column(Boolean, default=False)
    starred_at = Column(DateTime, nullable=True)  # Sort by when they starred it

    # Relationships
    user = relationship("User", backref="series_preferences")
    series = relationship("Series", backref="user_preferences")