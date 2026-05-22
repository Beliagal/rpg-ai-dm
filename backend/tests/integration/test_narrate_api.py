import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.character import Character
from app.models.message import Message

def test_narrate_endpoint_persists_chat_and_returns_payload(client: TestClient, db_session: Session):
    character = Character(
        name="Thorgar", race="Enano", char_class="Clérigo",
        stats={"strength": 14, "dexterity": 10, "constitution": 14, "intelligence": 10, "wisdom": 16, "charisma": 12},
        hp=10, max_hp=10, location="Catacumbas antiguas"
    )
    db_session.add(character)
    db_session.commit()
    db_session.refresh(character)

    payload = {"character_id": character.id, "role": "user", "content": "Busco inscripciones ocultas."}
    
    # Mockear el nuevo método estructurado devolviendo el formato de diccionario esperado
    mock_response_payload = {
        "narrative": "Tus dedos rozan runas polvorientas que emiten un leve brillo.",
        "hp_change": {"amount": -2, "reason": "Una pequeña descarga de energía mística de las runas protegidas"}
    }

    with patch("app.main.gemini_service.generate_structured_response", return_value=mock_response_payload) as mock_gemini:
        response = client.post("/narrate", json=payload)
        
        assert response.status_code == 200
        assert response.json() == {"response": mock_response_payload["narrative"]}
        mock_gemini.assert_called_once()

    # Validar que el daño se aplicó de forma automática en la DB (10 HP iniciales - 2 de daño = 8 HP)
    db_session.refresh(character)
    assert character.hp == 8

    # Deben existir el mensaje del usuario y la narrativa final en el historial de mensajes
    messages_in_db = db_session.query(Message).filter(Message.character_id == character.id).order_by(Message.created_at.asc()).all()
    assert len(messages_in_db) == 2
    assert messages_in_db[1].content == mock_response_payload["narrative"]

def test_narrate_endpoint_handles_ia_service_errors(client: TestClient, db_session: Session):
    character = Character(
        name="Eldrin", race="Elfo", char_class="Mago", 
        hp=8, max_hp=8,
        stats={"strength": 8, "dexterity": 14, "constitution": 12, "intelligence": 16, "wisdom": 10, "charisma": 12}
    )
    db_session.add(character)
    db_session.commit()
    db_session.refresh(character)

    payload = {"character_id": character.id, "role": "user", "content": "Lanzo un conjuro."}
    mock_error_payload = {"narrative": "Error de narración (Status 500)", "hp_change": None}

    with patch("app.main.gemini_service.generate_structured_response", return_value=mock_error_payload):
        response = client.post("/narrate", json=payload)
        assert response.status_code == 502