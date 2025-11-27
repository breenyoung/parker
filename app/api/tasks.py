from fastapi import APIRouter, Depends
from typing import Annotated

from app.api.deps import SessionDep, AdminUser
from app.services.maintenance import MaintenanceService

router = APIRouter()


@router.post("/cleanup")
async def run_cleanup_task(
        db: SessionDep,
        admin: AdminUser
):
    """
    Trigger database garbage collection.
    Removes tags, people, and collections that have no associated comics.
    """
    service = MaintenanceService(db)
    stats = service.cleanup_orphans()

    return {
        "message": "Cleanup complete",
        "stats": stats
    }