from fastapi import APIRouter, Depends
from sqlalchemy import func
from typing import Annotated

from app.api.deps import SessionDep, AdminUser
from app.models.comic import Comic, Volume
from app.models.series import Series
from app.models.library import Library
from app.models.user import User
from app.models.reading_progress import ReadingProgress

router = APIRouter()


@router.get("/")
async def get_system_stats(
        db: SessionDep,
        admin: AdminUser
):
    """
    Get global server statistics.
    """
    # 1. Basic Counts
    library_count = db.query(Library).count()
    series_count = db.query(Series).count()
    volume_count = db.query(Volume).count()
    comic_count = db.query(Comic).count()
    user_count = db.query(User).count()

    # 2. Storage Usage (Sum of file_size column)
    # Result is in Bytes
    total_size_bytes = db.query(func.sum(Comic.file_size)).scalar() or 0

    # 3. Reading Activity
    total_read_pages = db.query(func.sum(ReadingProgress.current_page)).scalar() or 0
    completed_books = db.query(ReadingProgress).filter(ReadingProgress.completed == True).count()

    return {
        "counts": {
            "libraries": library_count,
            "series": series_count,
            "volumes": volume_count,
            "comics": comic_count,
            "users": user_count
        },
        "storage": {
            "total_bytes": total_size_bytes
        },
        "activity": {
            "pages_read": total_read_pages,
            "completed_books": completed_books
        }
    }