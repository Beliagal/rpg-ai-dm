import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.character import Character
from app.models.message import Message

def test_narrate_endpoint_persists_chat_and_returns_payload(client: TestClient, db_session: Session):
    """
    Test de integración: Verifica que el endpoint /narrate recibe el mensaje,
    lo persiste, invoca al servicio de IA pasándole el historial, guarda la
    respuesta del DM y retorna el JSON correcto.
    """
    # 1. Preparar el estado inicial: Crear un personaje de prueba
    character = Character(
        name="Thorgar",
        race="Enano",
        char_class="Clérigo",
        stats={"strength": 14, "dexterity": 10, "constitution": 14, "intelligence": 10, "wisdom": 16, "charisma": 12},
        hp=10,
        max_hp=10,
        location="Catacumbas antiguas"
    )
    db_session.add(character)
    db_session.commit()
    db_session.refresh(character)

    # Payload simulado que enviará nuestro cliente frontend
    payload = {
        "character_id": character.id,
        "role": "user",
        "content": "Busco inscripciones ocultas en las paredes de la catacumba."
    }

    # Respuesta ficticia que debería generar el mock de Gemini
    mock_dm_response = "Tus dedos rozan runas polvorientas que emiten un leve brillo azulado. Una puerta de piedra cruje."

    # 2. Mockear la llamada HTTP externa de gemini_service
    with patch("app.main.gemini_service.generate_response", return_value=mock_dm_response) as mock_gemini:
        
        # Act: Ejecutar la petición HTTP al servidor de pruebas FastAPI
        response = client.post("/narrate", json=payload)
        
        # Assert: Validar la respuesta de la API
        assert response.status_code == 200
        assert response.json() == {"response": mock_dm_response}
        
        # Verificar que el servicio de IA fue invocado con los parámetros normalizados
        mock_gemini.assert_called_once()
        args, _ = mock_gemini.call_args
        # El primer argumento es context_instruction, validamos que incluya datos del personaje
        assert "Thorgar" in args[0]
        assert "Catacumbas antiguas" in args[0]

    # 3. Assert: Verificar la persistencia real en la base de datos
    messages_in_db = db_session.query(Message).filter(Message.character_id == character.id).order_by(Message.created_at.asc()).all()
    
    # Deben existir exactamente 2 mensajes (el del usuario y el del asistente)
    assert len(messages_in_db) == 2
    
    # Validar el mensaje del usuario
    assert messages_in_db[0].role == "user"
    assert messages_in_db[0].content == "Busco inscripciones ocultas en las paredes de la catacumba."
    
    # Validar el mensaje guardado de la IA
    assert messages_in_db[1].role == "assistant"
    assert messages_in_db[1].content == mock_dm_response


def test_narrate_endpoint_returns_404_if_character_not_found(client: TestClient):
    """Verifica que el sistema aborta de forma segura con un 404 si el personaje no existe."""
    payload = {
        "character_id": 9999,  # ID inexistente
        "role": "user",
        "content": "Hola"
    }
    
    response = client.post("/narrate", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Personaje no encontrado"


def test_narrate_endpoint_handles_ia_service_errors(client: TestClient, db_session: Session):
    """Verifica que si el servicio de IA reporta un fallo, la API responde con un error 502."""
    character = Character(
        name="Eldrin", race="Elfo", char_class="Mago",
        stats={"strength": 8, "dexterity": 14, "constitution": 12, "intelligence": 16, "wisdom": 12, "charisma": 10},
        hp=8, max_hp=8
    )
    db_session.add(character)
    db_session.commit()
    db_session.refresh(character)

    payload = {
        "character_id": character.id,
        "role": "user",
        "content": "Lanzo un conjuro de luz."
    }

    # Forzar al mock a devolver una cadena que el backend interpreta como fallo del servicio
    with patch("app.main.gemini_service.generate_response", return_value="Error de narración (Status 500)"):
        response = client.post("/narrate", json=payload)
        assert response.status_code == 502
        assert "Error de" in response.json()["detail"]