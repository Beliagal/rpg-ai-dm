import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importaciones corregidas desde la localización real en tu arquitectura
from app.main import app, get_db
from app.core.database import Base, engine as prod_engine
from app.models.character import Character  # Crucial para que Base registre el modelo

# Configuración del motor de pruebas (SQLite en memoria)
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Crea la estructura de tablas del ORM en la base de datos de pruebas
    antes de ejecutar la suite y la destruye al finalizar.
    """
    # Al haber importado 'Character' arriba, Base ya sabe qué tablas crear
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Proporciona una sesión de base de datos aislada y transaccional por cada test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """
    Sobrescribe la dependencia de base de datos en FastAPI e inyecta el TestClient.
    """
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def mock_guerrero():
    """
    Fixture de dominio que devuelve una instancia limpia de un Personaje
    para las pruebas unitarias del servicio de dados.
    """
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
            "strength": 16,
            "dexterity": 12,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 12
        },
        proficiencies={
            "skills": ["atletismo", "intimidacion"],
            "saving_throws": ["strength", "constitution"]
        },
        conditions=[],
        spell_slots={},
        inventory=[]
    )