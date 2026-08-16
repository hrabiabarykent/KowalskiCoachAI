import pytest

@pytest.mark.asyncio
async def test_get_dictionaries(async_client):
    response = await async_client.get("/dictionaries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Bike" in data or "Run" in data

@pytest.mark.asyncio
async def test_setup_keys_and_availability(async_client):
    # 1. Sprawdzenie availability nieistniejącego użytkownika (404)
    res_404 = await async_client.get("/user/99/availability")
    assert res_404.status_code == 404

    # 2. Tworzenie użytkownika przez /setup-keys
    payload = {
        "user_id": 99,
        "intervals_api_key": "test_api_key_123",
        "intervals_id": "i999"
    }
    res_setup = await async_client.post("/setup-keys", json=payload)
    assert res_setup.status_code == 200
    assert res_setup.json() == {"status": "ok"}

    # 3. Pobranie availability dla utworzonego użytkownika
    res_avail = await async_client.get("/user/99/availability")
    assert res_avail.status_code == 200
    assert res_avail.json() == {}
