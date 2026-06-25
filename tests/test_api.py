from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_dashboard_page(async_client):
    resp = await async_client.get("/")
    assert resp.status_code == 200
    assert b"AW Client Report Portal" in resp.content


@pytest.mark.asyncio
async def test_new_client_form(async_client):
    resp = await async_client.get("/client/new")
    assert resp.status_code == 200
    assert b"Add Client" in resp.content


@pytest.mark.asyncio
async def test_api_list_clients(async_client):
    resp = await async_client.get("/api/clients")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_api_create_client(async_client):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "dob": "1980-05-20",
        "ssn_last4": "1234",
        "monthly_salary": 10000,
        "monthly_expenses": 6000,
        "retirement_accounts": [
            {"owner": "client1", "account_type": "401K", "last4": "1111", "balance": 500000},
        ],
        "non_retirement_accounts": [
            {"account_type": "brokerage", "last4": "2222", "balance": 100000},
        ],
        "trusts": [],
        "liabilities": [],
    }
    resp = await async_client.post("/api/clients", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "Test"
    assert data["full_name"] == "Test User"
    assert len(data["retirement_accounts"]) == 1
    assert len(data["non_retirement_accounts"]) == 1


@pytest.mark.asyncio
async def test_api_get_client(async_client):
    resp = await async_client.get("/api/clients/1")
    assert resp.status_code == 404  # empty database, no seed in test


@pytest.mark.asyncio
async def test_404_returns_json(async_client):
    resp = await async_client.get("/api/clients/99999")
    assert resp.status_code == 404
    assert resp.json()["error"] == "Client not found"
