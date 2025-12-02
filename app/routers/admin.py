from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin Dashboard / Hub"""
    return templates.TemplateResponse("admin/dashboard.html", {"request": request})

@router.get("/jobs", response_class=HTMLResponse)
async def admin_jobs_page(request: Request):
    """Serve the Admin Job History page"""
    return templates.TemplateResponse("admin/jobs.html", {"request": request})

@router.get("/users", response_class=HTMLResponse)
async def admin_jobs_page(request: Request):
    """Serve the Admin User Managegment page"""
    return templates.TemplateResponse("admin/users.html", {"request": request})

@router.get("/libraries", response_class=HTMLResponse)
async def admin_jobs_page(request: Request):
    """Serve the Admin library Managegment page"""
    return templates.TemplateResponse("admin/libraries.html", {"request": request})

@router.get("/tasks", response_class=HTMLResponse)
async def admin_tasks_page(request: Request):
    """Serve the Admin Tasks page"""
    return templates.TemplateResponse("admin/tasks.html", {"request": request})

@router.get("/stats", response_class=HTMLResponse)
async def admin_stats_page(request: Request):
    """Serve the Admin Statistics page"""
    return templates.TemplateResponse("admin/stats.html", {"request": request})

@router.get("/settings", response_class=HTMLResponse)
async def admin_settings_page(request: Request):
    """Serve the Admin Settings page"""
    return templates.TemplateResponse("admin/settings.html", {"request": request})

