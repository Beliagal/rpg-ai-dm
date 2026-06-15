from unittest.mock import patch

import pytest
from app.models.character import Character
from app.models.message import Message
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_narrate_endpoint_persists_chat_and_returns_payload(
    client: TestClient, db_session: Session
):
    character = Character(
        name="Thorgar",
        race="Enano",
        char_class="Clérigo",
        stats={
            "strength": 14,
            "dexterity": 10,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 16,
            "charisma": 12,
        },
        hp=10,
        max_hp=10,
        location="Catacumbas antiguas",
        inventory=[],
        spell_slots={},
        conditions=[],
    )
    db_session.add(character)
    db_session.commit()
    db_session.refresh(character)

    # Payload adaptado al esquema de entrada 'PlayerTurnRequest' esperado por el Router
    payload = {
        "character_id": character.id,
        "player_action": "Busco inscripciones ocultas.",
    }

    # Mock estructurado idéntico al diccionario crudo que retorna local_ai_service.generate_structured_response
    mock_response_payload = {
        "narrative": "Tus dedos rozan runas polvorientas que emiten un leve brillo.",
        "hp_change": {
            "amount": -2,
            "reason": "Una pequeña descarga de energía mística de las runas protegidas",
        },
        "inventory_changes": [],
        "spell_slots_changes": {},
        "condition_changes": [],
        "location_change": None,
    }

    # Ruta de inyección corregida a la infraestructura de IA local
    with patch(
        "app.services.local_ai_service.local_ai_service.generate_structured_response",
        return_value=mock_response_payload,
    ) as mock_ai:
        response = client.post("/api/chat/turn", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Validar consistencia absoluta contra el contrato de datos del Frontend (GameTurnResponseSchema)
        assert data["narrative"] == mock_response_payload["narrative"]
        assert data["character_id"] == character.id
        assert data["hp_current"] == 8  # Refleja la mutación atómica del servicio
        assert data["hp_max"] == 10
        assert data["location"] == "Catacumbas antiguas"

    # Validar persistencia real de la mutación en la base de datos física del test
    db_session.refresh(character)
    assert character.hp == 8

    # El historial debe contener los mensajes cronológicos del flujo transaccional
    messages_in_db = (
        db_session.query(Message)
        .filter(Message.character_id == character.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    assert len(messages_in_db) == 2
    assert messages_in_db[0].content == "Busco inscripciones ocultas."
    assert messages_in_db[1].content == mock_response_payload["narrative"]


def test_narrate_endpoint_handles_ia_service_errors(
    client: TestClient, db_session: Session
):
    character = Character(
        name="Eldrin",
        race="Elfo",
        char_class="Mago",
        hp=8,
        max_hp=8,
        location="Torre Alta",
        stats={
            "strength": 8,
            "dexterity": 14,
            "constitution": 12,
            "intelligence": 16,
            "wisdom": 10,
            "charisma": 12,
        },
        inventory=[],
        spell_slots={},
        conditions=[],
    )
    db_session.add(character)
    db_session.commit()
    db_session.refresh(character)

    payload = {"character_id": character.id, "player_action": "Lanzo un conjuro."}

    # Payload de control de fallos emulado por el catch del servicio
    mock_error_payload = {
        "narrative": "El motor narrativo local ha sufrido un problema al procesar la acción. Por favor, intenta reformular tu comando.",
        "hp_change": None,
    }

    with patch(
        "app.services.local_ai_service.local_ai_service.generate_structured_response",
        return_value=mock_error_payload,
    ):
        response = client.post("/api/chat/turn", json=payload)

        assert response.status_code == 200
        assert response.json()["narrative"] == mock_error_payload["narrative"]
