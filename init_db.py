import os
from datetime import date, datetime
from dotenv import load_dotenv

from app import app, db
from models import (
    Client,
    RetirementAccount,
    NonRetirementAccount,
    Trust,
    Liability,
    QuarterlyReport,
    QuarterlyData,
)

# Load local environment variables if present
load_dotenv()


def create_sample_data():
    """
    Seed the database with two sample clients who have complete financial
    profiles.  This lets you test the full dashboard, report form, and PDF
    generation immediately after running the app.
    """
    with app.app_context():
        # Create all tables fresh
        db.create_all()

        # Clear existing sample data (useful during re-runs)
        QuarterlyData.query.delete()
        QuarterlyReport.query.delete()
        RetirementAccount.query.delete()
        NonRetirementAccount.query.delete()
        Trust.query.delete()
        Liability.query.delete()
        Client.query.delete()
        db.session.commit()

        # ------------------------------------------------------------------
        # Sample Client 1: James & Margaret Anderson
        # ------------------------------------------------------------------
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
        db.session.add(client1)
        db.session.flush()

        # Retirement accounts
        db.session.add_all([
            RetirementAccount(client_id=client1.id, owner="client1", account_type="401K", balance=875000.00, cash_balance=25000.00, last4="2147"),
            RetirementAccount(client_id=client1.id, owner="client1", account_type="IRA", balance=320000.00, cash_balance=5000.00, last4="8832"),
            RetirementAccount(client_id=client1.id, owner="client2", account_type="Roth IRA", balance=245000.00, cash_balance=3000.00, last4="5519"),
        ])

        # Non-retirement accounts
        db.session.add_all([
            NonRetirementAccount(client_id=client1.id, account_type="brokerage", balance=450000.00, cash_balance=30000.00, last4="7733"),
            NonRetirementAccount(client_id=client1.id, account_type="joint", balance=125000.00, cash_balance=10000.00, last4="9912"),
        ])

        # Trust
        db.session.add(
            Trust(client_id=client1.id, property_address="742 Evergreen Terrace, Springfield, IL", zillow_value=1200000.00)
        )

        # Liabilities
        db.session.add_all([
            Liability(client_id=client1.id, liability_type="mortgage", balance=285000.00, interest_rate=3.25),
            Liability(client_id=client1.id, liability_type="auto_loan", balance=18000.00, interest_rate=4.90),
        ])

        # A prior quarterly report for demonstration
        report1 = QuarterlyReport(
            client_id=client1.id,
            quarter="Q1",
            year=2026,
            generated_at=datetime(2026, 1, 15, 10, 0, 0),
        )
        db.session.add(report1)
        db.session.flush()

        db.session.add_all([
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

        # ------------------------------------------------------------------
        # Sample Client 2: Robert Chen (single, no spouse)
        # ------------------------------------------------------------------
        client2 = Client(
            first_name="Robert",
            last_name="Chen",
            spouse_first_name=None,
            spouse_last_name=None,
            dob=date(1958, 11, 8),
            spouse_dob=None,
            ssn_last4="6204",
            spouse_ssn_last4=None,
            monthly_salary=12000.00,
            monthly_expenses=6800.00,
            private_reserve_target=40800.00,
        )
        db.session.add(client2)
        db.session.flush()

        db.session.add_all([
            RetirementAccount(client_id=client2.id, owner="client1", account_type="401K", balance=1200000.00, cash_balance=40000.00, last4="4455"),
            RetirementAccount(client_id=client2.id, owner="client1", account_type="IRA", balance=380000.00, cash_balance=8000.00, last4="2288"),
        ])

        db.session.add_all([
            NonRetirementAccount(client_id=client2.id, account_type="brokerage", balance=275000.00, cash_balance=15000.00, last4="6677"),
        ])

        db.session.add(
            Trust(client_id=client2.id, property_address="450 Park Avenue, New York, NY", zillow_value=2800000.00)
        )

        db.session.add(
            Liability(client_id=client2.id, liability_type="mortgage", balance=950000.00, interest_rate=2.75)
        )

        db.session.commit()
        print("Database initialized with sample data.")
        print(f"  Client 1: {client1.full_name()} (ID: {client1.id})")
        print(f"  Client 2: {client2.full_name()} (ID: {client2.id})")


if __name__ == "__main__":
    create_sample_data()
