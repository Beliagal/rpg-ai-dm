from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


def test_api_health_check(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_character_flow(client: TestClient):
    payload = {"name": "Arthor", "race": "Humano", "char_class": "Guerrero"}
    create_response = client.post("/characters/", json=payload)

    assert create_response.status_code == 201
    char_data = create_response.json()
    assert char_data["name"] == "Arthor"

    char_id = char_data["id"]
    get_response = client.get(f"/characters/{char_id}")
    assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_roll_endpoint_integration(client: TestClient):
    """
    Verifica que las acciones que implican mecánicas de dados se procesen correctamente
    a través del flujo unificado del chat, sin endpoints huérfanos.
    """
    mock_ai_response = {
        "narrative": "Intentas forzar la puerta oxidada usando tu fuerza bruta. El metal cede.",
        "hp_change": None,
        "inventory_changes": [],
        "spell_slots_changes": {},
        "condition_changes": [],
        "location_change": None,
    }

    mock_async_method = AsyncMock(return_value=mock_ai_response)

    payload = {"name": "Shadow", "race": "Mediano", "char_class": "Pícaro"}
    create_response = client.post("/characters/", json=payload)
    char_id = create_response.json()["id"]

    turn_payload = {
        "character_id": char_id,
        "player_action": "Intento hacer una tirada de atletismo para derribar la puerta.",
    }

    with patch(
        "app.services.local_ai_service.local_ai_service.generate_structured_response",
        mock_async_method,
    ):
        response = client.post("/api/chat/turn", json=turn_payload)
        assert response.status_code == 200
        assert response.json()["narrative"] == mock_ai_response["narrative"]
