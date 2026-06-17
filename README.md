# AW Client Report Portal

A web application for a financial planning firm to automate quarterly client reports.
It replaces manual Excel/Word/Canva workflows with automated calculations and
PDF generation for SACS (Savings and Cashflow Snapshot) and TCC (Total Client
Composition) reports.

## Tech Stack

- **Frontend**: HTML, Tailwind CSS (via CDN), Vanilla JavaScript
- **Backend**: Python + Flask
- **Database**: SQLite
- **PDF Generation**: ReportLab
- **Deployment**: Railway-ready

## Features

- **Client Management**: Add, edit, and delete client profiles with spouse info,
  retirement accounts, non-retirement accounts, trusts, and liabilities.
- **Quarterly Report Entry**: Pre-populated data entry with "Use last value"
  checkboxes and real-time calculation totals.
- **Automated Calculations**: Deterministic SACS and TCC math with the critical
  rules that liabilities are displayed separately and trusts are not included in
  non-retirement totals.
- **PDF Generation**: Pixel-perfect SACS (2-page) and TCC (1-page) PDFs using
  ReportLab absolute positioning.
- **Report History**: Re-download previous quarterly reports.

## Project Structure

```
.
├── app.py                 # Flask application and API routes
├── database.py            # SQLAlchemy setup and database path helper
├── models.py              # All database models
├── pdf_generator.py       # SACS and TCC PDF generation with ReportLab
├── init_db.py             # Database initialization with sample data
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── client_form.html
│   └── report_form.html
└── static/                # CSS and JavaScript
    ├── css/style.css
    └── js/
        ├── app.js
        ├── dashboard.js
        ├── client_form.js
        └── report_form.js
```

## Local Development Setup

1. **Clone or navigate to the project directory**:

   ```bash
   cd financial-data-portal
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment variables**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set a `SECRET_KEY`. For local development, either delete
   `RAILWAY_DATABASE_PATH` or change it to a local file like `database.db`. The
   `.env.example` file is tuned for Railway deployment.

5. **Initialize the database with sample data**:

   ```bash
   python init_db.py
   ```

6. **Run the application** (development server):

   ```bash
   python app.py
   ```

   Or use Gunicorn for a production-ready server:

   ```bash
   gunicorn app:app
   ```

7. **Open in browser**:

   ```
   http://localhost:5000
   ```

## Testing with Sample Clients

After running `python init_db.py`, the database contains two fully configured
clients:

1. **James & Margaret Anderson** — Married client with retirement accounts for
   both spouses, brokerage and joint accounts, a trust property, and two
   liabilities.
2. **Robert Chen** — Single client with a 401K, IRA, brokerage account, a New
   York trust property, and a mortgage.

### Recommended test flow

1. Open the dashboard at `http://localhost:5000`.
2. Click **Generate Report** on either client card.
3. Verify that the quarter/year and pre-filled cashflow numbers are correct.
4. Enter balances for each account (or use the **Use last value** checkboxes).
5. Watch the **Live Totals** update in real-time as you type.
6. Click **Generate Report** and download the SACS and TCC PDFs.
7. Confirm the PDF totals match the live totals and the critical rules hold:
   - Trust is not included in the non-retirement total.
   - Liabilities are shown separately and not subtracted from net worth.

### Automated API test

A test script is included to validate the API endpoints, calculations, and PDF
 downloads:

```bash
pip install requests
python test_app.py
```

The script expects the app to be running at `http://localhost:5000` (change
`APP_URL` if needed). It creates a temporary client, generates reports for both
sample clients, downloads the PDFs, verifies the math, and cleans up the
temporary client.

## Environment Variables

| Variable | Description | Required |
| --- | --- | --- |
| `RAILWAY_DATABASE_PATH` | SQLite path on Railway disk, e.g. `/data/database.db` | On Railway only |
| `SECRET_KEY` | Flask session secret | Yes |
| `CANVA_API_KEY` | Optional Canva API key (not used in V1) | No |
| `FLASK_ENV` | `development` or `production` | No |
| `FLASK_DEBUG` | `1` to enable debug mode | No |
| `PORT` | Port to run the server on | No, defaults to 5000 |

## Railway Deployment

1. Push the project to a Git repository.
2. Create a new Railway project and connect the repository.
3. Add a **Railway volume** mounted at `/data` so the SQLite database persists.
4. In Railway Variables, use the values from `.env.example` and ensure:
   - `RAILWAY_DATABASE_PATH=/data/database.db`
   - `SECRET_KEY=<a strong random string>`
5. Railway will detect the `Procfile` and start the app with Gunicorn.
6. After the first deploy, run the init script once via Railway's shell or add a
   startup hook:

   ```bash
   python init_db.py
   ```

7. Verify that the dashboard loads, then generate a test report.

## Calculation Rules

**SACS:**
- `Excess = Monthly Inflow - Monthly Outflow`
- `Private Reserve Target = (6 × Monthly Expenses) + Insurance Deductibles`
  - In V1, insurance deductibles are not tracked, so the deductible sum is 0.

**TCC:**
- `Client 1 Retirement Total = sum of retirement accounts where owner = client1`
- `Client 2 Retirement Total = sum of retirement accounts where owner = client2`
- `Non-Retirement Total = sum of all non-retirement accounts`
- `Grand Total = Client1 + Client2 + Non-Retirement + Trust`
- `Liabilities Total = sum of all liability balances` (displayed separately)

## Notes

- No external API integrations are used in V1.  Zillow values and all balances
  are entered manually.
- The PDFs use absolute positioning so the layout stays stable regardless of
  the number of account bubbles.
- All calculations are deterministic and run both on the frontend for live
  feedback and on the backend for PDF generation.

## License

Internal use for the financial planning firm.
