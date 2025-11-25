from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import get_db
from app.models.reading_progress import ReadingProgress
from app.services.reading_progress import ReadingProgressService

router = APIRouter()


class UpdateProgressRequest(BaseModel):
    current_page: int
    total_pages: Optional[int] = None


@router.get("/{comic_id}")
async def get_comic_progress(comic_id: int, db: Session = Depends(get_db)):
    """Get reading progress for a specific comic"""
    service = ReadingProgressService(db)
    progress = service.get_progress(comic_id)

    if not progress:
        return {
            "comic_id": comic_id,
            "has_progress": False
        }

    return {
        "comic_id": comic_id,
        "has_progress": True,
        "current_page": progress.current_page,
        "total_pages": progress.total_pages,
        "progress_percentage": progress.progress_percentage,
        "pages_remaining": progress.pages_remaining,
        "completed": progress.completed,
        "last_read_at": progress.last_read_at
    }


@router.post("/{comic_id}")
async def update_comic_progress(
        comic_id: int,
        request: UpdateProgressRequest,
        db: Session = Depends(get_db)
):
    """Update reading progress for a comic"""
    service = ReadingProgressService(db)

    try:
        progress = service.update_progress(
            comic_id,
            request.current_page,
            request.total_pages
        )

        return {
            "comic_id": comic_id,
            "current_page": progress.current_page,
            "total_pages": progress.total_pages,
            "progress_percentage": progress.progress_percentage,
            "pages_remaining": progress.pages_remaining,
            "completed": progress.completed,
            "last_read_at": progress.last_read_at
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{comic_id}/mark-read")
async def mark_comic_as_read(comic_id: int, db: Session = Depends(get_db)):
    """Mark a comic as completely read"""
    service = ReadingProgressService(db)

    try:
        progress = service.mark_as_read(comic_id)
        return {
            "comic_id": comic_id,
            "completed": True,
            "message": "Comic marked as read"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{comic_id}")
async def mark_comic_as_unread(comic_id: int, db: Session = Depends(get_db)):
    """Mark a comic as unread (remove progress)"""
    service = ReadingProgressService(db)
    service.mark_as_unread(comic_id)

    return {
        "comic_id": comic_id,
        "message": "Comic marked as unread"
    }


@router.get("/")
async def get_recent_progress(
        filter: str = Query("recent", regex="^(recent|in_progress|completed)$"),
        limit: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db)
):
    """
    Get reading progress

    Args:
        filter: 'recent' (all recently read), 'in_progress' (currently reading), 'completed' (finished)
        limit: Number of results to return
    """
    service = ReadingProgressService(db)

    if filter == "in_progress":
        progress_list = service.get_in_progress(limit)
    elif filter == "completed":
        progress_list = service.get_completed(limit)
    else:  # recent
        progress_list = service.get_recently_read(limit)

    results = []
    for progress in progress_list:
        comic = progress.comic
        results.append({
            "comic_id": comic.id,
            "series": comic.volume.series.name,
            "volume": comic.volume.volume_number,
            "number": comic.number,
            "title": comic.title,
            "filename": comic.filename,
            "current_page": progress.current_page,
            "total_pages": progress.total_pages,
            "progress_percentage": progress.progress_percentage,
            "completed": progress.completed,
            "last_read_at": progress.last_read_at
        })

    return {
        "filter": filter,
        "total": len(results),
        "results": results
    }