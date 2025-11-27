from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ReadingProgress(Base):
    """Track reading progress for comics"""
    __tablename__ = "reading_progress"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Comic being read
    comic_id = Column(Integer, ForeignKey('comics.id', ondelete='CASCADE'), nullable=False, index=True)

    # Progress tracking
    current_page = Column(Integer, default=0, nullable=False)  # Zero-based
    total_pages = Column(Integer, nullable=False)  # Denormalized for convenience
    completed = Column(Boolean, default=False, nullable=False)

    # Timestamps
    last_read_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Ensure one progress record per user per comic
    __table_args__ = (
        UniqueConstraint('user_id', 'comic_id', name='unique_user_comic_progress'),
    )

    # Relationship
    comic = relationship("Comic", back_populates="reading_progress")
    user = relationship("User", back_populates="reading_progress")

    @property
    def progress_percentage(self) -> float:
        """Calculate reading progress as percentage"""
        if self.total_pages == 0:
            return 0.0
        return (self.current_page / self.total_pages) * 100

    @property
    def pages_remaining(self) -> int:
        """Calculate pages remaining"""
        return max(0, self.total_pages - self.current_page - 1)