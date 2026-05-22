from typing import List, Literal
from sqlalchemy.orm import Session
from app.models.message import Message
from app.models.character import Character

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def save_message(self, character_id: int, role: Literal["user", "assistant"], content: str) -> Message:
        """Persiste un nuevo mensaje en el historial del personaje."""
        message = Message(
            character_id=character_id, 
            role=role, 
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_history(self, character_id: int, limit: int = 10) -> List[Message]:
        """
        Recupera los últimos N mensajes del personaje para la ventana de contexto.
        Los extrae desde el más reciente para aplicar el límite, pero los devuelve 
        en orden cronológico (antiguo -> nuevo) para la lectura secuencial del LLM.
        """
        recent_messages = self.db.query(Message)\
            .filter(Message.character_id == character_id)\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .all()
        
        return recent_messages[::-1]