from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ReportDataResponse(BaseModel):
    """Payload for the report data endpoint (pre-fill report form)."""

    client: dict
    inflow: float
    outflow: float
    private_reserve_target: float
    retirement_accounts: list[dict]
    non_retirement_accounts: list[dict]
    trusts: list[dict]
    liabilities: list[dict]
    last_values: dict


class BalanceField(BaseModel):
    """Key-value pair for a single balance field in a report."""

    field_name: str
    field_value: str


class ReportGenerateRequest(BaseModel):
    """Request body for generating a quarterly report."""

    quarter: str = Field(..., pattern=r"^Q[1-4]$")
    year: int = Field(..., ge=2020, le=2100)
    balances: dict[str, str]


class CalculationContext(BaseModel):
    """All calculated values returned after report generation."""

    inflow: float
    outflow: float
    excess: float
    private_reserve_target: float
    private_reserve_balance: float
    client1_retirement_total: float
    client2_retirement_total: float
    non_retirement_total: float
    trust_total: float
    grand_total: float
    liabilities_total: float
    retirement_accounts: list[dict]
    non_retirement_accounts: list[dict]
    trusts: list[dict]
    liabilities: list[dict]


class ReportGenerateResponse(BaseModel):
    """Response after successful report generation."""

    report: dict
    calculations: dict
    download_urls: dict[str, str]
