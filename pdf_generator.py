import os
from datetime import date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# Primary brand color from the PRD
BRAND_BLUE = HexColor("#1a56db")
BRAND_DARK = HexColor("#1e293b")
GREEN = HexColor("#4CAF50")
RED = HexColor("#f44336")
LIGHT_GRAY = HexColor("#f3f4f6")
DARK_GRAY = HexColor("#6b7280")

# Page dimensions
PAGE_WIDTH, PAGE_HEIGHT = letter


def format_currency(value):
    """Format a number as US currency: $X,XXX.XX"""
    try:
        value = float(value)
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


def format_percent(value):
    """Format a number as a percentage: X.XX%"""
    try:
        value = float(value)
        return f"{value:.2f}%"
    except (ValueError, TypeError):
        return "0.00%"


def _draw_header(c, client, title):
    """Draw the branded header used across all pages."""
    # Header background bar
    c.setFillColor(BRAND_BLUE)
    c.rect(0, PAGE_HEIGHT - 80, PAGE_WIDTH, 80, fill=1, stroke=0)

    # Company name on the left
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, PAGE_HEIGHT - 45, "AW Client Report Portal")

    # Report title
    c.setFont("Helvetica", 14)
    c.drawString(40, PAGE_HEIGHT - 65, title)

    # Client name and date on the right
    today = date.today().strftime("%B %d, %Y")
    c.setFont("Helvetica", 12)
    c.drawRightString(PAGE_WIDTH - 40, PAGE_HEIGHT - 45, client.full_name())
    c.drawRightString(PAGE_WIDTH - 40, PAGE_HEIGHT - 65, today)


def _draw_footer(c):
    """Draw a simple footer with page branding."""
    c.setStrokeColor(DARK_GRAY)
    c.setLineWidth(0.5)
    c.line(40, 40, PAGE_WIDTH - 40, 40)
    c.setFillColor(DARK_GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(40, 28, "Prepared by AW Client Report Portal")
    c.drawRightString(PAGE_WIDTH - 40, 28, "Confidential")


def _draw_centered_text(c, text, x, y, font="Helvetica", size=12, color=black):
    """Draw text centered horizontally at the given coordinates."""
    c.setFont(font, size)
    c.setFillColor(color)
    width = c.stringWidth(text, font, size)
    c.drawString(x - width / 2, y, text)


def generate_sacs_pdf(output_path, client, calc_context):
    """
    Generate the SACS (Savings and Cashflow Snapshot) PDF.

    Page 1: Cashflow bubble diagram.
    Page 2: Detail view with private reserve, investment balance, and target.
    """
    c = canvas.Canvas(output_path, pagesize=letter)

    # ------------------------------------------------------------------
    # Page 1 - Bubble diagram
    # ------------------------------------------------------------------
    _draw_header(c, client, "SACS - Savings and Cashflow Snapshot")

    inflow = calc_context["inflow"]
    outflow = calc_context["outflow"]
    excess = calc_context["excess"]
    private_reserve_balance = calc_context["private_reserve_balance"]
    private_reserve_target = calc_context["private_reserve_target"]

    # Page title
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 130, "Cashflow Snapshot")

    # Inflow circle (green)
    c.setFillColor(GREEN)
    c.setStrokeColor(white)
    c.setLineWidth(2)
    c.circle(200, 460, 80, fill=1, stroke=1)
    _draw_centered_text(c, "Inflow", 200, 475, "Helvetica-Bold", 14, white)
    _draw_centered_text(c, format_currency(inflow), 200, 455, "Helvetica", 12, white)

    # Outflow circle (red)
    c.setFillColor(RED)
    c.circle(412, 460, 80, fill=1, stroke=1)
    _draw_centered_text(c, "Outflow", 412, 475, "Helvetica-Bold", 14, white)
    _draw_centered_text(c, format_currency(outflow), 412, 455, "Helvetica", 12, white)

    # Arrow from Inflow to Outflow
    c.setStrokeColor(BRAND_DARK)
    c.setLineWidth(3)
    c.line(280, 460, 332, 460)
    # Arrowhead
    c.setFillColor(BRAND_DARK)
    p = c.beginPath()
    p.moveTo(332, 460)
    p.lineTo(322, 455)
    p.lineTo(322, 465)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    _draw_centered_text(c, "Expenses", 306, 445, "Helvetica", 10, BRAND_DARK)

    # Excess label
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(PAGE_WIDTH / 2, 405, f"Excess: {format_currency(excess)}")

    # Arrow from Outflow to Private Reserve
    c.setStrokeColor(BRAND_DARK)
    c.setLineWidth(3)
    c.line(412, 380, 412, 330)
    p = c.beginPath()
    p.moveTo(412, 330)
    p.lineTo(407, 340)
    p.lineTo(417, 340)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    _draw_centered_text(c, "Savings", 440, 355, "Helvetica", 10, BRAND_DARK)

    # Private Reserve rectangle (blue)
    c.setFillColor(BRAND_BLUE)
    c.setStrokeColor(white)
    c.roundRect(150, 200, 400, 100, 15, fill=1, stroke=1)
    _draw_centered_text(c, "Private Reserve", PAGE_WIDTH / 2, 270, "Helvetica-Bold", 16, white)
    _draw_centered_text(c, format_currency(private_reserve_balance), PAGE_WIDTH / 2, 245, "Helvetica", 14, white)
    _draw_centered_text(c, f"Target: {format_currency(private_reserve_target)}", PAGE_WIDTH / 2, 220, "Helvetica", 10, white)

    # Legend
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica", 10)
    c.drawString(40, 120, "Green = Money coming in  |  Red = Money going out  |  Blue = Reserve savings")

    _draw_footer(c)
    c.showPage()

    # ------------------------------------------------------------------
    # Page 2 - Detail view
    # ------------------------------------------------------------------
    _draw_header(c, client, "SACS - Detail View")

    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 130, "Detail View")

    # Summary boxes
    y = PAGE_HEIGHT - 200
    box_height = 80
    box_width = 170
    gap = 20
    start_x = (PAGE_WIDTH - (3 * box_width + 2 * gap)) / 2

    boxes = [
        ("Private Reserve", format_currency(private_reserve_balance), "#1a56db"),
        ("Investment Balance", format_currency(calc_context["non_retirement_total"]), "#4CAF50"),
        ("Target Savings", format_currency(private_reserve_target), "#f59e0b"),
    ]

    for i, (label, value, color) in enumerate(boxes):
        x = start_x + i * (box_width + gap)
        c.setFillColor(HexColor(color))
        c.roundRect(x, y, box_width, box_height, 10, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + box_width / 2, y + 50, label)
        c.setFont("Helvetica", 14)
        c.drawCentredString(x + box_width / 2, y + 25, value)

    # Monthly cashflow table
    y = PAGE_HEIGHT - 340
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, y, "Monthly Cashflow")

    y -= 40
    rows = [
        ("Monthly Inflow (Salary)", format_currency(inflow)),
        ("Monthly Outflow (Expenses)", format_currency(outflow)),
        ("Excess", format_currency(excess)),
    ]

    for label, value in rows:
        c.setFillColor(BRAND_DARK)
        c.setFont("Helvetica", 12)
        c.drawString(60, y, label)
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(PAGE_WIDTH - 60, y, value)
        c.setStrokeColor(HexColor("#e5e7eb"))
        c.line(60, y - 8, PAGE_WIDTH - 60, y - 8)
        y -= 35

    # Reserve notes
    y -= 20
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, y, "Reserve Notes")
    y -= 25
    c.setFont("Helvetica", 11)
    c.drawString(60, y, f"Current Private Reserve: {format_currency(private_reserve_balance)}")
    y -= 20
    c.drawString(60, y, f"Private Reserve Target: {format_currency(private_reserve_target)}")
    y -= 20
    c.drawString(60, y, f"Gap to Target: {format_currency(private_reserve_target - private_reserve_balance)}")

    _draw_footer(c)
    c.showPage()
    c.save()


def generate_tcc_pdf(output_path, client, calc_context):
    """
    Generate the TCC (Total Client Composition) PDF.

    One page with:
    - Header
    - Client info bubbles
    - Retirement totals and account bubbles
    - Non-retirement total and account bubbles
    - Trust section
    - Liabilities section
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    _draw_header(c, client, "TCC - Total Client Composition")

    y = PAGE_HEIGHT - 130

    # ------------------------------------------------------------------
    # Client info bubbles (green)
    # ------------------------------------------------------------------
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Client Information")
    y -= 30

    info_bubbles = [
        {
            "name": client.full_name(),
            "age": client.age(),
            "dob": client.dob.strftime("%m/%d/%Y") if client.dob else "",
            "ssn": f"SSN ending in {client.ssn_last4}",
        }
    ]
    if client.spouse_first_name:
        info_bubbles.append({
            "name": f"{client.spouse_first_name} {client.spouse_last_name}",
            "age": client.spouse_age(),
            "dob": client.spouse_dob.strftime("%m/%d/%Y") if client.spouse_dob else "",
            "ssn": f"SSN ending in {client.spouse_ssn_last4}" if client.spouse_ssn_last4 else "",
        })

    bubble_width = 260
    bubble_height = 80
    gap = 20
    start_x = (PAGE_WIDTH - (len(info_bubbles) * bubble_width + (len(info_bubbles) - 1) * gap)) / 2

    for i, info in enumerate(info_bubbles):
        x = start_x + i * (bubble_width + gap)
        c.setFillColor(GREEN)
        c.roundRect(x, y - bubble_height, bubble_width, bubble_height, 12, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(x + bubble_width / 2, y - 25, info["name"])
        c.setFont("Helvetica", 10)
        c.drawCentredString(x + bubble_width / 2, y - 45, f"Age: {info['age']} | DOB: {info['dob']}")
        c.drawCentredString(x + bubble_width / 2, y - 62, info["ssn"])

    y -= (bubble_height + 30)

    # ------------------------------------------------------------------
    # Retirement section
    # ------------------------------------------------------------------
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Retirement Accounts")
    y -= 35

    # Summary boxes for client1 and client2 retirement totals
    summary_width = 240
    summary_height = 60
    c.setFillColor(HexColor("#e5e7eb"))
    c.roundRect(40, y - summary_height, summary_width, summary_height, 8, fill=1, stroke=0)
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(40 + summary_width / 2, y - 20, "Client 1 Retirement Total")
    c.setFont("Helvetica", 13)
    c.drawCentredString(40 + summary_width / 2, y - 40, format_currency(calc_context["client1_retirement_total"]))

    c.setFillColor(HexColor("#e5e7eb"))
    c.roundRect(PAGE_WIDTH - 40 - summary_width, y - summary_height, summary_width, summary_height, 8, fill=1, stroke=0)
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(PAGE_WIDTH - 40 - summary_width / 2, y - 20, "Client 2 Retirement Total")
    c.setFont("Helvetica", 13)
    c.drawCentredString(PAGE_WIDTH - 40 - summary_width / 2, y - 40, format_currency(calc_context["client2_retirement_total"]))

    y -= (summary_height + 20)

    # Retirement account bubbles split by owner
    client1_accounts = [a for a in calc_context["retirement_accounts"] if a["owner"] != "client2"]
    client2_accounts = [a for a in calc_context["retirement_accounts"] if a["owner"] == "client2"]

    left_y = y
    right_y = y
    if client1_accounts:
        left_y = _draw_account_bubbles(c, 40, y, client1_accounts, "left")
    if client2_accounts:
        right_y = _draw_account_bubbles(c, PAGE_WIDTH - 40, y, client2_accounts, "right")

    y = min(left_y, right_y) - 20

    # ------------------------------------------------------------------
    # Non-Retirement section
    # ------------------------------------------------------------------
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Non-Retirement Accounts")
    y -= 35

    c.setFillColor(HexColor("#e5e7eb"))
    c.roundRect(40, y - summary_height, summary_width, summary_height, 8, fill=1, stroke=0)
    c.setFillColor(BRAND_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(40 + summary_width / 2, y - 20, "Non-Retirement Total")
    c.setFont("Helvetica", 13)
    c.drawCentredString(40 + summary_width / 2, y - 40, format_currency(calc_context["non_retirement_total"]))

    y -= (summary_height + 15)

    # Non-retirement account bubbles
    y = _draw_account_bubbles(c, 40, y, calc_context["non_retirement_accounts"], "left")
    y -= 10

    # ------------------------------------------------------------------
    # Trust section
    # ------------------------------------------------------------------
    if calc_context["trusts"]:
        c.setFillColor(BRAND_DARK)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "Trust")
        y -= 25

        for trust in calc_context["trusts"]:
            c.setFillColor(BRAND_BLUE)
            c.setFillAlpha(0.15)
            c.roundRect(40, y - 55, PAGE_WIDTH - 80, 55, 10, fill=1, stroke=0)
            c.setFillAlpha(1.0)
            c.setFillColor(BRAND_DARK)
            c.setFont("Helvetica", 11)
            c.drawString(55, y - 25, trust["property_address"])
            c.setFont("Helvetica-Bold", 12)
            c.drawRightString(PAGE_WIDTH - 55, y - 25, format_currency(trust["current_value"]))
            y -= 70

    # ------------------------------------------------------------------
    # Grand total
    # ------------------------------------------------------------------
    c.setFillColor(BRAND_BLUE)
    c.roundRect(40, y - 45, PAGE_WIDTH - 80, 45, 10, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(55, y - 25, "Grand Total")
    c.drawRightString(PAGE_WIDTH - 55, y - 25, format_currency(calc_context["grand_total"]))
    y -= 65

    # ------------------------------------------------------------------
    # Liabilities section (displayed separately, never subtracted)
    # ------------------------------------------------------------------
    if calc_context["liabilities"]:
        c.setFillColor(RED)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "Liabilities (displayed separately)")
        y -= 25

        c.setFillColor(HexColor("#fee2e2"))
        c.roundRect(40, y - 30, summary_width, 30, 6, fill=1, stroke=0)
        c.setFillColor(RED)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(40 + summary_width / 2, y - 12, "Total Liabilities")
        c.setFont("Helvetica", 12)
        c.drawCentredString(40 + summary_width / 2, y - 28, format_currency(calc_context["liabilities_total"]))
        y -= 40

        for liability in calc_context["liabilities"]:
            c.setFillColor(BRAND_DARK)
            c.setFont("Helvetica", 10)
            label = f"{liability['liability_type'].replace('_', ' ').title()}"
            rate = format_percent(liability.get("interest_rate", 0))
            c.drawString(40, y, f"{label} ({rate})")
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(PAGE_WIDTH - 40, y, format_currency(liability["current_balance"]))
            c.setStrokeColor(HexColor("#e5e7eb"))
            c.line(40, y - 5, PAGE_WIDTH - 40, y - 5)
            y -= 22

    _draw_footer(c)
    c.showPage()
    c.save()


def _draw_account_bubbles(c, x, y, accounts, alignment="left"):
    """
    Draw a grid of account bubbles.  Supports 1-6 accounts.

    Each bubble shows the account type, last4, and current balance.  When
    alignment is 'right' the bubbles are drawn relative to the right edge of
    the page.
    """
    if not accounts:
        return y

    bubble_width = 160
    bubble_height = 90
    gap_x = 15
    gap_y = 15
    max_per_row = 3 if alignment == "left" else 3

    rows = [accounts[i:i + max_per_row] for i in range(0, len(accounts), max_per_row)]

    for row in rows:
        if alignment == "left":
            start_x = x
        else:
            start_x = x - (len(row) * bubble_width + (len(row) - 1) * gap_x)

        for i, account in enumerate(row):
            bx = start_x + i * (bubble_width + gap_x)
            by = y - bubble_height

            c.setFillColor(LIGHT_GRAY)
            c.setStrokeColor(HexColor("#d1d5db"))
            c.setLineWidth(1)
            c.roundRect(bx, by, bubble_width, bubble_height, 8, fill=1, stroke=1)

            c.setFillColor(BRAND_DARK)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(bx + bubble_width / 2, by + 68, account["account_type"])
            c.setFont("Helvetica", 9)
            c.drawCentredString(bx + bubble_width / 2, by + 52, f"...{account['last4']}")
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(bx + bubble_width / 2, by + 35, format_currency(account.get("current_balance", 0)))
            cash_balance = account.get("cash_balance", 0) or 0
            if cash_balance > 0:
                c.setFont("Helvetica", 9)
                c.setFillColor(HexColor("#047857"))
                c.drawCentredString(bx + bubble_width / 2, by + 18, f"Cash: {format_currency(cash_balance)}")

        y -= (bubble_height + gap_y)

    return y - 10
