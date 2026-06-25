from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Client,
    Liability,
    NonRetirementAccount,
    RetirementAccount,
    Trust,
)


def _parse_float(value: object) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


async def get_client_or_404(db: AsyncSession, client_id: int) -> Client:
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


async def list_clients(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Client).order_by(Client.last_name, Client.first_name))
    clients = result.scalars().all()
    return [c.to_dict() for c in clients]


async def create_client(db: AsyncSession, data: dict) -> Client:
    client = Client(
        first_name=data.get("first_name", "").strip(),
        last_name=data.get("last_name", "").strip(),
        spouse_first_name=((data.get("spouse_first_name") or "").strip() or None),
        spouse_last_name=((data.get("spouse_last_name") or "").strip() or None),
        dob=data.get("dob") if isinstance(data.get("dob"), date) else date.fromisoformat(data.get("dob", "")),
        spouse_dob=data.get("spouse_dob") if isinstance(data.get("spouse_dob"), date) else (None if not data.get("spouse_dob") else date.fromisoformat(data["spouse_dob"])),
        ssn_last4=data.get("ssn_last4", "").strip(),
        spouse_ssn_last4=((data.get("spouse_ssn_last4") or "").strip() or None),
        monthly_salary=_parse_float(data.get("monthly_salary")),
        monthly_expenses=_parse_float(data.get("monthly_expenses")),
        private_reserve_target=_parse_float(data.get("private_reserve_target")) or None,
    )
    db.add(client)
    await db.flush()

    for a in data.get("retirement_accounts", []):
        db.add(RetirementAccount(
            client_id=client.id,
            owner=a.get("owner", "client1"),
            account_type=a.get("account_type", "").strip(),
            balance=_parse_float(a.get("balance")),
            cash_balance=_parse_float(a.get("cash_balance")),
            last4=a.get("last4", "").strip(),
        ))
    for a in data.get("non_retirement_accounts", []):
        db.add(NonRetirementAccount(
            client_id=client.id,
            account_type=a.get("account_type", "").strip(),
            balance=_parse_float(a.get("balance")),
            cash_balance=_parse_float(a.get("cash_balance")),
            last4=a.get("last4", "").strip(),
        ))
    for t in data.get("trusts", []):
        db.add(Trust(
            client_id=client.id,
            property_address=t.get("property_address", "").strip(),
            zillow_value=_parse_float(t.get("zillow_value")),
        ))
    for l in data.get("liabilities", []):
        db.add(Liability(
            client_id=client.id,
            liability_type=l.get("liability_type", "").strip(),
            balance=_parse_float(l.get("balance")),
            interest_rate=l.get("interest_rate") if l.get("interest_rate") is not None else None,
        ))

    await db.flush()
    await db.refresh(client)
    return client


async def update_client(db: AsyncSession, client: Client, data: dict) -> Client:
    if "first_name" in data:
        client.first_name = data["first_name"].strip()
    if "last_name" in data:
        client.last_name = data["last_name"].strip()
    if "spouse_first_name" in data:
        client.spouse_first_name = (data["spouse_first_name"] or "").strip() or None
    if "spouse_last_name" in data:
        client.spouse_last_name = (data["spouse_last_name"] or "").strip() or None
    if "dob" in data:
        client.dob = data["dob"] if isinstance(data["dob"], date) else date.fromisoformat(data["dob"])
    if "spouse_dob" in data:
        client.spouse_dob = None if not data["spouse_dob"] else (data["spouse_dob"] if isinstance(data["spouse_dob"], date) else date.fromisoformat(data["spouse_dob"]))
    if "ssn_last4" in data:
        client.ssn_last4 = data["ssn_last4"].strip()
    if "spouse_ssn_last4" in data:
        client.spouse_ssn_last4 = (data["spouse_ssn_last4"] or "").strip() or None
    if "monthly_salary" in data:
        client.monthly_salary = _parse_float(data["monthly_salary"])
    if "monthly_expenses" in data:
        client.monthly_expenses = _parse_float(data["monthly_expenses"])
    if "private_reserve_target" in data:
        client.private_reserve_target = _parse_float(data.get("private_reserve_target")) or None

    if "retirement_accounts" in data:
        client.retirement_accounts.clear()
        for a in data["retirement_accounts"]:
            client.retirement_accounts.append(RetirementAccount(
                client_id=client.id,
                owner=a.get("owner", "client1"),
                account_type=a.get("account_type", "").strip(),
                balance=_parse_float(a.get("balance")),
                cash_balance=_parse_float(a.get("cash_balance")),
                last4=a.get("last4", "").strip(),
            ))
    if "non_retirement_accounts" in data:
        client.non_retirement_accounts.clear()
        for a in data["non_retirement_accounts"]:
            client.non_retirement_accounts.append(NonRetirementAccount(
                client_id=client.id,
                account_type=a.get("account_type", "").strip(),
                balance=_parse_float(a.get("balance")),
                cash_balance=_parse_float(a.get("cash_balance")),
                last4=a.get("last4", "").strip(),
            ))
    if "trusts" in data:
        client.trusts.clear()
        for t in data["trusts"]:
            client.trusts.append(Trust(
                client_id=client.id,
                property_address=t.get("property_address", "").strip(),
                zillow_value=_parse_float(t.get("zillow_value")),
            ))
    if "liabilities" in data:
        client.liabilities.clear()
        for l in data["liabilities"]:
            client.liabilities.append(Liability(
                client_id=client.id,
                liability_type=l.get("liability_type", "").strip(),
                balance=_parse_float(l.get("balance")),
                interest_rate=l.get("interest_rate") if l.get("interest_rate") is not None else None,
            ))

    await db.flush()
    await db.refresh(client)
    return client


async def delete_client(db: AsyncSession, client: Client) -> None:
    await db.delete(client)
    await db.flush()
