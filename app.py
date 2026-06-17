import os
import io
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template, send_file, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from database import db, get_database_path
from models import (
    Client,
    RetirementAccount,
    NonRetirementAccount,
    Trust,
    Liability,
    QuarterlyReport,
    QuarterlyData,
)
from pdf_generator import generate_sacs_pdf, generate_tcc_pdf

# Load environment variables from .env when running locally
load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = get_database_path()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

# Initialize SQLAlchemy with the Flask app
db.init_app(app)

# Directory where generated PDFs are stored
PDF_OUTPUT_DIR = os.environ.get("PDF_OUTPUT_DIR", "generated_pdfs")
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def parse_date(value):
    """Convert a YYYY-MM-DD string into a Python date object."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_float(value):
    """Safely parse a string/float into a float, defaulting to 0.0."""
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def get_client_or_404(client_id):
    client = db.session.get(Client, client_id)
    if not client:
        abort(404, description="Client not found")
    return client


def build_client_payload(client):
    """Return a complete client profile dictionary including related records."""
    data = client.to_dict()
    data["retirement_accounts"] = [a.to_dict() for a in client.retirement_accounts]
    data["non_retirement_accounts"] = [a.to_dict() for a in client.non_retirement_accounts]
    data["trusts"] = [t.to_dict() for t in client.trusts]
    data["liabilities"] = [l.to_dict() for l in client.liabilities]
    data["quarterly_reports"] = [r.to_dict() for r in client.quarterly_reports]
    return data


# ---------------------------------------------------------------------------
# Frontend page routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    """Main dashboard listing all clients."""
    return render_template("dashboard.html")


@app.route("/client/new")
def new_client_form():
    """Empty client form for adding a new client."""
    return render_template("client_form.html", client=None)


@app.route("/client/<int:client_id>")
def edit_client_form(client_id):
    """Pre-filled client form for editing an existing client."""
    client = get_client_or_404(client_id)
    return render_template("client_form.html", client=client.to_dict())


@app.route("/client/<int:client_id>/reports")
def client_report_history(client_id):
    """Page showing all generated reports for a client with re-download links."""
    client = get_client_or_404(client_id)
    reports = (
        QuarterlyReport.query.filter_by(client_id=client.id)
        .order_by(QuarterlyReport.generated_at.desc())
        .all()
    )
    return render_template(
        "report_history.html",
        client=client.to_dict(),
        reports=[r.to_dict() for r in reports],
    )


@app.route("/report/<int:client_id>")
def report_form(client_id):
    """Quarterly report data entry page for a client."""
    client = get_client_or_404(client_id)
    return render_template("report_form.html", client=client.to_dict())


# ---------------------------------------------------------------------------
# Client API
# ---------------------------------------------------------------------------

@app.route("/api/clients", methods=["GET"])
def list_clients():
    """Return a list of all clients with their last report date."""
    clients = Client.query.order_by(Client.last_name, Client.first_name).all()
    return jsonify([c.to_dict() for c in clients])


@app.route("/api/clients", methods=["POST"])
def create_client():
    """Create a new client and all related accounts/trusts/liabilities."""
    data = request.get_json() or {}

    # Validate required fields
    required = ["first_name", "last_name", "dob", "ssn_last4", "monthly_salary", "monthly_expenses"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": "Missing required fields", "fields": missing}), 400

    # Build the client profile
    client = Client(
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        spouse_first_name=(data.get("spouse_first_name") or "").strip() or None,
        spouse_last_name=(data.get("spouse_last_name") or "").strip() or None,
        dob=parse_date(data.get("dob")),
        spouse_dob=parse_date(data.get("spouse_dob")),
        ssn_last4=data["ssn_last4"].strip(),
        spouse_ssn_last4=(data.get("spouse_ssn_last4") or "").strip() or None,
        monthly_salary=parse_float(data.get("monthly_salary")),
        monthly_expenses=parse_float(data.get("monthly_expenses")),
        private_reserve_target=parse_float(data.get("private_reserve_target")),
    )
    db.session.add(client)
    db.session.flush()  # Get client.id before committing

    # Retirement accounts (1-6 allowed)
    retirement_accounts = data.get("retirement_accounts", [])
    if not 1 <= len(retirement_accounts) <= 6:
        return jsonify({"error": "Clients must have 1-6 retirement accounts"}), 400
    for account in retirement_accounts:
        if account.get("account_type") and account.get("last4"):
            db.session.add(RetirementAccount(
                client_id=client.id,
                owner=account.get("owner", "client1"),
                account_type=account["account_type"].strip(),
                balance=parse_float(account.get("balance")),
                cash_balance=parse_float(account.get("cash_balance")),
                last4=account["last4"].strip(),
            ))

    # Non-retirement accounts (1-6 allowed)
    non_retirement_accounts = data.get("non_retirement_accounts", [])
    if not 1 <= len(non_retirement_accounts) <= 6:
        return jsonify({"error": "Clients must have 1-6 non-retirement accounts"}), 400
    for account in non_retirement_accounts:
        if account.get("account_type") and account.get("last4"):
            db.session.add(NonRetirementAccount(
                client_id=client.id,
                account_type=account["account_type"].strip(),
                balance=parse_float(account.get("balance")),
                cash_balance=parse_float(account.get("cash_balance")),
                last4=account["last4"].strip(),
            ))

    # Trusts (0-1 supported in V1)
    trusts = data.get("trusts", [])
    if len(trusts) > 1:
        return jsonify({"error": "Clients can have at most 1 trust in V1"}), 400
    for trust in trusts:
        if trust.get("property_address"):
            db.session.add(Trust(
                client_id=client.id,
                property_address=trust["property_address"].strip(),
                zillow_value=parse_float(trust.get("zillow_value")),
            ))

    # Liabilities (0-3 allowed)
    liabilities = data.get("liabilities", [])
    if len(liabilities) > 3:
        return jsonify({"error": "Clients can have at most 3 liabilities"}), 400
    for liability in liabilities:
        if liability.get("liability_type"):
            db.session.add(Liability(
                client_id=client.id,
                liability_type=liability["liability_type"].strip(),
                balance=parse_float(liability.get("balance")),
                interest_rate=parse_float(liability.get("interest_rate")),
            ))

    db.session.commit()
    return jsonify(build_client_payload(client)), 201


@app.route("/api/clients/<int:client_id>", methods=["GET"])
def get_client(client_id):
    """Return a single client profile with all related records."""
    client = get_client_or_404(client_id)
    return jsonify(build_client_payload(client))


@app.route("/api/clients/<int:client_id>", methods=["PUT"])
def update_client(client_id):
    """Update a client profile and replace all related records."""
    client = get_client_or_404(client_id)
    data = request.get_json() or {}

    required = ["first_name", "last_name", "dob", "ssn_last4", "monthly_salary", "monthly_expenses"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": "Missing required fields", "fields": missing}), 400

    # Update client fields
    client.first_name = data["first_name"].strip()
    client.last_name = data["last_name"].strip()
    client.spouse_first_name = (data.get("spouse_first_name") or "").strip() or None
    client.spouse_last_name = (data.get("spouse_last_name") or "").strip() or None
    client.dob = parse_date(data.get("dob"))
    client.spouse_dob = parse_date(data.get("spouse_dob"))
    client.ssn_last4 = data["ssn_last4"].strip()
    client.spouse_ssn_last4 = (data.get("spouse_ssn_last4") or "").strip() or None
    client.monthly_salary = parse_float(data.get("monthly_salary"))
    client.monthly_expenses = parse_float(data.get("monthly_expenses"))
    client.private_reserve_target = parse_float(data.get("private_reserve_target"))

    # Replace related records by deleting then re-adding
    RetirementAccount.query.filter_by(client_id=client.id).delete()
    NonRetirementAccount.query.filter_by(client_id=client.id).delete()
    Trust.query.filter_by(client_id=client.id).delete()
    Liability.query.filter_by(client_id=client.id).delete()

    retirement_accounts = data.get("retirement_accounts", [])
    if not 1 <= len(retirement_accounts) <= 6:
        return jsonify({"error": "Clients must have 1-6 retirement accounts"}), 400
    for account in retirement_accounts:
        if account.get("account_type") and account.get("last4"):
            db.session.add(RetirementAccount(
                client_id=client.id,
                owner=account.get("owner", "client1"),
                account_type=account["account_type"].strip(),
                balance=parse_float(account.get("balance")),
                cash_balance=parse_float(account.get("cash_balance")),
                last4=account["last4"].strip(),
            ))

    non_retirement_accounts = data.get("non_retirement_accounts", [])
    if not 1 <= len(non_retirement_accounts) <= 6:
        return jsonify({"error": "Clients must have 1-6 non-retirement accounts"}), 400
    for account in non_retirement_accounts:
        if account.get("account_type") and account.get("last4"):
            db.session.add(NonRetirementAccount(
                client_id=client.id,
                account_type=account["account_type"].strip(),
                balance=parse_float(account.get("balance")),
                cash_balance=parse_float(account.get("cash_balance")),
                last4=account["last4"].strip(),
            ))

    trusts = data.get("trusts", [])
    if len(trusts) > 1:
        return jsonify({"error": "Clients can have at most 1 trust in V1"}), 400
    for trust in trusts:
        if trust.get("property_address"):
            db.session.add(Trust(
                client_id=client.id,
                property_address=trust["property_address"].strip(),
                zillow_value=parse_float(trust.get("zillow_value")),
            ))

    liabilities = data.get("liabilities", [])
    if len(liabilities) > 3:
        return jsonify({"error": "Clients can have at most 3 liabilities"}), 400
    for liability in liabilities:
        if liability.get("liability_type"):
            db.session.add(Liability(
                client_id=client.id,
                liability_type=liability["liability_type"].strip(),
                balance=parse_float(liability.get("balance")),
                interest_rate=parse_float(liability.get("interest_rate")),
            ))

    db.session.commit()
    return jsonify(build_client_payload(client))


@app.route("/api/clients/<int:client_id>", methods=["DELETE"])
def delete_client(client_id):
    """Delete a client and all related records."""
    client = get_client_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return jsonify({"message": "Client deleted"}), 200


# ---------------------------------------------------------------------------
# Report generation API
# ---------------------------------------------------------------------------

@app.route("/api/clients/<int:client_id>/report-data", methods=["GET"])
def get_report_data(client_id):
    """
    Return the static data needed to pre-fill a quarterly report form,
    plus the most recent balances as references.
    """
    client = get_client_or_404(client_id)

    # Find the most recent report to pre-fill "last value" references
    last_report = (
        db.session.query(QuarterlyReport)
        .filter_by(client_id=client.id)
        .order_by(QuarterlyReport.generated_at.desc())
        .first()
    )
    last_values = {}
    if last_report:
        for dp in last_report.data_points:
            last_values[dp.field_name] = dp.field_value

    # Build the payload
    payload = {
        "client": client.to_dict(),
        "inflow": client.monthly_salary,
        "outflow": client.monthly_expenses,
        "private_reserve_target": client.private_reserve_target or client.computed_private_reserve_target(),
        "retirement_accounts": [a.to_dict() for a in client.retirement_accounts],
        "non_retirement_accounts": [a.to_dict() for a in client.non_retirement_accounts],
        "trusts": [t.to_dict() for t in client.trusts],
        "liabilities": [l.to_dict() for l in client.liabilities],
        "last_values": last_values,
    }
    return jsonify(payload)


@app.route("/api/clients/<int:client_id>/reports", methods=["POST"])
def generate_report(client_id):
    """
    Generate a quarterly report with SACS and TCC PDFs.

    The request body should contain the current quarter/year, all account
    balances, and any manually entered trust/zillow values.
    """
    client = get_client_or_404(client_id)
    data = request.get_json() or {}

    quarter = data.get("quarter")
    year = data.get("year")
    if not quarter or not year:
        return jsonify({"error": "Quarter and year are required"}), 400

    try:
        year = int(year)
    except (ValueError, TypeError):
        return jsonify({"error": "Year must be a number"}), 400

    # Validate that all dynamic balance fields are present
    balances = data.get("balances", {})

    # Collect accounts for validation
    retirement = [a.to_dict() for a in client.retirement_accounts]
    non_retirement = [a.to_dict() for a in client.non_retirement_accounts]
    liabilities = [l.to_dict() for l in client.liabilities]
    trusts = [t.to_dict() for t in client.trusts]

    missing = []
    for account in retirement:
        key = f"retirement_{account['id']}"
        if key not in balances or balances[key] == "":
            missing.append(f"Retirement {account['account_type']} ending in {account['last4']}")
    for account in non_retirement:
        key = f"non_retirement_{account['id']}"
        if key not in balances or balances[key] == "":
            missing.append(f"Non-Retirement {account['account_type']} ending in {account['last4']}")
    for liability in liabilities:
        key = f"liability_{liability['id']}"
        if key not in balances or balances[key] == "":
            missing.append(f"Liability {liability['liability_type']}")
    if not trusts:
        # Trust is optional at the client level
        pass
    else:
        for trust in trusts:
            key = f"trust_zillow_{trust['id']}"
            if key not in balances or balances[key] == "":
                missing.append(f"Trust value for {trust['property_address']}")

    # Private reserve balance is required
    if "private_reserve_balance" not in balances or balances["private_reserve_balance"] == "":
        missing.append("Private Reserve balance")

    if missing:
        return jsonify({"error": "Missing required balance fields", "fields": missing}), 400

    # Create the report record
    report = QuarterlyReport(
        client_id=client.id,
        quarter=quarter,
        year=year,
    )
    db.session.add(report)
    db.session.flush()

    # Persist every snapshot field as QuarterlyData
    for name, value in balances.items():
        db.session.add(QuarterlyData(
            report_id=report.id,
            field_name=name,
            field_value=str(value),
        ))

    # Build calculation context for the PDFs
    calc_context = build_calculation_context(client, balances)

    # Generate filenames and write PDFs
    safe_name = secure_filename(f"{client.last_name}_{client.first_name}")
    sacs_filename = f"SACS_{safe_name}_{quarter}_{year}_{report.id}.pdf"
    tcc_filename = f"TCC_{safe_name}_{quarter}_{year}_{report.id}.pdf"
    sacs_path = os.path.join(PDF_OUTPUT_DIR, sacs_filename)
    tcc_path = os.path.join(PDF_OUTPUT_DIR, tcc_filename)

    generate_sacs_pdf(sacs_path, client, calc_context)
    generate_tcc_pdf(tcc_path, client, calc_context)

    report.sacs_pdf_path = sacs_path
    report.tcc_pdf_path = tcc_path
    db.session.commit()

    return jsonify({
        "report": report.to_dict(),
        "calculations": calc_context,
        "download_urls": {
            "sacs": f"/api/reports/{report.id}/download/sacs",
            "tcc": f"/api/reports/{report.id}/download/tcc",
        },
    }), 201


def build_calculation_context(client, balances):
    """
    Build the SACS and TCC calculation values from the entered balances.

    All totals are returned as floats so the frontend and PDFs match exactly.
    """
    inflow = parse_float(client.monthly_salary)
    outflow = parse_float(client.monthly_expenses)
    excess = inflow - outflow
    private_reserve_target = client.private_reserve_target or client.computed_private_reserve_target()

    retirement_accounts = [a.to_dict() for a in client.retirement_accounts]
    non_retirement_accounts = [a.to_dict() for a in client.non_retirement_accounts]
    trusts = [t.to_dict() for t in client.trusts]
    liabilities = [l.to_dict() for l in client.liabilities]

    # Retirement totals by owner
    client1_retirement = 0.0
    client2_retirement = 0.0
    for account in retirement_accounts:
        balance = parse_float(balances.get(f"retirement_{account['id']}"))
        account["current_balance"] = balance
        if account["owner"] == "client2":
            client2_retirement += balance
        else:
            client1_retirement += balance

    # Non-retirement total (trust is excluded per PRD)
    non_retirement_total = 0.0
    for account in non_retirement_accounts:
        balance = parse_float(balances.get(f"non_retirement_{account['id']}"))
        account["current_balance"] = balance
        non_retirement_total += balance

    # Trust values
    trust_total = 0.0
    for trust in trusts:
        trust["current_value"] = parse_float(balances.get(f"trust_zillow_{trust['id']}"))
        trust_total += trust["current_value"]

    # Liabilities total (displayed separately, never subtracted)
    liabilities_total = 0.0
    for liability in liabilities:
        liability["current_balance"] = parse_float(balances.get(f"liability_{liability['id']}"))
        liabilities_total += liability["current_balance"]

    grand_total = client1_retirement + client2_retirement + non_retirement_total + trust_total

    return {
        "inflow": inflow,
        "outflow": outflow,
        "excess": excess,
        "private_reserve_target": private_reserve_target,
        "private_reserve_balance": parse_float(balances.get("private_reserve_balance", 0)),
        "client1_retirement_total": client1_retirement,
        "client2_retirement_total": client2_retirement,
        "non_retirement_total": non_retirement_total,
        "trust_total": trust_total,
        "grand_total": grand_total,
        "liabilities_total": liabilities_total,
        "retirement_accounts": retirement_accounts,
        "non_retirement_accounts": non_retirement_accounts,
        "trusts": trusts,
        "liabilities": liabilities,
    }


@app.route("/api/reports/<int:report_id>/download/<string:pdf_type>", methods=["GET"])
def download_pdf(report_id, pdf_type):
    """Download a generated SACS or TCC PDF by report ID."""
    report = db.session.get(QuarterlyReport, report_id)
    if not report:
        abort(404, description="Report not found")
    if pdf_type == "sacs":
        path = report.sacs_pdf_path
    elif pdf_type == "tcc":
        path = report.tcc_pdf_path
    else:
        abort(404)

    if not path or not os.path.exists(path):
        abort(404, description="PDF not found")

    return send_file(
        path,
        as_attachment=True,
        download_name=os.path.basename(path),
        mimetype="application/pdf",
    )


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": error.description or "Bad request"}), 400


def initialize_database():
    """Create all tables and seed sample data if the database is empty."""
    with app.app_context():
        db.create_all()

        if Client.query.first() is not None:
            return

        # Seed sample data when the app starts with an empty database.
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

        db.session.add_all([
            RetirementAccount(client_id=client1.id, owner="client1", account_type="401K", balance=875000.00, cash_balance=25000.00, last4="2147"),
            RetirementAccount(client_id=client1.id, owner="client1", account_type="IRA", balance=320000.00, cash_balance=5000.00, last4="8832"),
            RetirementAccount(client_id=client1.id, owner="client2", account_type="Roth IRA", balance=245000.00, cash_balance=3000.00, last4="5519"),
        ])
        db.session.add_all([
            NonRetirementAccount(client_id=client1.id, account_type="brokerage", balance=450000.00, cash_balance=30000.00, last4="7733"),
            NonRetirementAccount(client_id=client1.id, account_type="joint", balance=125000.00, cash_balance=10000.00, last4="9912"),
        ])
        db.session.add(
            Trust(client_id=client1.id, property_address="742 Evergreen Terrace, Springfield, IL", zillow_value=1200000.00)
        )
        db.session.add_all([
            Liability(client_id=client1.id, liability_type="mortgage", balance=285000.00, interest_rate=3.25),
            Liability(client_id=client1.id, liability_type="auto_loan", balance=18000.00, interest_rate=4.90),
        ])

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
        app.logger.info("Database initialized with sample data on startup.")


# Run initialization once at startup (covers both `python app.py` and Gunicorn).
initialize_database()


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description or "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
