from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from app.models.reading_progress import ReadingProgress
from app.models.comic import Comic


class ReadingProgressService:
    """Service for managing reading progress"""

    def __init__(self, db: Session, user_id: int = 1):
        self.db = db
        self.user_id = user_id  # Default user for now

    def get_progress(self, comic_id: int) -> Optional[ReadingProgress]:
        """Get reading progress for a comic"""
        return self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == self.user_id,
            ReadingProgress.comic_id == comic_id
        ).first()

    def update_progress(self, comic_id: int, current_page: int, total_pages: int = None) -> ReadingProgress:
        """
        Update reading progress for a comic

        Args:
            comic_id: ID of the comic
            current_page: Current page (zero-based)
            total_pages: Total pages (if None, will fetch from comic)
        """
        # Get or create progress record
        progress = self.get_progress(comic_id)

        if not progress:
            # Get total pages from comic if not provided
            if total_pages is None:
                comic = self.db.query(Comic).filter(Comic.id == comic_id).first()
                if not comic:
                    raise ValueError(f"Comic {comic_id} not found")
                total_pages = comic.page_count

            progress = ReadingProgress(
                user_id=self.user_id,
                comic_id=comic_id,
                current_page=current_page,
                total_pages=total_pages,
                completed=False
            )
            self.db.add(progress)
        else:
            # Update existing progress
            progress.current_page = current_page
            if total_pages is not None:
                progress.total_pages = total_pages
            progress.last_read_at = datetime.utcnow()

        # Check if completed (on last page)
        if current_page >= progress.total_pages - 1:
            progress.completed = True
        else:
            progress.completed = False

        self.db.commit()
        self.db.refresh(progress)

        return progress

    def mark_as_read(self, comic_id: int) -> ReadingProgress:
        """Mark a comic as completely read"""
        comic = self.db.query(Comic).filter(Comic.id == comic_id).first()
        if not comic:
            raise ValueError(f"Comic {comic_id} not found")

        progress = self.get_progress(comic_id)

        if not progress:
            progress = ReadingProgress(
                user_id=self.user_id,
                comic_id=comic_id,
                current_page=comic.page_count - 1,
                total_pages=comic.page_count,
                completed=True
            )
            self.db.add(progress)
        else:
            progress.current_page = progress.total_pages - 1
            progress.completed = True
            progress.last_read_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(progress)

        return progress

    def mark_as_unread(self, comic_id: int) -> None:
        """Remove reading progress (mark as unread)"""
        progress = self.get_progress(comic_id)

        if progress:
            self.db.delete(progress)
            self.db.commit()

    def get_recently_read(self, limit: int = 20) -> List[ReadingProgress]:
        """Get recently read comics"""
        return self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == self.user_id
        ).order_by(
            ReadingProgress.last_read_at.desc()
        ).limit(limit).all()

    def get_in_progress(self, limit: int = 20) -> List[ReadingProgress]:
        """Get comics currently being read (not completed)"""
        return self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == self.user_id,
            ReadingProgress.completed == False
        ).order_by(
            ReadingProgress.last_read_at.desc()
        ).limit(limit).all()

    def get_completed(self, limit: int = 20) -> List[ReadingProgress]:
        """Get completed comics"""
        return self.db.query(ReadingProgress).filter(
            ReadingProgress.user_id == self.user_id,
            ReadingProgress.completed == True
        ).order_by(
            ReadingProgress.last_read_at.desc()
        ).limit(limit).all()

    def get_series_progress(self, series_id: int) -> List[ReadingProgress]:
        """Get reading progress for all comics in a series"""
        return self.db.query(ReadingProgress).join(
            Comic
        ).join(
            Comic.volume
        ).filter(
            ReadingProgress.user_id == self.user_id,
            Volume.series_id == series_id
        ).order_by(
            Comic.number
        ).all()