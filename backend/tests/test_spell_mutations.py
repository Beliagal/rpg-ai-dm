import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.character import Character
from app.services.state_mutation_service import StateMutationService
from app.schemas.ai_responses import SpellMutationSchema

# Setup de la base de datos en memoria para pruebas aisladas
@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="mutation_service")
def fixture_mutation_service(db_session):
    return StateMutationService(db=db_session)

@pytest.fixture(name="magical_character")
def fixture_magical_character(db_session):
    """Crea un personaje con un bloque de slots estructurado según el SRD."""
    character = Character(
        name="Melf",
        race="High Elf",
        char_class="Wizard",
        hp=12,
        max_hp=12,
        stats={"strength": 8, "dexterity": 14, "constitution": 12, "intelligence": 16, "wisdom": 10, "charisma": 12},
        spell_slots={
            "1": {"current": 2, "max": 2},
            "2": {"current": 0, "max": 1}
        },
        inventory=[]
    )
    db_session.add(character)
    db_session.commit()
    db_session.refresh(character)
    return character


def test_apply_spell_usage_success(db_session, mutation_service, magical_character):
    """Caso Feliz: El personaje consume un slot disponible y se persiste el cambio."""
    # Act
    updated_char = mutation_service.apply_spell_usage(
        character_id=magical_character.id, 
        spell_level=1
    )

    # Assert
    assert updated_char.spell_slots["1"]["current"] == 1
    assert updated_char.spell_slots["1"]["max"] == 2
    
    # Forzar recarga desde la base de datos para asegurar la mutación JSON del ORM
    db_session.expire_all()
    char_from_db = db_session.get(Character, magical_character.id)
    assert char_from_db.spell_slots["1"]["current"] == 1


def test_apply_spell_usage_insufficient_slots(db_session, mutation_service, magical_character):
    """Caso Límite: Intento de consumir un slot a 0 levanta ValueError y hace rollback."""
    # Act & Assert
    with pytest.raises(ValueError, match="No quedan espacios de conjuro de nivel 2 disponibles"):
        mutation_service.apply_spell_usage(
            character_id=magical_character.id, 
            spell_level=2
        )

    # Verificar que el estado no ha cambiado tras el rollback
    db_session.expire_all()
    char_from_db = db_session.get(Character, magical_character.id)
    assert char_from_db.spell_slots["2"]["current"] == 0


def test_apply_spell_mutation_via_schema(db_session, mutation_service, magical_character):
    """Prueba la integración con el esquema que mapea la respuesta de la IA."""
    mutation_schema = SpellMutationSchema(level=1, name="Magic Missile")
    
    # Act
    updated_char = mutation_service.apply_spell_mutation(
        character_id=magical_character.id, 
        spell_mutation=mutation_schema
    )

    # Assert
    assert updated_char.spell_slots["1"]["current"] == 1


def test_apply_long_rest_restores_slots_and_hp(db_session, mutation_service, magical_character):
    """Mecánica SRD: Un descanso largo restaura por completo los slots y la vida."""
    # Forzar desgaste previo del personaje
    magical_character.hp = 2
    magical_character.spell_slots["1"]["current"] = 0
    db_session.commit()

    # Act
    updated_char = mutation_service.apply_long_rest(character_id=magical_character.id)

    # Assert
    assert updated_char.hp == updated_char.max_hp
    assert updated_char.spell_slots["1"]["current"] == updated_char.spell_slots["1"]["max"]
    assert updated_char.spell_slots["2"]["current"] == updated_char.spell_slots["2"]["max"]


def test_apply_spell_usage_invalid_character(mutation_service):
    """Prueba de robustez: Lanzar una excepción limpia si el ID del personaje no existe."""
    with pytest.raises(ValueError, match="Character with ID 999 not found in database"):
        mutation_service.apply_spell_usage(character_id=999, spell_level=1)