import json
from typing import List, Literal, Dict, Any
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

    def get_history(self, character_id: int, limit: int = 12) -> List[Message]:
        """Recupera el historial cronológico del personaje adaptándolo al formato de OpenAI/Ollama."""
        recent_messages = self.db.query(Message)\
            .filter(Message.character_id == character_id)\
            .order_by(Message.created_at.desc())\
            .limit(limit)\
            .all()
        return recent_messages[::-1]

    def _build_context_instruction(self, character: Character) -> str:
        """Construye un string detallado con el estado matemático del personaje para el LLM."""
        return (
            f"Personaje Actual: {character.name} ({character.race} {character.char_class}, Nivel {character.level})\n"
            f"HP Actuales: {character.hp}/{character.max_hp} | Oro: {character.gold} po\n"
            f"Localización: {character.location}\n"
            f"Modificadores de Atributos: {json.dumps(character.modifiers)}\n"
            f"Condiciones Activas: {json.dumps(character.conditions)}\n"
            f"Espacios de Conjuro Disponibles: {json.dumps(character.spell_slots)}\n"
            f"Carga: {character.current_weight:.1f}/{character.carrying_capacity:.1f} lbs\n"
            f"Inventario Completo: {json.dumps(character.inventory)}"
        )

    async def process_player_turn(self, character_id: int, player_action: str) -> Dict[str, Any]:
        """Orquesta el turno completo del juego inyectando los servicios de manera perezosa (Lazy)."""
        from app.services.local_ai_service import local_ai_service
        from app.services.state_mutation_service import StateMutationService
        from app.services.dice_service import dice_service

        character = self.db.get(Character, character_id)
        if not character:
            raise ValueError(f"No se encontró el personaje con ID {character_id}")

        self.save_message(character_id=character.id, role="user", content=player_action)

        history_messages = [
            {"role": msg.role, "content": msg.content} 
            for msg in self.get_history(character.id)
        ]
        context_instruction = self._build_context_instruction(character)

        ai_response = await local_ai_service.generate_structured_response(
            context_instruction=context_instruction,
            history=history_messages
        )

        roll_intent = ai_response.get("roll_intent")
        if roll_intent and roll_intent.get("requires_roll"):
            target_name = roll_intent.get("roll_target")
            dc = roll_intent.get("dc", 15)
            
            try:
                roll_result = dice_service.resolve_d20_roll(character, target_name)
                total_roll = roll_result["total"]
                success = total_roll >= dc
                
                outcome_text = "ÉXITO" if success else "FRACASO"
                system_injection = (
                    f"\n[SISTEMA - RESOLUCIÓN DE DADOS REAL]\n"
                    f"El jugador intentó un chequeo de '{target_name}' contra una CD {dc}.\n"
                    f"Resultado del backend: {outcome_text} absoluto.\n"
                    f"Detalle matemático: {roll_result['dice_selected']} (en el dado) "
                    f"+ {roll_result['stat_modifier']} (mod) "
                    f"+ {roll_result['proficiency_bonus_applied']} (bono competencia) = Total: {total_roll}."
                )
                
                context_with_dice = f"{context_instruction}\n{system_injection}\nCRÍTICO: Narra el {outcome_text} del personaje basándote exclusivamente en estos dados."
                
                ai_response = await local_ai_service.generate_structured_response(
                    context_instruction=context_with_dice,
                    history=history_messages
                )
            except ValueError as ve:
                print(f"⚠️ Target de tirada inválido ignorado: {str(ve)}")

        # Instanciamos el servicio pasándole la sesión activa requerida por su constructor
        mutation_service = StateMutationService(self.db)
        mutation_service.apply_mutations(character.id, ai_response)
        
        self.db.refresh(character)
        self.save_message(character_id=character.id, role="assistant", content=ai_response["narrative"])

        return {
            "narrative": ai_response["narrative"],
            "character_id": character.id,
            "hp_current": character.hp,
            "hp_max": character.max_hp,
            "conditions": character.conditions,
            "location": character.location,
            "inventory": character.inventory,
            "spell_slots": character.spell_slots
        }