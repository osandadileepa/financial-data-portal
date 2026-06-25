"""Database seeding — called on app startup and usable as a standalone script."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime

from sqlalchemy import select

from src.database import Base, async_session, engine
from src.models import (
    Client,
    Liability,
    NonRetirementAccount,
    QuarterlyData,
    QuarterlyReport,
    RetirementAccount,
    Trust,
)

logger = logging.getLogger(__name__)


async def seed_database() -> None:
    """Create tables and seed sample data if the clients table is empty."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        result = await db.execute(select(Client).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        # Sample Client 1: James & Margaret Anderson
        client1 = Client(
            first_name="James",
            last_name="Anderson",
            spouse_first_name="Margaret",
            spouse_last_name="Anderson",
            dob=date(1962, 3, 15),
            spouse_dob=date(1965, 7, 22),
            ssn_last4="4821",
            spouse_ssn_last4="7392",
            monthly_salary=18500.00,
            monthly_expenses=11200.00,
            private_reserve_target=67200.00,
        )
        db.add(client1)
        await db.flush()

        db.add_all([
            RetirementAccount(client_id=client1.id, owner="client1", account_type="401K", balance=875000.00, cash_balance=25000.00, last4="2147"),
            RetirementAccount(client_id=client1.id, owner="client1", account_type="IRA", balance=320000.00, cash_balance=5000.00, last4="8832"),
            RetirementAccount(client_id=client1.id, owner="client2", account_type="Roth IRA", balance=245000.00, cash_balance=3000.00, last4="5519"),
        ])
        db.add_all([
            NonRetirementAccount(client_id=client1.id, account_type="brokerage", balance=450000.00, cash_balance=30000.00, last4="7733"),
            NonRetirementAccount(client_id=client1.id, account_type="joint", balance=125000.00, cash_balance=10000.00, last4="9912"),
        ])
        db.add(Trust(client_id=client1.id, property_address="742 Evergreen Terrace, Springfield, IL", zillow_value=1200000.00))
        db.add_all([
            Liability(client_id=client1.id, liability_type="mortgage", balance=285000.00, interest_rate=3.25),
            Liability(client_id=client1.id, liability_type="auto_loan", balance=18000.00, interest_rate=4.90),
        ])

        report1 = QuarterlyReport(client_id=client1.id, quarter="Q1", year=2026, generated_at=datetime(2026, 1, 15, 10, 0, 0))
        db.add(report1)
        await db.flush()

        db.add_all([
            QuarterlyData(report_id=report1.id, field_name="private_reserve_balance", field_value="58000.00"),
            QuarterlyData(report_id=report1.id, field_name="retirement_1", field_value="860000.00"),
            QuarterlyData(report_id=report1.id, field_name="retirement_2", field_value="315000.00"),
            QuarterlyData(report_id=report1.id, field_name="retirement_3", field_value="240000.00"),
            QuarterlyData(report_id=report1.id, field_name="non_retirement_1", field_value="440000.00"),
            QuarterlyData(report_id=report1.id, field_name="non_retirement_2", field_value="120000.00"),
            QuarterlyData(report_id=report1.id, field_name="trust_zillow_1", field_value="1180000.00"),
            QuarterlyData(report_id=report1.id, field_name="liability_1", field_value="290000.00"),
            QuarterlyData(report_id=report1.id, field_name="liability_2", field_value="22000.00"),
        ])

        # Sample Client 2: Robert Chen
        client2 = Client(
            first_name="Robert",
            last_name="Chen",
            dob=date(1958, 11, 8),
            ssn_last4="6204",
            monthly_salary=12000.00,
            monthly_expenses=6800.00,
            private_reserve_target=40800.00,
        )
        db.add(client2)
        await db.flush()

        db.add_all([
            RetirementAccount(client_id=client2.id, owner="client1", account_type="401K", balance=1200000.00, cash_balance=40000.00, last4="4455"),
            RetirementAccount(client_id=client2.id, owner="client1", account_type="IRA", balance=380000.00, cash_balance=8000.00, last4="2288"),
        ])
        db.add_all([
            NonRetirementAccount(client_id=client2.id, account_type="brokerage", balance=275000.00, cash_balance=15000.00, last4="6677"),
        ])
        db.add(Trust(client_id=client2.id, property_address="450 Park Avenue, New York, NY", zillow_value=2800000.00))
        db.add(Liability(client_id=client2.id, liability_type="mortgage", balance=950000.00, interest_rate=2.75))

        await db.commit()
        logger.info("Database seeded with sample data.")


async def reset_database() -> None:
    """Drop all tables and re-seed (for development use)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await seed_database()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_database())
