from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.client_service import get_client_or_404

router = APIRouter()


def _page(router_instance, path: str):
    """Decorator shorthand for page routes returning HTML."""
    def wrapper(func):
        router_instance.add_api_route(path, func, methods=["GET"], response_class=HTMLResponse)
        return func
    return wrapper


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    from src.main import templates
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/client/new", response_class=HTMLResponse)
async def new_client_form(request: Request):
    from src.main import templates
    return templates.TemplateResponse("client_form.html", {"request": request, "client": None})


@router.get("/client/{client_id}", response_class=HTMLResponse)
async def edit_client_form(request: Request, client_id: int, db: AsyncSession = Depends(get_db)):
    from src.main import templates
    client = await get_client_or_404(db, client_id)
    return templates.TemplateResponse("client_form.html", {"request": request, "client": client.to_dict()})


@router.get("/client/{client_id}/reports", response_class=HTMLResponse)
async def client_report_history(request: Request, client_id: int, db: AsyncSession = Depends(get_db)):
    from src.main import templates
    from sqlalchemy import select
    from src.models import QuarterlyReport

    client = await get_client_or_404(db, client_id)
    result = await db.execute(
        select(QuarterlyReport)
        .where(QuarterlyReport.client_id == client.id)
        .order_by(QuarterlyReport.generated_at.desc())
    )
    reports = result.scalars().all()
    return templates.TemplateResponse("report_history.html", {
        "request": request,
        "client": client.to_dict(),
        "reports": [r.to_dict() for r in reports],
    })


@router.get("/report/{client_id}", response_class=HTMLResponse)
async def report_form(request: Request, client_id: int, db: AsyncSession = Depends(get_db)):
    from src.main import templates
    client = await get_client_or_404(db, client_id)
    return templates.TemplateResponse("report_form.html", {"request": request, "client": client.to_dict()})
