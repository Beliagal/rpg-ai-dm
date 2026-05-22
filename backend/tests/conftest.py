import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.core.database import Base
from app.models.character import Character

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def mock_guerrero():
    return Character(
        id=1,
        name="Arthor",
        race="Humano",
        char_class="Guerrero",
        level=1,
        xp=0,
        hp=12,
        max_hp=12,
        gold=15,
        location="Taberna",
        stats={
            "strength": 16, "dexterity": 12, "constitution": 14, 
            "intelligence": 10, "wisdom": 10, "charisma": 12
        },
        proficiencies={
            "skills": ["atletismo", "intimidacion"], 
            "saving_throws": ["strength", "constitution"]
        },
        conditions=[],
        spell_slots={},
        inventory=[]
    )