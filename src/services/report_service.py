from __future__ import annotations

import os
from datetime import datetime, date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from werkzeug.utils import secure_filename

from src.config import get_pdf_output_dir
from src.models import (
    Client,
    Liability,
    NonRetirementAccount,
    RetirementAccount,
    Trust,
    QuarterlyReport,
    QuarterlyData,
)
from pdf_generator import generate_sacs_pdf, generate_tcc_pdf


def _parse_float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


async def get_report_or_404(db: AsyncSession, report_id: int) -> QuarterlyReport:
    result = await db.execute(select(QuarterlyReport).where(QuarterlyReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


async def get_report_data(db: AsyncSession, client: Client) -> dict:
    """Return static data + last known values for the report form."""
    # Find the most recent report
    result = await db.execute(
        select(QuarterlyReport)
        .where(QuarterlyReport.client_id == client.id)
        .order_by(QuarterlyReport.generated_at.desc())
        .limit(1)
    )
    last_report: Optional[QuarterlyReport] = result.scalar_one_or_none()

    last_values = {}
    if last_report:
        await db.refresh(last_report, ["data_points"])
        for dp in last_report.data_points:
            last_values[dp.field_name] = dp.field_value

    return {
        "client": client.to_dict(),
        "inflow": client.monthly_salary,
        "outflow": client.monthly_expenses,
        "private_reserve_target": client.private_reserve_target or client.computed_private_reserve_target,
        "retirement_accounts": [a.to_dict() for a in client.retirement_accounts],
        "non_retirement_accounts": [a.to_dict() for a in client.non_retirement_accounts],
        "trusts": [t.to_dict() for t in client.trusts],
        "liabilities": [l.to_dict() for l in client.liabilities],
        "last_values": last_values,
    }


def _build_calculation_context(client: Client, balances: dict) -> dict:
    """Build SACS and TCC calculation values from entered balances.

    Returns a dict that both the API response and the PDF generators consume.
    """
    inflow = _parse_float(client.monthly_salary)
    outflow = _parse_float(client.monthly_expenses)
    excess = inflow - outflow
    private_reserve_target = client.private_reserve_target or client.computed_private_reserve_target

    retirement_accounts = [a.to_dict() for a in client.retirement_accounts]
    non_retirement_accounts = [a.to_dict() for a in client.non_retirement_accounts]
    trusts = [t.to_dict() for t in client.trusts]
    liabilities_list = [l.to_dict() for l in client.liabilities]

    client1_retirement = 0.0
    client2_retirement = 0.0
    for account in retirement_accounts:
        balance = _parse_float(balances.get(f"retirement_{account['id']}"))
        account["current_balance"] = balance
        if account["owner"] == "client2":
            client2_retirement += balance
        else:
            client1_retirement += balance

    non_retirement_total = 0.0
    for account in non_retirement_accounts:
        balance = _parse_float(balances.get(f"non_retirement_{account['id']}"))
        account["current_balance"] = balance
        non_retirement_total += balance

    trust_total = 0.0
    for trust in trusts:
        trust["current_value"] = _parse_float(balances.get(f"trust_zillow_{trust['id']}"))
        trust_total += trust["current_value"]

    liabilities_total = 0.0
    for liability in liabilities_list:
        liability["current_balance"] = _parse_float(balances.get(f"liability_{liability['id']}"))
        liabilities_total += liability["current_balance"]

    grand_total = client1_retirement + client2_retirement + non_retirement_total + trust_total

    return {
        "inflow": inflow,
        "outflow": outflow,
        "excess": excess,
        "private_reserve_target": private_reserve_target,
        "private_reserve_balance": _parse_float(balances.get("private_reserve_balance", 0)),
        "client1_retirement_total": client1_retirement,
        "client2_retirement_total": client2_retirement,
        "non_retirement_total": non_retirement_total,
        "trust_total": trust_total,
        "grand_total": grand_total,
        "liabilities_total": liabilities_total,
        "retirement_accounts": retirement_accounts,
        "non_retirement_accounts": non_retirement_accounts,
        "trusts": trusts,
        "liabilities": liabilities_list,
    }


async def generate_report(
    db: AsyncSession,
    client: Client,
    quarter: str,
    year: int,
    balances: dict[str, str],
) -> dict:
    """Create a QuarterlyReport, persist balance snapshots, generate PDFs."""

    # Validate all required fields are present
    missing = []
    for account_data in client.retirement_accounts:
        key = f"retirement_{account_data.id}"
        if key not in balances or balances[key] == "":
            missing.append(f"Retirement {account_data.account_type} ending in {account_data.last4}")
    for account_data in client.non_retirement_accounts:
        key = f"non_retirement_{account_data.id}"
        if key not in balances or balances[key] == "":
            missing.append(f"Non-Retirement {account_data.account_type} ending in {account_data.last4}")
    for liability_data in client.liabilities:
        key = f"liability_{liability_data.id}"
        if key not in balances or balances[key] == "":
            missing.append(f"Liability {liability_data.liability_type}")
    for trust in client.trusts:
        key = f"trust_zillow_{trust.id}"
        if key not in balances or balances[key] == "":
            missing.append(f"Trust value for {trust.property_address}")
    if "private_reserve_balance" not in balances or balances["private_reserve_balance"] == "":
        missing.append("Private Reserve balance")

    if missing:
        raise HTTPException(
            status_code=400,
            detail={"error": "Missing required balance fields", "fields": missing},
        )

    # Create report record
    report = QuarterlyReport(
        client_id=client.id,
        quarter=quarter,
        year=year,
        generated_at=datetime.utcnow(),
    )
    db.add(report)
    await db.flush()

    # Persist balance snapshots
    for name, value in balances.items():
        db.add(QuarterlyData(
            report_id=report.id,
            field_name=name,
            field_value=str(value),
        ))

    # Build calculation context
    calc_context = _build_calculation_context(client, balances)

    # Write PDFs
    pdf_dir = get_pdf_output_dir()
    os.makedirs(pdf_dir, exist_ok=True)

    safe_name = secure_filename(f"{client.last_name}_{client.first_name}")
    sacs_filename = f"SACS_{safe_name}_{quarter}_{year}_{report.id}.pdf"
    tcc_filename = f"TCC_{safe_name}_{quarter}_{year}_{report.id}.pdf"
    sacs_path = os.path.join(pdf_dir, sacs_filename)
    tcc_path = os.path.join(pdf_dir, tcc_filename)

    generate_sacs_pdf(sacs_path, client, calc_context)
    generate_tcc_pdf(tcc_path, client, calc_context)

    report.sacs_pdf_path = sacs_path
    report.tcc_pdf_path = tcc_path
    await db.flush()

    return {
        "report": report.to_dict(),
        "calculations": calc_context,
        "download_urls": {
            "sacs": f"/api/reports/{report.id}/download/sacs",
            "tcc": f"/api/reports/{report.id}/download/tcc",
        },
    }
