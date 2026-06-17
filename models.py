from datetime import datetime, date
from database import db


class Client(db.Model):
    """
    Core client profile.

    Stores the client (and optional spouse) personal information, monthly cash
    flow numbers, and the private reserve target.  Related accounts, trusts,
    liabilities, and reports are linked through one-to-many relationships.
    """
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    spouse_first_name = db.Column(db.String(100), nullable=True)
    spouse_last_name = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.Date, nullable=False)
    spouse_dob = db.Column(db.Date, nullable=True)
    ssn_last4 = db.Column(db.String(4), nullable=False)
    spouse_ssn_last4 = db.Column(db.String(4), nullable=True)
    monthly_salary = db.Column(db.Float, nullable=False, default=0.0)
    monthly_expenses = db.Column(db.Float, nullable=False, default=0.0)
    private_reserve_target = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Related records - cascade delete keeps the profile clean when a client is removed
    retirement_accounts = db.relationship(
        "RetirementAccount", backref="client", lazy=True, cascade="all, delete-orphan"
    )
    non_retirement_accounts = db.relationship(
        "NonRetirementAccount", backref="client", lazy=True, cascade="all, delete-orphan"
    )
    trusts = db.relationship(
        "Trust", backref="client", lazy=True, cascade="all, delete-orphan"
    )
    liabilities = db.relationship(
        "Liability", backref="client", lazy=True, cascade="all, delete-orphan"
    )
    quarterly_reports = db.relationship(
        "QuarterlyReport", backref="client", lazy=True, cascade="all, delete-orphan"
    )

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def age(self, as_of: date = None):
        """Calculate the client's age from their date of birth."""
        if self.dob is None:
            return None
        as_of = as_of or date.today()
        return as_of.year - self.dob.year - ((as_of.month, as_of.day) < (self.dob.month, self.dob.day))

    def spouse_age(self, as_of: date = None):
        """Calculate the spouse's age from their date of birth."""
        if self.spouse_dob is None:
            return None
        as_of = as_of or date.today()
        return as_of.year - self.spouse_dob.year - ((as_of.month, as_of.day) < (self.spouse_dob.month, self.spouse_dob.day))

    def computed_private_reserve_target(self):
        """
        Private Reserve Target = (6 * monthly expenses) + sum of insurance deductibles.
        In V1 there are no separate insurance deductibles, so the deductible sum is 0.
        """
        return (self.monthly_expenses * 6) + 0.0

    def to_dict(self):
        """Serialize the client profile for the frontend."""
        last_report = (
            QuarterlyReport.query.filter_by(client_id=self.id)
            .order_by(QuarterlyReport.generated_at.desc())
            .first()
        )
        last_report_date = None
        if last_report:
            last_report_date = last_report.generated_at.strftime("%Y-%m-%d")

        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name(),
            "spouse_first_name": self.spouse_first_name,
            "spouse_last_name": self.spouse_last_name,
            "dob": self.dob.isoformat() if self.dob else None,
            "age": self.age(),
            "spouse_dob": self.spouse_dob.isoformat() if self.spouse_dob else None,
            "spouse_age": self.spouse_age(),
            "ssn_last4": self.ssn_last4,
            "spouse_ssn_last4": self.spouse_ssn_last4,
            "monthly_salary": self.monthly_salary,
            "monthly_expenses": self.monthly_expenses,
            "private_reserve_target": self.private_reserve_target or self.computed_private_reserve_target(),
            "computed_private_reserve_target": self.computed_private_reserve_target(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_report_date": last_report_date,
        }


class RetirementAccount(db.Model):
    """Tax-advantaged retirement account owned by client1 or client2."""
    __tablename__ = "retirement_accounts"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    owner = db.Column(db.String(50), nullable=False)  # "client1" or "client2"
    account_type = db.Column(db.String(50), nullable=False)  # IRA, Roth IRA, 401K, Pension
    balance = db.Column(db.Float, nullable=False, default=0.0)
    cash_balance = db.Column(db.Float, nullable=False, default=0.0)
    last4 = db.Column(db.String(4), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "owner": self.owner,
            "account_type": self.account_type,
            "balance": self.balance,
            "cash_balance": self.cash_balance,
            "last4": self.last4,
        }


class NonRetirementAccount(db.Model):
    """Taxable brokerage or joint account.  Trusts are tracked separately."""
    __tablename__ = "non_retirement_accounts"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # brokerage, joint
    balance = db.Column(db.Float, nullable=False, default=0.0)
    cash_balance = db.Column(db.Float, nullable=False, default=0.0)
    last4 = db.Column(db.String(4), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "account_type": self.account_type,
            "balance": self.balance,
            "cash_balance": self.cash_balance,
            "last4": self.last4,
        }


class Trust(db.Model):
    """Real estate held in trust.  Kept separate from non-retirement totals."""
    __tablename__ = "trusts"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    property_address = db.Column(db.Text, nullable=False)
    zillow_value = db.Column(db.Float, nullable=False, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "property_address": self.property_address,
            "zillow_value": self.zillow_value,
        }


class Liability(db.Model):
    """Mortgage or auto loan.  Displayed separately, never subtracted from net worth."""
    __tablename__ = "liabilities"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    liability_type = db.Column(db.String(50), nullable=False)  # mortgage, auto_loan
    balance = db.Column(db.Float, nullable=False, default=0.0)
    interest_rate = db.Column(db.Float, nullable=False, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "liability_type": self.liability_type,
            "balance": self.balance,
            "interest_rate": self.interest_rate,
        }


class QuarterlyReport(db.Model):
    """Header record for a generated quarterly report."""
    __tablename__ = "quarterly_reports"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    quarter = db.Column(db.String(10), nullable=False)  # e.g. "Q1"
    year = db.Column(db.Integer, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    sacs_pdf_path = db.Column(db.String(255), nullable=True)
    tcc_pdf_path = db.Column(db.String(255), nullable=True)

    data_points = db.relationship(
        "QuarterlyData", backref="report", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "quarter": self.quarter,
            "year": self.year,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "sacs_pdf_path": self.sacs_pdf_path,
            "tcc_pdf_path": self.tcc_pdf_path,
        }


class QuarterlyData(db.Model):
    """
    Key/value storage for per-report balances.

    This lets the report capture a snapshot of balances at generation time,
    independent of the live account balances that may change later.
    """
    __tablename__ = "quarterly_data"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey("quarterly_reports.id"), nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_value = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "field_name": self.field_name,
            "field_value": self.field_value,
        }
