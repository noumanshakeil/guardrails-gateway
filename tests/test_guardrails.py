import pytest

@pytest.mark.asyncio
async def test_blocks_pii(client):
    r = await client.post("/api/check", json={"text": "Email user@example.com"})
    assert r.status_code == 200
    assert r.json()["allowed"] is False

@pytest.mark.asyncio
async def test_rule_crud(client):
    c = await client.post("/api/rules", json={"name": "sec", "kind": "regex", "pattern": "SECRET", "action": "block"})
    assert c.status_code == 200
    b = await client.post("/api/check", json={"text": "SECRET plan"})
    assert b.json()["allowed"] is False
