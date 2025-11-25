from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from app.database import get_db
from app.models.comic import Comic, Volume
from app.models.series import Series
from app.models.collection import Collection, CollectionItem
from app.models.reading_list import ReadingList, ReadingListItem

router = APIRouter()

# Formats that are NOT considered "plain" issues
NON_PLAIN_FORMATS = [
    'annual',
    'giant size',
    'giant-size',
    'graphic novel',
    'one shot',
    'one-shot',
    'hardcover',
    'trade paperback',
    'trade paper back',
    'tpb',
    'preview'
    'special'
]


def is_plain_issue(comic: Comic) -> bool:
    """Check if a comic is a plain issue (not annual, special, etc.)"""
    if not comic.format:
        return True
    return comic.format.lower().strip() not in NON_PLAIN_FORMATS


def is_annual(comic: Comic) -> bool:
    """Check if a comic is an annual"""
    if not comic.format:
        return False
    return comic.format.lower().strip() == 'annual'


def is_special(comic: Comic) -> bool:
    """Check if a comic is a special (has format but not plain and not annual)"""
    if not comic.format:
        return False
    format_lower = comic.format.lower().strip()
    return format_lower != 'annual' and format_lower in NON_PLAIN_FORMATS


def comic_to_dict(comic: Comic) -> Dict[str, Any]:
    """Convert a comic to a dictionary for JSON response"""
    return {
        "id": comic.id,
        "volume_number": comic.volume.volume_number,
        "number": comic.number,
        "title": comic.title,
        "year": comic.year,
        "format": comic.format,
        "filename": comic.filename
    }


def get_first_issue(comics_list: List[Comic]) -> Comic:
    """
    Get the first issue from a list of comics, prioritizing plain issues.
    
    Returns the earliest plain issue by number, or if no plain issues exist,
    returns the earliest issue overall.
    """
    if not comics_list:
        return None
    
    # Sort all comics by issue number
    sorted_comics = sorted(
        comics_list, 
        key=lambda c: float(c.number) if c.number else 0
    )
    
    # Try to find the first plain issue
    plain_comics = [c for c in sorted_comics if is_plain_issue(c)]
    
    if plain_comics:
        # Return earliest plain issue
        return plain_comics[0]
    else:
        # No plain issues, return earliest overall
        return sorted_comics[0]


@router.get("/{series_id}")
async def get_series_detail(series_id: int, db: Session = Depends(get_db)):
    """Get comprehensive series details including all issues, metadata, and related content"""
    
    # Get series
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Get all volumes for this series
    volumes = db.query(Volume).filter(Volume.series_id == series_id).all()
    
    # Get all comics for this series (through volumes)
    volume_ids = [v.id for v in volumes]
    comics = db.query(Comic).filter(Comic.volume_id.in_(volume_ids)).all()
    
    # Categorize comics using helper functions
    plain_issues = [c for c in comics if is_plain_issue(c)]
    annuals = [c for c in comics if is_annual(c)]
    specials = [c for c in comics if is_special(c)]
    
    # Sort helper function
    def sort_by_volume_and_number(comics_list):
        return sorted(
            comics_list, 
            key=lambda c: (c.volume.volume_number, float(c.number) if c.number else 0)
        )
    
    # Sort all categories
    plain_issues_sorted = sort_by_volume_and_number(plain_issues)
    annuals_sorted = sort_by_volume_and_number(annuals)
    specials_sorted = sort_by_volume_and_number(specials)
    
    # Convert to dictionaries for JSON response
    plain_issues_data = [comic_to_dict(c) for c in plain_issues_sorted]
    annuals_data = [comic_to_dict(c) for c in annuals_sorted]
    specials_data = [comic_to_dict(c) for c in specials_sorted]
    
    # Process volumes data - one entry per volume with first plain issue
    volumes_data = []
    for volume in volumes:
        # Get all comics for this volume
        volume_comics = [c for c in comics if c.volume_id == volume.id]
        
        if volume_comics:
            # Get first plain issue (or earliest if no plain issues)
            first_issue = get_first_issue(volume_comics)
            
            volumes_data.append({
                "volume_id": volume.id,
                "volume_number": volume.volume_number,
                "first_issue_id": first_issue.id,
                "issue_count": len(volume_comics)
            })
    
    # Get first issue for series cover (earliest plain issue across all volumes)
    first_issue = None
    if comics:
        # Sort by volume number first, then issue number
        sorted_comics = sort_by_volume_and_number(comics)
        
        # Try to find the first plain issue
        plain_comics = [c for c in sorted_comics if is_plain_issue(c)]
        
        if plain_comics:
            # Use earliest plain issue
            first_issue = plain_comics[0]
        else:
            # No plain issues, use earliest overall
            first_issue = sorted_comics[0] if sorted_comics else None
    
    # Get related collections (collections that contain any issue from this series)
    related_collections = []
    collection_items = db.query(CollectionItem).filter(
        CollectionItem.comic_id.in_([c.id for c in comics])
    ).all()
    
    collection_ids = list(set([item.collection_id for item in collection_items]))
    if collection_ids:
        collections = db.query(Collection).filter(Collection.id.in_(collection_ids)).all()
        for col in collections:
            related_collections.append({
                "id": col.id,
                "name": col.name,
                "description": col.description,
                "comic_count": len(col.items)
            })
    
    # Get related reading lists
    related_reading_lists = []
    reading_list_items = db.query(ReadingListItem).filter(
        ReadingListItem.comic_id.in_([c.id for c in comics])
    ).all()
    
    reading_list_ids = list(set([item.reading_list_id for item in reading_list_items]))
    if reading_list_ids:
        reading_lists = db.query(ReadingList).filter(ReadingList.id.in_(reading_list_ids)).all()
        for rl in reading_lists:
            related_reading_lists.append({
                "id": rl.id,
                "name": rl.name,
                "description": rl.description,
                "comic_count": len(rl.items)
            })
    
    # Aggregate details across all issues
    writers = set()
    pencillers = set()
    characters = set()
    teams = set()
    locations = set()
    
    for comic in comics:
        # Credits
        for credit in comic.credits:
            if credit.role == 'writer':
                writers.add(credit.person.name)
            elif credit.role == 'penciller':
                pencillers.add(credit.person.name)
        
        # Tags
        for char in comic.characters:
            characters.add(char.name)
        for team in comic.teams:
            teams.add(team.name)
        for loc in comic.locations:
            locations.add(loc.name)
    
    # Get folder path (from first volume if available)
    folder_path = None
    if volumes:
        # Assuming volumes might have a path or we derive from first comic
        if comics:
            first_comic_path = comics[0].file_path
            if first_comic_path:
                # Get directory of first comic
                from pathlib import Path
                folder_path = str(Path(first_comic_path).parent)
    
    return {
        "id": series.id,
        "name": series.name,
        "publisher": comics[0].publisher if comics else None,
        "start_year": first_issue.year if first_issue else None,
        "volume_count": len(volumes),
        "total_issues": len(plain_issues),
        "annual_count": len(annuals),
        "special_count": len(specials),
        "folder_path": folder_path,
        "volumes": volumes_data,
        # Send pre-filtered and sorted lists to frontend
        "plain_issues": plain_issues_data,
        "annuals": annuals_data,
        "specials": specials_data,
        "collections": related_collections,
        "reading_lists": related_reading_lists,
        "details": {
            "writers": sorted(list(writers)),
            "pencillers": sorted(list(pencillers)),
            "characters": sorted(list(characters)),
            "teams": sorted(list(teams)),
            "locations": sorted(list(locations))
        }
    }
