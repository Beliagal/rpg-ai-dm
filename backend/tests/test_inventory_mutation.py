import pytest
from app.models.character import Character
from app.schemas.inventory_mutation import InventoryMutationListSchema, ItemMutationSchema
from app.services.state_mutation_service import StateMutationService

def test_apply_inventory_mutation_add_new_item(db_session):
    """Verifica que añadir un ítem inexistente lo inserte correctamente en la lista JSON."""
    # 1. Setup: Crear personaje con inventario vacío
    char = Character(
        name="Regdar", race="Humano", char_class="Guerrero", 
        hp=10, max_hp=10, stats={"dexterity": 10}, inventory=[]
    )
    db_session.add(char)
    db_session.commit()

    service = StateMutationService(db_session)
    mutations = InventoryMutationListSchema(mutations=[
        ItemMutationSchema(action="add", name="Poción de curación", quantity=2, type="potion")
    ])

    # 2. Ejecución
    updated_char = service.apply_inventory_mutations(char.id, mutations)

    # 3. Aserciones
    assert len(updated_char.inventory) == 1
    assert updated_char.inventory[0]["name"] == "Poción de curación"
    assert updated_char.inventory[0]["quantity"] == 2
    assert updated_char.inventory[0]["equipped"] is False

def test_apply_inventory_mutation_add_existing_item(db_session):
    """Verifica que añadir un ítem que ya posee el personaje incremente su cantidad de forma acumulativa."""
    initial_inventory = [{"name": "Antorcha", "quantity": 3, "type": "utility", "equipped": False}]
    char = Character(
        name="Lidda", race="Mediana", char_class="Pícaro", 
        hp=8, max_hp=8, stats={"dexterity": 16}, inventory=initial_inventory
    )
    db_session.add(char)
    db_session.commit()

    service = StateMutationService(db_session)
    mutations = InventoryMutationListSchema(mutations=[
        ItemMutationSchema(action="add", name="Antorcha", quantity=5)
    ])

    # 2. Ejecución
    updated_char = service.apply_inventory_mutations(char.id, mutations)

    # 3. Aserciones
    assert len(updated_char.inventory) == 1
    assert updated_char.inventory[0]["quantity"] == 8

def test_apply_inventory_mutation_remove_partial_and_total(db_session):
    """Verifica la reducción de cantidades y la eliminación completa del objeto si llega a cero."""
    initial_inventory = [
        {"name": "Flecha", "quantity": 10, "type": "utility", "equipped": False},
        {"name": "Raciones", "quantity": 1, "type": "utility", "equipped": False}
    ]
    char = Character(
        name="Mialee", race="Elfo", char_class="Mago", 
        hp=6, max_hp=6, stats={"dexterity": 12}, inventory=initial_inventory
    )
    db_session.add(char)
    db_session.commit()

    service = StateMutationService(db_session)
    
    # Mutación compuesta: restar 4 flechas y restar 1 ración (debería borrar las raciones por completo)
    mutations = InventoryMutationListSchema(mutations=[
        ItemMutationSchema(action="remove", name="Flecha", quantity=4),
        ItemMutationSchema(action="remove", name="Raciones", quantity=1)
    ])

    # 2. Ejecución
    updated_char = service.apply_inventory_mutations(char.id, mutations)

    # 3. Aserciones
    assert len(updated_char.inventory) == 1  # Solo quedan las flechas
    assert updated_char.inventory[0]["name"] == "Flecha"
    assert updated_char.inventory[0]["quantity"] == 6