from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class SearchFilter(BaseModel):
    """A single search filter"""
    field: Literal[
        'series', 'volume', 'number', 'title', 'publisher', 'imprint',
        'format', 'year', 'writer', 'penciller', 'inker', 'colorist',
        'letterer', 'cover_artist', 'editor', 'character', 'team',
        'location', 'collection', 'reading_list', 'series_group'
    ]
    operator: Literal['equal', 'not_equal', 'contains', 'does_not_contain', 'must_contain', 'is_empty', 'is_not_empty']
    value: Optional[str | int | List[str]] = None

class SearchRequest(BaseModel):
    """Search request with filters"""
    match: Literal['any', 'all'] = 'all'
    filters: List[SearchFilter] = Field(default_factory=list)
    sort_by: Literal['created', 'year', 'series', 'title'] = 'created'
    sort_order: Literal['asc', 'desc'] = 'desc'
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

class SearchResponse(BaseModel):
    """Search results"""
    total: int
    limit: int
    offset: int
    results: List[dict]