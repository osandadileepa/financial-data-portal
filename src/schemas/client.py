from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ── Nested account schemas ────────────────────────────────────────────────


class RetirementAccountCreate(BaseModel):
    owner: str = "client1"
    account_type: str
    last4: str = Field(..., pattern=r"^\d{1,4}$")
    balance: float = Field(default=0.0, ge=0)
    cash_balance: float = Field(default=0.0, ge=0)


class RetirementAccountResponse(BaseModel):
    id: int
    client_id: int
    owner: str
    account_type: str
    balance: float
    cash_balance: float
    last4: str

    model_config = {"from_attributes": True}


class NonRetirementAccountCreate(BaseModel):
    account_type: str
    last4: str = Field(..., pattern=r"^\d{1,4}$")
    balance: float = Field(default=0.0, ge=0)
    cash_balance: float = Field(default=0.0, ge=0)


class NonRetirementAccountResponse(BaseModel):
    id: int
    client_id: int
    account_type: str
    balance: float
    cash_balance: float
    last4: str

    model_config = {"from_attributes": True}


class TrustCreate(BaseModel):
    property_address: str
    zillow_value: Optional[float] = None


class TrustResponse(BaseModel):
    id: int
    client_id: int
    property_address: str
    zillow_value: Optional[float] = None

    model_config = {"from_attributes": True}


class LiabilityCreate(BaseModel):
    liability_type: str
    balance: float = Field(default=0.0, ge=0)
    interest_rate: Optional[float] = None


class LiabilityResponse(BaseModel):
    id: int
    client_id: int
    liability_type: str
    balance: float
    interest_rate: Optional[float] = None

    model_config = {"from_attributes": True}


# ── Client schemas ────────────────────────────────────────────────────────


class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    spouse_first_name: Optional[str] = None
    spouse_last_name: Optional[str] = None
    dob: date
    spouse_dob: Optional[date] = None
    ssn_last4: str = Field(..., pattern=r"^\d{1,4}$")
    spouse_ssn_last4: Optional[str] = Field(None, pattern=r"^\d{1,4}$")
    monthly_salary: float = Field(..., ge=0)
    monthly_expenses: float = Field(..., ge=0)
    private_reserve_target: Optional[float] = Field(None, ge=0)
    retirement_accounts: list[RetirementAccountCreate] = Field(..., min_length=1, max_length=6)
    non_retirement_accounts: list[NonRetirementAccountCreate] = Field(..., min_length=1, max_length=6)
    trusts: list[TrustCreate] = Field(default_factory=list)
    liabilities: list[LiabilityCreate] = Field(default_factory=list)


class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    spouse_first_name: Optional[str] = None
    spouse_last_name: Optional[str] = None
    dob: Optional[date] = None
    spouse_dob: Optional[date] = None
    ssn_last4: Optional[str] = Field(None, pattern=r"^\d{1,4}$")
    spouse_ssn_last4: Optional[str] = Field(None, pattern=r"^\d{1,4}$")
    monthly_salary: Optional[float] = Field(None, ge=0)
    monthly_expenses: Optional[float] = Field(None, ge=0)
    private_reserve_target: Optional[float] = Field(None, ge=0)
    retirement_accounts: Optional[list[RetirementAccountCreate]] = Field(None, min_length=1, max_length=6)
    non_retirement_accounts: Optional[list[NonRetirementAccountCreate]] = Field(None, min_length=1, max_length=6)
    trusts: Optional[list[TrustCreate]] = None
    liabilities: Optional[list[LiabilityCreate]] = None


class ClientResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    spouse_first_name: Optional[str] = None
    spouse_last_name: Optional[str] = None
    dob: Optional[str] = None
    spouse_dob: Optional[str] = None
    ssn_last4: str
    spouse_ssn_last4: Optional[str] = None
    full_name: str
    age: Optional[int] = None
    spouse_age: Optional[int] = None
    monthly_salary: float
    monthly_expenses: float
    private_reserve_target: Optional[float] = None
    computed_private_reserve_target: float = 0.0
    last_report_date: Optional[str] = None
    retirement_accounts: list[RetirementAccountResponse] = []
    non_retirement_accounts: list[NonRetirementAccountResponse] = []
    trusts: list[TrustResponse] = []
    liabilities: list[LiabilityResponse] = []
    quarterly_reports: list[dict] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}
