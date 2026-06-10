from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.core.database import get_db  # Importación corregida de tu infraestructura real
from app.models.character import Character
from app.services.chat_service import ChatService
from app.services.state_mutation_service import StateMutationService
from app.services.local_ai_service import local_ai_service
from app.schemas.ai_responses import StateMutationResponseSchema

router = APIRouter(prefix="/api/chat", tags=["Game Chat"])

# --- Esquemas de validación exclusivos del flujo del Chat ---
class PlayerTurnRequest(BaseModel):
    character_id: int = Field(..., description="ID del personaje que realiza la acción")
    player_action: str = Field(..., min_length=1, description="Texto narrativo con la acción del jugador")

class InventoryItemSchema(BaseModel):
    name: str
    quantity: int

class GameTurnResponseSchema(BaseModel):
    narrative: str
    character_id: int
    hp_current: int
    hp_max: int
    conditions: List[str]
    location: str
    inventory: List[InventoryItemSchema]
    spell_slots: Dict[str, int]


@router.post("/turn", response_model=GameTurnResponseSchema, status_code=status.HTTP_200_OK)
async def handle_player_turn(payload: PlayerTurnRequest, db: Session = Depends(get_db)):
    """
    Endpoint atómico y desacoplado. Procesa la acción del jugador, aplica mutaciones
    a través del StateMutationService y retorna el estado unificado a la UI.
    """
    try:
        chat_service = ChatService(db)
        mutation_service = StateMutationService(db)
        
        char = db.query(Character).filter(Character.id == payload.character_id).first()
        if not char:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")

        # 1. Registrar acción del jugador en el historial
        chat_service.save_message(payload.character_id, "user", payload.player_action)
        history = chat_service.get_history(payload.character_id, limit=10)
        
        formatted_history = [{"role": msg.role, "parts": [{"text": msg.content}]} for msg in history]
        
        context_instruction = (
            f"Personaje Actual: {char.name} ({char.race} {char.char_class}). "
            f"Puntos de Vida: {char.hp}/{char.max_hp}. "
            f"Ubicación: {char.location}. "
            f"Inventario Actual: {char.inventory}."
        )
        
        # 2. Generar respuesta estructurada con la IA Local
        ai_result_dict = await local_ai_service.generate_structured_response(context_instruction, formatted_history)
        
        # 3. Delegar mutaciones de forma segura en el método maestro del servicio de estado
        mutation_service.apply_mutations(char.id, ai_result_dict)
        
        # 4. Registrar la respuesta del narrador en el historial si existe
        narrative_text = ai_result_dict.get("narrative")
        if narrative_text:
            chat_service.save_message(payload.character_id, "assistant", narrative_text)
            
        # Forzar la sincronización del objeto de la base de datos
        db.refresh(char)

        # 5. Normalizar de forma segura la salida de los slots de conjuros (Nested -> Plano)
        flat_spell_slots: Dict[str, int] = {}
        if char.spell_slots and isinstance(char.spell_slots, dict):
            for level, slot_data in char.spell_slots.items():
                if isinstance(slot_data, dict):
                    flat_spell_slots[str(level)] = int(slot_data.get("current", 0))
                else:
                    flat_spell_slots[str(level)] = int(slot_data)

        return {
            "narrative": narrative_text or "El DM asiente en silencio.",
            "character_id": char.id,
            "hp_current": char.hp,
            "hp_max": char.max_hp,
            "conditions": char.conditions or [],
            "location": char.location or "Explorando...",
            "inventory": [{"name": item.get("name", "Objeto"), "quantity": item.get("quantity", 1)} for item in (char.inventory or [])],
            "spell_slots": flat_spell_slots
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        print("🚨 ERROR CRÍTICO EN EL CONTROLADOR DE TURNO ATÓMICO:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fallo en el motor del DM: {str(e)}")