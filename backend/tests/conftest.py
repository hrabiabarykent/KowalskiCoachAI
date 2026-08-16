import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from app.database import Base, get_db
from app.main import app

# Utworzenie bazy danych SQLite w pamięci na potrzeby testów
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Tworzy czystą bazę danych przed każdym testem i po nim czyści."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest_asyncio.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Zwraca asynchroniczny klient testowy FastAPI podmieniający bazy danych."""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_intervals_dataset():
    """Przykładowy zestaw danych z Intervals.icu."""
    return {
        "athlete": {
            "id": "i12345",
            "name": "Test Athlete",
            "icu_ftp": 280,
            "weight": 70.0,
            "sex": "M"
        },
        "wellness": [
            {
                "id": "2026-08-01",
                "restingHR": 50,
                "hrv": 65,
                "sleepQuality": 2,
                "ctl": 75.0,
                "atl": 80.0,
                "tsb": -5.0
            }
        ],
        "activities_year": [],
        "pc_run_42d": None,
        "pc_run_year": None,
        "pc_bike_42d": None,
        "pc_bike_year": None
    }
