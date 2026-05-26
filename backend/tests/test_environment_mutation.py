import pytest
from app.models.character import Character
from app.schemas.environment_mutation import EnvironmentMutationSchema
from app.services.state_mutation_service import StateMutationService

def test_apply_environment_mutation_changes_location(db_session):
    """Verifica que el servicio actualice correctamente la localización del personaje."""
    # 1. Setup: Personaje en la localización por defecto
    char = Character(
        name="Tordek", race="Enano", char_class="Clérigo", 
        hp=12, max_hp=12, stats={"dexterity": 10}, 
        location="Taberna de la Sangre de Dragón"
    )
    db_session.add(char)
    db_session.commit()

    service = StateMutationService(db_session)
    mutation = EnvironmentMutationSchema(
        new_location="Sótano Olvidado",
        world_flags={"puerta_secreta_descubierta": True}
    )

    # 2. Ejecución
    updated_char = service.apply_environment_mutations(char.id, mutation)

    # 3. Aserciones
    assert updated_char.location == "Sótano Olvidado"

def test_apply_environment_mutation_ignores_empty_or_none(db_session):
    """Verifica que si la IA no envía cambios de localización, el estado permanezca intacto."""
    char = Character(
        name="Eberk", race="Enano", char_class="Paladín", 
        hp=14, max_hp=14, stats={"dexterity": 8}, 
        location="Cripta Ancestral"
    )
    db_session.add(char)
    db_session.commit()

    service = StateMutationService(db_session)
    mutation = EnvironmentMutationSchema(new_location=None, world_flags={})

    # 2. Ejecución
    updated_char = service.apply_environment_mutations(char.id, mutation)

    # 3. Aserciones
    assert updated_char.location == "Cripta Ancestral"