import pytest
from app.services.chat_service import ChatService
from app.models.message import Message

def test_save_message_persists_and_links_to_character(db_session, mock_guerrero):
    # Setup inicial: añadir el personaje al contexto de la BD
    db_session.add(mock_guerrero)
    db_session.commit()

    chat_service = ChatService(db_session)
    msg = chat_service.save_message(mock_guerrero.id, "user", "Observo el mapa de la pared.")

    # Verificaciones del modelo Message
    assert msg.id is not None
    assert msg.character_id == mock_guerrero.id
    assert msg.role == "user"
    assert msg.content == "Observo el mapa de la pared."

    # Verificación de la relación bidireccional Lazy Load en Character
    assert len(mock_guerrero.messages) == 1
    assert mock_guerrero.messages[0].content == "Observo el mapa de la pared."

def test_get_history_applies_sliding_window_limit(db_session, mock_guerrero):
    db_session.add(mock_guerrero)
    db_session.commit()

    chat_service = ChatService(db_session)

    # Inserción de 5 mensajes secuenciales
    for i in range(1, 6):
        chat_service.save_message(mock_guerrero.id, "user", f"Turno {i}")

    # Recuperación con ventana deslizante de tamaño 3
    history = chat_service.get_history(mock_guerrero.id, limit=3)

    assert len(history) == 3
    # Comprobar que los mensajes devueltos son los últimos y están en orden cronológico
    assert history[0].content == "Turno 3"
    assert history[1].content == "Turno 4"
    assert history[2].content == "Turno 5"

def test_cascade_delete_removes_messages_when_character_deleted(db_session, mock_guerrero):
    db_session.add(mock_guerrero)
    db_session.commit()

    chat_service = ChatService(db_session)
    chat_service.save_message(mock_guerrero.id, "assistant", "Un goblin salta de las sombras.")

    # Acción destructiva
    db_session.delete(mock_guerrero)
    db_session.commit()

    # Verificación de limpieza en base de datos
    messages_in_db = db_session.query(Message).count()
    assert messages_in_db == 0