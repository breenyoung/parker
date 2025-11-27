from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

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
