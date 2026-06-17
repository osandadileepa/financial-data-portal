# AW Client Report Portal — PRD v1.0

**Date:** 2026-04-09 | **Build Type:** New

## One-Line Summary
A portal where the team enters client financial data into a structured form and generates polished quarterly SACS (cashflow) and TCC (net worth) PDF reports in minutes instead of a full day.

---

## Company Context
EF is a financial planning firm based in Atlanta. The firm serves high net worth and ultra-high-net-worth families with comprehensive financial planning, including cash flow management, investment oversight, retirement planning, and college planning.

**Team:** Three people:
- Andrew
- Rebecca (financial planner with Schwab access and compliance responsibilities)
- Maryann (executive assistant, recently hired through Sagan)

**Clients:** Approximately 6 regular clients on retainer with quarterly meetings, plus assets under management. Clients are millionaires with high expectations for professionalism and accuracy.

**Current Process:** Report preparation takes a full day per client meeting, involving manual data pulling from multiple sources (Pinnacle Bank, Charles Schwab, RightCapital, Zillow) and assembly in Canva and Word documents.

---

## Developer Brief

### Client Setup (One-Time)
The team currently stores client data across Excel spreadsheets, PreciseFP (onboarding questionnaires), and various document files in Dropbox. There's no central CRM. The portal provides a simple client record where they enter static info once:
- Names, DOB, age, last four of SSN
- Account types (retirement, non-retirement, joint, trust)
- Monthly salary, agreed expense budget
- Which accounts each client has

This eliminates re-entering the same info every quarter.

### Data Entry + Automated Math
Currently, Maryann and Rebecca spend a full day pulling balances from:
- Pinnacle Bank (via email request)
- Schwab (Rebecca logs in manually)
- Zillow (for house values)
- RightCapital (sometimes)

They then manually calculate totals, excess transfers, and net worth — often making errors.

**The portal presents:**
- A checklist of fields per client, pre-populated with static data
- Fields for entering current balances
- All math is automatic

**Key quote from Rebecca:** *"all of that math is done manually, so even just automating that would be great"* (25:36)

### PDF Generation Matching Existing Format
Andrew created the SACS and TCC templates and is happy with how they look — no visual redesign.

**SACS** (screenshot at 13:08): Cashflow diagram with Inflow, Outflow, and Private Reserve bubbles connected by arrows.

**TCC**: Circle chart with retirement accounts (top), non-retirement (bottom), trust (center), and liabilities.

**Key quote from Rebecca:** *"We're not looking to change the appearance"* (11:15)

**Key quote from Maryann:** *"I like that, a little [polish] would be nice"* (52:42)

### Export Options
- Download as PDF directly
- Export to Canva for any last-minute adjustments

Both options from the same interface.

---

## Stack Suggestions

| Layer | Tool | Rationale |
|-------|------|-----------|
| **Hosting** | Railway | Standard Sagan default. Simple web app, no heavy compute needed |
| **Frontend** | HTML + CSS + JS | Clean, professional portal. Team is 3 people — needs to be simple and beautiful. No framework overhead |
| **Backend** | Python | PDF generation (ReportLab or WeasyPrint), form handling, calculations. Straightforward data processing |
| **Database** | SQLite on Railway volume | Client profiles, account structures, report history. 6 clients — minimal volume |
| **PDF Generation** | ReportLab or WeasyPrint | Generate pixel-perfect PDFs matching existing SACS and TCC templates. Templates are fixed layout — no dynamic resizing needed |
| **AI** | None for V1 | This is a structured data entry + calculation + PDF generation tool. No AI reasoning needed. All math is deterministic |

**Environment Variables:**
- `CANVA_API_KEY` (if Canva export is built)
- `RAILWAY_DATABASE_PATH`

**Note:** No API integrations in V1. All financial data is entered manually by the team. This is intentional — RightCapital data is unreliable, Schwab access has compliance restrictions, and Pinnacle Bank data comes via secure email. V2 can add automated data pulling.

---

## Screen Share Timestamps

| Timestamp | Screenshots | Description | Relevance |
|-----------|-------------|-------------|-----------|
| 04:52 | 1_04m52s.jpg | Maryann showed Dropbox folder structure — client Excel-based budget template clients fill during onboarding | Shows current file organization — no central CRM, outflow/expense number |
| 29:14-29:18 | 100_29m14s.jpg — 102_29m18s.jpg | Data Point List document — detailed specification of where each data field comes from for SACS and TCC | **Critical reference.** This document maps every field to its data source. The engineer should request this document |

---

## Key Definitions

| Term | Meaning | Examples |
|------|---------|----------|
| **SACS** | Simple Automated Cash Flow — a one-page visual diagram showing how money flows from the client's paycheck through their bank accounts each month | Inflow ($15,000/mo) → Outflow ($11,000/mo for expenses) → Private Reserve (excess savings) |
| **TCC** | Total Client Chart — a one-page net worth overview showing all client accounts organized by type (retirement, non-retirement, trust, liabilities) with balances and totals | Retirement: IRA $11K + Roth IRA $15K = $26K total. Non-retirement: brokerage $50K. Trust: house $450K. Liabilities: mortgage $200K |
| **Inflow** | The client's take-home pay deposited into their primary checking account | $15,000/month after taxes |
| **Outflow** | The agreed-upon monthly expense budget transferred from inflow to the spending account | $11,000/month (rounded up from actual ~$10,500 to create buffer) |
| **Private Reserve** | High-yield savings account where excess cash (inflow minus outflow) accumulates | Target = 6 months of expenses + all insurance deductibles |
| **Trust** | Usually funded by the client's primary residence. Value updated quarterly from Zillow Zestimate | *"We go to Zillow, type in their address, and it just pops up"* |
| **Pinnacle Bank** | The bank where all clients are encouraged to open their personal banking accounts. Balances requested via secure email 2 days before meetings | Personal bankers provide balances on request |
| **RightCapital** | Financial planning aggregator tool that connects to clients' external accounts. Has an API but data is often stale or disconnected | *"Don't trust RightCapital that much... their own API is not perfect"* |
| **PreciseFP** | Client onboarding questionnaire tool — closest thing to a CRM. Stores client profiles, family info, advisor assignments | Has an API; used for onboarding data collection |
| **Floor** | $1,000 minimum balance maintained in each bank account as a buffer | Never changes — always $1,000 |

---

## User Story 1: Client Profile Management

**Description:** A simple client management screen where the team enters each client's static information once. This replaces scattered Excel files and Dropbox folders as the source of truth for client data.

### Acceptance Criteria:
- Add a new client with:
  - Name(s), DOB, age (auto-calculated), last four of SSN
  - Spouse info if applicable
- Define the client's account structure:
  - Retirement accounts (IRA, Roth IRA, 401K, pension)
  - Non-retirement accounts (brokerage, joint)
  - Trust details (property address for Zillow lookup)
  - Liabilities (mortgage, auto loan with interest rates)
- Enter static financial data:
  - Monthly salary (after tax)
  - Agreed monthly expense budget
  - Private reserve target
- Support both single and married clients (Client 1 / Client 2 structure)
- Edit client details when things change (new job, raise, new account)
- Client list view showing all clients with last report date

**Data Sources:** Manual entry (from PreciseFP onboarding data, monthly expense worksheet)

**AI/Models:** None

**Notes:** ~6 clients currently, may grow to 12. Rebecca: *"We're a very small operation, there's 3 of us"* (31:54). The portal essentially serves as a lightweight CRM for report generation purposes. The Data Point List document maps exactly which fields are needed — request this document from the team.

---

## User Story 2: Enter Quarterly Balances and Auto-Calculate Everything

### 2a: Quarterly Report Data Entry

**Description:** Before a client meeting, the team clicks "Generate Report" for a client. The system shows a structured form with all fields needed, pre-populated with static data, and blanks for the dynamic balances that need to be entered.

### Acceptance Criteria:
- One-click "Generate Report" from client profile
- Form shows all fields needed, organized by report section (SACS fields, then TCC fields)
- Static data (salary, expense budget, account types) is pre-filled from client profile
- Dynamic fields show clear labels:
  - "Roth IRA Balance"
  - "Schwab Brokerage Balance"
  - "Private Reserve Balance"
  - "Zillow Home Value"
- Each dynamic field shows the last known value (from previous quarter) as reference
- Fields that haven't been entered are highlighted as incomplete
- Option to "use last value" for fields that haven't changed
- Manual override on any field

**Data Sources:** Client profile (static), manual entry (dynamic balances)

**AI/Models:** None

**Notes:** Rebecca described the current pain: *"we have to keep double checking, and things like that"* (25:54). Maryann: *"This takes us a day to prepare. If we could take this down to an hour"* (33:34). The form should make it impossible to generate a report with missing data — all required fields must be filled.

---

### 2b: Automated Calculations

**Description:** All math is automated once balances are entered. No manual addition, subtraction, or cross-referencing.

### Acceptance Criteria:

**SACS:**
- Excess = Inflow - Outflow (auto-calculated)
- Private Reserve Target = (6 × monthly expenses) + sum of all insurance deductibles

**TCC:**
- Client 1 Retirement Total = sum of Client 1's retirement account balances
- Client 2 Retirement Total = sum of Client 2's retirement account balances
- Non-Retirement Total = sum of all non-retirement account balances (excluding trust)
- Grand Total Net Worth = Client 1 Retirement + Client 2 Retirement + Non-Retirement + Trust
- Liabilities Total = sum of all liability balances (displayed separately, NOT subtracted from net worth)
- All totals update in real-time as balances are entered

**Data Sources:** Entered balances from 2a

**AI/Models:** None — pure arithmetic

**Notes:** Rebecca was very specific about the calculation rules:
- *"we do not subtract liabilities from their net worth, they're just a separate box"* (26:15)
- *"We do not add the trust in [to non-retirement total]... the non-retirement total is only the accounts, not the trust"* (24:28)

**These rules must be exact.**

---

## User Story 3: PDF Generation

### 3a: SACS PDF Generation

**Description:** Generate a SACS (Simple Automated Cash Flow) PDF matching the existing visual template — cashflow bubble diagram with Inflow, Outflow, and Private Reserve sections.

### Acceptance Criteria:
- PDF matches existing SACS layout:
  - Green Inflow circle
  - Red Outflow circle
  - Blue Private Reserve section
  - Connecting arrows
- Client name and date in header
- Page 1: Cashflow diagram with monthly amounts (Inflow → Outflow → Private Reserve)
- Page 2: Private Reserve balance, investment account balance (Schwab), target savings number
- All numbers correctly placed in their visual positions
- Format is fixed — nothing shifts or misaligns regardless of number size
- Company branding colors (blue) applied

**Data Sources:** Calculated values from 2b

**AI/Models:** None

**Notes:** Rebecca: *"We want the form set so nothing can move"* (13:57). The current Canva template causes alignment issues — *"if we move something, especially with the circle chart, this one gets moved"* (12:47). The PDF must be pixel-perfect and stable. Request sample PDFs from the team for exact layout matching.

---

### 3b: TCC (Circle Chart) PDF Generation

**Description:** Generate a TCC (Total Client Chart) PDF matching the existing net worth overview template — account bubbles organized by type with totals.

### Acceptance Criteria:
- PDF matches existing TCC layout:
  - Retirement accounts (top)
  - Non-retirement (bottom)
  - Trust (center)
  - Liabilities (separate section)
- Client name and date in header
- Green client info bubbles with names, ages, DOB, last four SSN
- Account bubbles show:
  - Account type
  - Last four account number
  - Balance
  - Cash balance (for investment accounts)
- Gray summary boxes:
  - Client 1 Retirement Total
  - Client 2 Retirement Total
  - Non-Retirement Total
  - Grand Total
- Liabilities section with type, interest rate, and balance
- Dynamic number of account bubbles per client (some have 2, some have 5)
- Trust section shows property address and Zillow value

**Data Sources:** Calculated values from 2b

**AI/Models:** None

**Notes:** The TCC has variable layout — number of account bubbles varies by client. Rebecca: *"we personalize this for every client. We make however many bubbles we need"* (22:00). The template must handle 1-6 retirement accounts per spouse and 1-6 non-retirement accounts. Liabilities are 0-3 items typically.

---

## User Story 4: Export Options

### 4a: PDF Download and Canva Export

**Description:** After generating reports, the team can download as PDF or export to Canva for final adjustments.

### Acceptance Criteria:
- "Download as PDF" button generates and downloads both SACS and TCC as separate PDFs
- "Export to Canva" button creates the report in the team's Canva workspace for visual editing
- Downloaded PDFs are print-ready and client-presentation quality
- Report generation history: team can re-download previous quarterly reports

**Data Sources:** Generated report data

**AI/Models:** None

**Notes:** Zaki proposed both options at 52:56-53:07. Maryann confirmed: *"Sound? Perfect."* The Canva export is a nice-to-have — if Canva API integration is complex, PDF download alone covers the core need. Rebecca: *"We don't want to do it in either [Canva or Word], ideally"* (13:48) — the portal itself is the preferred tool.

---

## Data Sources

### Primary Data Source (V1):
| Source | Type | Direction | Integration Method | Notes |
|--------|------|-----------|-------------------|-------|
| Manual Entry (Team) | Form Input | In | Portal web form | Primary data source for V1. Team enters balances from Pinnacle Bank, Schwab, Zillow |

### Data Sources (Not in V1 Scope):
- **RightCapital API** — auto-pull account balances (unreliable, needs investigation)
- **Schwab** — auto-pull investment balances (compliance restrictions on credentials)
- **Pinnacle Bank** — auto-request balances (currently via secure email)
- **Zillow API** — auto-pull Zestimate for trust property values

---

## Discussed But Not Confirmed

These items came up in the transcript but were not explicitly committed to. Verify with the customer before including in the build.

| Item | Context | Priority Clarification |
|------|---------|----------------------|
| **Canva export** | Zaki proposed exporting to Canva (52:56) and Maryann confirmed, but Rebecca also said *"we don't want to do it in either [Canva or Word], ideally"* (13:48) | The portal PDF may be sufficient without Canva export. Clarify priority |
| **Dropbox auto-save** | Maryann asked about automatically saving generated reports to the client's Dropbox folder (41:23) | Lightweight to add if confirmed |
| **Monthly email distribution** | Zaki suggested auto-emailing reports to clients monthly (16:15). Rebecca said they only do quarterly | Not committed — future enhancement if they want to increase touchpoints |

---

## Out of Scope (Future Phases)

| Item | Notes |
|------|-------|
| **Auto-pull from RightCapital API** | Maryann explicitly deferred this: *"don't trust RightCapital that much... make that second version"* (49:06-49:24). V2 feature |
| **Auto-pull from Schwab** | Rebecca said the login *"cannot be shared with any agent"* due to compliance (48:14). Needs to be explored carefully. V2 feature |
| **Client-facing monthly expense worksheet on portal** | Rebecca's idea — clients could update their expense worksheet directly in the portal instead of via Excel (42:14). Separate LEGO brick |
| **Onboarding automation agent** | Zaki proposed automating client onboarding with reminders and form completion tracking (43:36-43:56). Separate LEGO brick |
| **Plaid integration** | Zaki mentioned potentially connecting to bank accounts via Plaid instead of relying on RightCapital (49:28-49:46). V2+ feature |
| **Podcast production** | Andrew asked about podcast production help in the first call — this is a hiring request, not an agent build |

---

## Confidence Score

### Overall: **4/5** (Customer Impact is the constraint)

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Scope Definition** | 5/5 | Exceptionally clear. Two calls define the exact input fields and output formats. Rebecca and Maryann created a "Data Point List" document mapping every field to its source. Sample PDFs were shared. The team knows exactly what they want |
| **Technical Feasibility** | 5/5 | This is a straightforward web app: form input → calculations → PDF generation. No API integrations in V1. No AI needed. Fixed-layout PDF templates. Well-understood technology. The only complexity is matching the visual layout exactly (circle chart with variable bubbles) |
| **Customer Impact** | 4/5 | Reduces meeting prep from a full day to under an hour per client. Eliminates manual math errors. But with only 6 clients meeting quarterly, the time savings are ~24 person-days/year. The bigger impact is error elimination and enabling scale — the firm can take on more clients without more staff |

**Summary:** Excellent build. Extremely well-defined scope with sample documents provided. Zero technical risk. The main value is error elimination, consistency, and enabling the firm to scale beyond 6 clients without adding staff. Rebecca and Maryann are engaged, detail-oriented, and will be excellent collaborators during the build.

---

## Audit Notes

All engineering stories traced to specific transcript moments across both calls:

| User Story | Transcript Reference |
|------------|---------------------|
| **Client setup (US1)** | Confirmed by Zaki's portal proposal (35:44-36:05) and discussion of PreciseFP data (50:00-50:44) |
| **Data entry and calculations (US2)** | Confirmed by Rebecca's detailed walkthrough of both reports (05:55-26:34) and Maryann's statement *"all of that math is done manually, so even just automating that would be great"* (25:36) |
| **PDF generation (US3)** | Confirmed by extensive discussion of SACS and TCC formats, Rebecca's insistence on fixed layout (13:57), and agreement to match existing visual design (11:15) |
| **Export options (US4)** | Confirmed by Zaki's proposal (52:56) and Maryann's confirmation |

**Moved to "Discussed But Not Confirmed":**
- Canva export (ambiguous — portal may be sufficient)
- Dropbox auto-save (mentioned but not committed)
- Monthly email distribution (team only does quarterly)

**No red flags found** — all features trace directly to the transcript.

---

## Quick Reference: Technical Requirements

### Frontend
- Clean, professional portal
- Client list view
- Client profile management
- Quarterly report data entry form
- Real-time calculation updates
- PDF download buttons
- Canva export button (if implemented)

### Backend
- Python-based
- Form handling
- Calculation engine (SACS and TCC)
- PDF generation using ReportLab or WeasyPrint
- SQLite database management

### Database Schema (Suggested)
- **clients:** id, name, spouse_name, dob, spouse_dob, ssn_last4, spouse_ssn_last4, monthly_salary, monthly_expenses, private_reserve_target, created_at, updated_at
- **accounts:** id, client_id, type (retirement/non-retirement/trust/liability), subtype, account_number_last4, balance, cash_balance, interest_rate, property_address (for trust)
- **reports:** id, client_id, quarter, year, generated_at, pdf_path_sacs, pdf_path_tcc
- **quarterly_data:** id, report_id, field_name, field_value

### Key Calculations to Implement
1. **Excess** = Inflow - Outflow
2. **Private Reserve Target** = (6 × monthly expenses) + sum(insurance deductibles)
3. **Client 1 Retirement Total** = sum(Client 1's retirement accounts)
4. **Client 2 Retirement Total** = sum(Client 2's retirement accounts)
5. **Non-Retirement Total** = sum(all non-retirement accounts excluding trust)
6. **Grand Total** = Client 1 Retirement + Client 2 Retirement + Non-Retirement + Trust
7. **Liabilities Total** = sum(all liabilities)

---

**End of PRD v1.0**
