from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Client
from src.services.client_service import (
    create_client,
    delete_client,
    get_client_or_404,
    list_clients,
    update_client,
)
from src.services.report_service import generate_report, get_report_data, get_report_or_404

router = APIRouter()


# ── Client CRUD ───────────────────────────────────────────────────────────


@router.get("/clients")
async def api_list_clients(db: AsyncSession = Depends(get_db)):
    return await list_clients(db)


@router.post("/clients", status_code=201)
async def api_create_client(
    data: dict,  # validated via Pydantic in production; kept loose for migration compat
    db: AsyncSession = Depends(get_db),
):
    payload = await data if hasattr(data, "__await__") else data
    result = await create_client(db, payload)
    return result.to_dict()


@router.get("/clients/{client_id}")
async def api_get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    client = await get_client_or_404(db, client_id)
    return client.to_dict()


@router.put("/clients/{client_id}")
async def api_update_client(
    client_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    payload = await data if hasattr(data, "__await__") else data
    client = await get_client_or_404(db, client_id)
    result = await update_client(db, client, payload)
    return result.to_dict()


@router.delete("/clients/{client_id}")
async def api_delete_client(client_id: int, db: AsyncSession = Depends(get_db)):
    client = await get_client_or_404(db, client_id)
    await delete_client(db, client)
    return {"message": "Client deleted"}


# ── Report endpoints ──────────────────────────────────────────────────────


@router.get("/clients/{client_id}/report-data")
async def api_get_report_data(client_id: int, db: AsyncSession = Depends(get_db)):
    client = await get_client_or_404(db, client_id)
    return await get_report_data(db, client)


@router.post("/clients/{client_id}/reports", status_code=201)
async def api_generate_report(
    client_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    payload = await data if hasattr(data, "__await__") else data
    client = await get_client_or_404(db, client_id)

    quarter = payload.get("quarter")
    year = payload.get("year")
    if not quarter or not year:
        raise HTTPException(status_code=400, detail="Quarter and year are required")
    try:
        year = int(year)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Year must be a number")

    balances = payload.get("balances", {})
    return await generate_report(db, client, quarter, year, balances)


@router.get("/reports/{report_id}/download/{pdf_type}")
async def api_download_pdf(report_id: int, pdf_type: str, db: AsyncSession = Depends(get_db)):
    report = await get_report_or_404(db, report_id)

    if pdf_type == "sacs":
        path = report.sacs_pdf_path
    elif pdf_type == "tcc":
        path = report.tcc_pdf_path
    else:
        raise HTTPException(status_code=404, detail="Invalid PDF type")

    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        path=path,
        filename=os.path.basename(path),
        media_type="application/pdf",
    )
