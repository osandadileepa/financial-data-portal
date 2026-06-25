from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    spouse_first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    spouse_last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dob: Mapped[date_type] = mapped_column(nullable=False)
    spouse_dob: Mapped[Optional[date_type]] = mapped_column(nullable=True)
    ssn_last4: Mapped[str] = mapped_column(String(4), nullable=False)
    spouse_ssn_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    monthly_salary: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    monthly_expenses: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    private_reserve_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    retirement_accounts: Mapped[list["RetirementAccount"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", lazy="selectin"
    )
    non_retirement_accounts: Mapped[list["NonRetirementAccount"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", lazy="selectin"
    )
    trusts: Mapped[list["Trust"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", lazy="selectin"
    )
    liabilities: Mapped[list["Liability"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", lazy="selectin"
    )
    quarterly_reports: Mapped[list["QuarterlyReport"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", lazy="selectin"
    )

    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def computed_private_reserve_target(self) -> float:
        if self.private_reserve_target:
            return self.private_reserve_target
        return 6 * (self.monthly_expenses or 0)

    @property
    def age(self) -> Optional[int]:
        if not self.dob:
            return None
        today = date_type.today()
        return (
            today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        )

    @property
    def spouse_age(self) -> Optional[int]:
        if not self.spouse_dob:
            return None
        today = date_type.today()
        return (
            today.year
            - self.spouse_dob.year
            - ((today.month, today.day) < (self.spouse_dob.month, self.spouse_dob.day))
        )

    @property
    def last_report_date(self) -> Optional[str]:
        if not self.quarterly_reports:
            return None
        latest = max(self.quarterly_reports, key=lambda r: r.generated_at or datetime.min)
        return latest.generated_at.isoformat() if latest.generated_at else None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "spouse_first_name": self.spouse_first_name,
            "spouse_last_name": self.spouse_last_name,
            "dob": str(self.dob) if self.dob else None,
            "spouse_dob": str(self.spouse_dob) if self.spouse_dob else None,
            "ssn_last4": self.ssn_last4,
            "spouse_ssn_last4": self.spouse_ssn_last4,
            "full_name": self.full_name(),
            "age": self.age,
            "spouse_age": self.spouse_age,
            "monthly_salary": self.monthly_salary,
            "monthly_expenses": self.monthly_expenses,
            "private_reserve_target": self.private_reserve_target,
            "computed_private_reserve_target": self.computed_private_reserve_target,
            "last_report_date": self.last_report_date,
            "retirement_accounts": [a.to_dict() for a in self.retirement_accounts],
            "non_retirement_accounts": [a.to_dict() for a in self.non_retirement_accounts],
            "trusts": [t.to_dict() for t in self.trusts],
            "liabilities": [l.to_dict() for l in self.liabilities],
            "quarterly_reports": [r.to_dict() for r in self.quarterly_reports],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RetirementAccount(Base):
    __tablename__ = "retirement_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    owner: Mapped[str] = mapped_column(String(50), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cash_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last4: Mapped[str] = mapped_column(String(4), nullable=False)

    client: Mapped["Client"] = relationship(back_populates="retirement_accounts")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "owner": self.owner,
            "account_type": self.account_type,
            "balance": self.balance,
            "cash_balance": self.cash_balance,
            "last4": self.last4,
        }


class NonRetirementAccount(Base):
    __tablename__ = "non_retirement_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cash_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last4: Mapped[str] = mapped_column(String(4), nullable=False)

    client: Mapped["Client"] = relationship(back_populates="non_retirement_accounts")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "account_type": self.account_type,
            "balance": self.balance,
            "cash_balance": self.cash_balance,
            "last4": self.last4,
        }


class Trust(Base):
    __tablename__ = "trusts"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    property_address: Mapped[str] = mapped_column(String(255), nullable=False)
    zillow_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    client: Mapped["Client"] = relationship(back_populates="trusts")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "property_address": self.property_address,
            "zillow_value": self.zillow_value,
        }


class Liability(Base):
    __tablename__ = "liabilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    liability_type: Mapped[str] = mapped_column(String(50), nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    interest_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    client: Mapped["Client"] = relationship(back_populates="liabilities")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "liability_type": self.liability_type,
            "balance": self.balance,
            "interest_rate": self.interest_rate,
        }


class QuarterlyReport(Base):
    __tablename__ = "quarterly_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    quarter: Mapped[str] = mapped_column(String(10), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    generated_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.utcnow)
    sacs_pdf_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tcc_pdf_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    client: Mapped["Client"] = relationship(back_populates="quarterly_reports")
    data_points: Mapped[list["QuarterlyData"]] = relationship(
        back_populates="report", cascade="all, delete-orphan", lazy="selectin"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "quarter": self.quarter,
            "year": self.year,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "sacs_pdf_path": self.sacs_pdf_path,
            "tcc_pdf_path": self.tcc_pdf_path,
        }


class QuarterlyData(Base):
    __tablename__ = "quarterly_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("quarterly_reports.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    field_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    report: Mapped["QuarterlyReport"] = relationship(back_populates="data_points")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "report_id": self.report_id,
            "field_name": self.field_name,
            "field_value": self.field_value,
        }
