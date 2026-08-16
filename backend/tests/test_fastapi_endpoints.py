import pytest
from app.main import app

def test_fastapi_app_initialization():
    # Sprawdzenie czy aplikacja inicjalizuje się poprawnie
    assert app.title is not None

@pytest.mark.asyncio
async def test_evaluate_goal_404_handling(async_client):
    # Sprawdzenie czy nieistniejący cel zwraca 404
    response = await async_client.post("/evaluate-goal/99999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Cel nie istnieje"

@pytest.mark.asyncio
async def test_sota_passport_404_handling(async_client):
    # Sprawdzenie czy nieistniejący użytkownik zwraca 404
    response = await async_client.get("/sota-passport/99999999")
    assert response.status_code == 404

