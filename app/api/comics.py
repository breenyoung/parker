from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.comic import Comic, Volume
from app.models.series import Series

router = APIRouter()


@router.get("/")
async def list_comics(db: Session = Depends(get_db)):
    """List all comics"""
    comics = db.query(Comic).join(Volume).join(Series).all()

    result = []
    for comic in comics:
        result.append({
            "id": comic.id,
            "filename": comic.filename,
            "series": comic.volume.series.name,
            "volume": comic.volume.volume_number,
            "number": comic.number,
            "title": comic.title,
            "page_count": comic.page_count,
            "year": comic.year
        })

    return {
        "total": len(result),
        "comics": result
    }


@router.get("/{comic_id}")
async def get_comic(comic_id: int, db: Session = Depends(get_db)):
    """Get a specific comic with all metadata"""
    comic = db.query(Comic).filter(Comic.id == comic_id).first()

    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")

    # Build credits dictionary by role
    credits = {}
    for credit in comic.credits:
        if credit.role not in credits:
            credits[credit.role] = []
        credits[credit.role].append(credit.person.name)

    return {
        "id": comic.id,
        "filename": comic.filename,
        "file_path": comic.file_path,

        # Series info
        "series": comic.volume.series.name,
        "volume": comic.volume.volume_number,
        "number": comic.number,
        "title": comic.title,
        "summary": comic.summary,
        "web": comic.web,
        "notes": comic.notes,

        # Date
        "year": comic.year,
        "month": comic.month,
        "day": comic.day,

        # Credits (grouped by role)
        "credits": credits,

        # Publishing
        "publisher": comic.publisher,
        "imprint": comic.imprint,
        "format": comic.format,
        "series_group": comic.series_group,

        # Technical
        "page_count": comic.page_count,
        "scan_information": comic.scan_information,

        # Tags (now from relationships)
        "characters": [c.name for c in comic.characters],
        "teams": [t.name for t in comic.teams],
        "locations": [l.name for l in comic.locations],

        # Reading lists
        "alternate_series": comic.alternate_series,
        "alternate_number": comic.alternate_number,
        "story_arc": comic.story_arc,

        # Timestamps
        "created_at": comic.created_at,
        "updated_at": comic.updated_at
    }