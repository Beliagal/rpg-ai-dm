import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.gemini_service import gemini_service

client = TestClient(app)

def test_narrate_endpoint_applies_all_mutations_successfully(monkeypatch):
    """
    Test de integración End-to-End. Verifica que el endpoint /narrate
    procesa en cascada y de forma segura las mutaciones de estado tras la respuesta de la IA.
    """
    # 1. SETUP: Crear el personaje a través de la API oficial para asegurar coherencia en DB
    char_payload = {
        "name": "Regdar",
        "race": "Humano",
        "char_class": "Guerrero"
    }
    create_response = client.post("/characters/", json=char_payload)
    assert create_response.status_code == 201
    character_id = create_response.json()["id"]

    # 2. Mockear la respuesta estructurada que devolvería GeminiService
    mock_response = {
        "narrative": "Abres el cofre viejo; una aguja envenenada te pincha el dedo, pero encuentras una gema reluciente y decides bajar por las escaleras hacia la cripta.",
        "hp_change": {"amount": -2, "reason": "Aguja envenenada"},
        "inventory_changes": {
            "mutations": [
                {"action": "add", "name": "Gema Reluciente", "quantity": 1}
            ]
        },
        "environment_changes": {
            "new_location": "Cripta Oscura",
            "world_flags": {"cofre_abierto": True}
        }
    }
    
    monkeypatch.setattr(
        gemini_service, 
        "generate_structured_response", 
        MagicMock(return_value=mock_response)
    )

    # 3. EJECUCIÓN: Consumir el endpoint de narrativa
    payload = {
        "character_id": character_id,
        "role": "user",
        "content": "Abro el cofre de madera del rincón."
    }
    response = client.post("/narrate", json=payload)

    # 4. ASERCIONES DE LA RESPUESTA HTTP
    assert response.status_code == 200
    assert response.json()["response"] == mock_response["narrative"]

    # 5. ASERCIONES DE PERSISTENCIA: Consultamos el estado final consolidado
    get_response = client.get(f"/characters/{character_id}")
    assert get_response.status_code == 200
    updated_char = get_response.json()

    # Comprobamos la mutación de HP (12 de base en el endpoint - 2 = 10 HP)
    assert updated_char["hp"] == 10
    
    # Comprobamos que el nuevo objeto se ha inyectado correctamente en el JSON del inventario
    items = [item["name"] for item in updated_char["inventory"] if "name" in item]
    assert "Gema Reluciente" in items

    # Comprobamos que el cambio geográfico se ha consolidado
    assert updated_char["location"] == "Cripta Oscura"