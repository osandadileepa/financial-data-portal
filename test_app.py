import os
import sys
import json
import requests
import tempfile

# Ensure local packages are available
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".python-packages"))

BASE_URL = os.environ.get("APP_URL", "http://localhost:5000")


def print_section(title):
    print(f"\n{'=' * 60}")
    print(title)
    print(f"{'=' * 60}")


def assert_equal(actual, expected, message):
    if abs(actual - expected) > 0.001:
        raise AssertionError(f"{message}: expected {expected}, got {actual}")
    print(f"  ✓ {message}: {actual}")


def test_dashboard():
    print_section("Testing Dashboard API")
    r = requests.get(f"{BASE_URL}/api/clients")
    r.raise_for_status()
    clients = r.json()
    assert len(clients) == 2, f"Expected 2 sample clients, got {len(clients)}"
    print(f"  ✓ Found {len(clients)} sample clients")
    return clients


def test_client_profile(client_id):
    print_section(f"Testing Client Profile (ID: {client_id})")
    r = requests.get(f"{BASE_URL}/api/clients/{client_id}")
    r.raise_for_status()
    client = r.json()
    assert client["id"] == client_id
    assert "retirement_accounts" in client
    assert "non_retirement_accounts" in client
    print(f"  ✓ Loaded profile for {client['full_name']}")
    return client


def test_report_data(client_id):
    print_section(f"Testing Report Data Endpoint (ID: {client_id})")
    r = requests.get(f"{BASE_URL}/api/clients/{client_id}/report-data")
    r.raise_for_status()
    data = r.json()
    assert "client" in data
    assert "retirement_accounts" in data
    assert "non_retirement_accounts" in data
    assert "trusts" in data
    assert "liabilities" in data
    print(f"  ✓ Report data loaded with all sections")
    return data


def test_generate_report(client_id):
    print_section(f"Testing Report Generation (ID: {client_id})")

    # Use the same balances as the stored profile for predictable math
    data = requests.get(f"{BASE_URL}/api/clients/{client_id}/report-data").json()
    balances = {}
    for account in data["retirement_accounts"]:
        balances[f"retirement_{account['id']}"] = str(account["balance"])
    for account in data["non_retirement_accounts"]:
        balances[f"non_retirement_{account['id']}"] = str(account["balance"])
    for trust in data["trusts"]:
        balances[f"trust_zillow_{trust['id']}"] = str(trust["zillow_value"])
    for liability in data["liabilities"]:
        balances[f"liability_{liability['id']}"] = str(liability["balance"])
    balances["private_reserve_balance"] = str(data["client"]["private_reserve_target"])

    payload = {
        "quarter": "Q2",
        "year": 2026,
        "balances": balances,
    }

    r = requests.post(
        f"{BASE_URL}/api/clients/{client_id}/reports",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    r.raise_for_status()
    result = r.json()

    calc = result["calculations"]
    client1_ret = sum(
        a["balance"]
        for a in data["retirement_accounts"]
        if a["owner"] != "client2"
    )
    client2_ret = sum(
        a["balance"]
        for a in data["retirement_accounts"]
        if a["owner"] == "client2"
    )
    non_ret = sum(a["balance"] for a in data["non_retirement_accounts"])
    trust = sum(t["zillow_value"] for t in data["trusts"])
    liabilities = sum(l["balance"] for l in data["liabilities"])
    grand = client1_ret + client2_ret + non_ret + trust

    assert_equal(calc["client1_retirement_total"], client1_ret, "Client 1 retirement total")
    assert_equal(calc["client2_retirement_total"], client2_ret, "Client 2 retirement total")
    assert_equal(calc["non_retirement_total"], non_ret, "Non-retirement total")
    assert_equal(calc["trust_total"], trust, "Trust total")
    assert_equal(calc["grand_total"], grand, "Grand total")
    assert_equal(calc["liabilities_total"], liabilities, "Liabilities total (separate)")
    assert_equal(calc["excess"], data["inflow"] - data["outflow"], "Excess")
    assert_equal(
        calc["private_reserve_target"],
        data["client"]["private_reserve_target"],
        "Private reserve target",
    )

    print(f"  ✓ Report created with ID {result['report']['id']}")
    print(f"  ✓ SACS PDF: {result['report']['sacs_pdf_path']}")
    print(f"  ✓ TCC PDF: {result['report']['tcc_pdf_path']}")
    return result


def test_pdf_download(report_id):
    print_section(f"Testing PDF Download (Report ID: {report_id})")

    for pdf_type in ["sacs", "tcc"]:
        r = requests.get(f"{BASE_URL}/api/reports/{report_id}/download/{pdf_type}")
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(r.content)
            path = f.name
        size = os.path.getsize(path)
        assert size > 1000, f"{pdf_type.upper()} PDF is too small ({size} bytes)"
        print(f"  ✓ {pdf_type.upper()} PDF downloaded: {size} bytes")
        os.unlink(path)


def test_create_and_delete_client():
    print_section("Testing Client Creation and Deletion")

    payload = {
        "first_name": "Test",
        "last_name": "Client",
        "dob": "1980-01-15",
        "ssn_last4": "9999",
        "monthly_salary": "8000",
        "monthly_expenses": "5000",
        "retirement_accounts": [
            {"owner": "client1", "account_type": "401K", "last4": "9999", "balance": "100000", "cash_balance": "5000"}
        ],
        "non_retirement_accounts": [
            {"account_type": "brokerage", "last4": "8888", "balance": "50000", "cash_balance": "2500"}
        ],
        "trusts": [],
        "liabilities": [],
    }

    r = requests.post(
        f"{BASE_URL}/api/clients",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    r.raise_for_status()
    client = r.json()
    assert client["first_name"] == "Test"
    print(f"  ✓ Created test client ID {client['id']}")

    # Delete the test client
    r = requests.delete(f"{BASE_URL}/api/clients/{client['id']}")
    r.raise_for_status()
    print(f"  ✓ Deleted test client ID {client['id']}")


def main():
    print_section("AW Client Report Portal - API Tests")
    print(f"Base URL: {BASE_URL}")

    try:
        test_dashboard()
        clients = test_dashboard()
        for client in clients:
            test_client_profile(client["id"])
            test_report_data(client["id"])
            result = test_generate_report(client["id"])
            test_pdf_download(result["report"]["id"])
        test_create_and_delete_client()

        print_section("All tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
