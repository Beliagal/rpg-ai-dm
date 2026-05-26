from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.core.database import engine, Base, get_db
from app.models.character import Character
from app.models.message import Message  
from app.services.gemini_service import gemini_service
from app.services.dice_service import dice_service
from app.services.chat_service import ChatService
from app.services.state_mutation_service import StateMutationService
from app.schemas.ai_responses import HpMutationSchema

# --- Esquemas de validación de entrada ---
class ChatMessage(BaseModel):
    character_id: int
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)

class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    race: str
    char_class: str

class CharacterResponse(BaseModel):
    id: int
    name: str
    race: str
    char_class: str
    level: int
    xp: int
    hp: int
    max_hp: int
    gold: int
    location: str
    stats: Dict[str, int]
    proficiencies: Dict[str, Any]
    conditions: List[str]
    spell_slots: Dict[str, Any]
    inventory: List[Dict[str, Any]]
    proficiency_bonus: int
    armor_class: int
    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    character_id: int
    message: str
    history: List[Dict[str, str]] = []

class ActionRollRequest(BaseModel):
    character_id: int
    target_name: str
    force_advantage: Optional[bool] = False
    force_disadvantage: Optional[bool] = False
    history: List[Dict[str, str]] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="RPG AI Dungeon Master API", 
    version="0.4.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "version": "0.4.0"}

# --- Endpoint de Narrativa con Automatización de Estado ---
@app.post("/narrate")
async def narrate(data: ChatMessage, db: Session = Depends(get_db)):
    chat_service = ChatService(db)
    mutation_service = StateMutationService(db)
    
    char = db.query(Character).filter(Character.id == data.character_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    # 1. Guardar de forma persistente la acción enviada por el jugador
    chat_service.save_message(data.character_id, data.role, data.content)
    
    # 2. Recuperar el historial bajo la regla de ventana deslizante
    history = chat_service.get_history(data.character_id, limit=10)
    formatted_history = [{"role": msg.role, "parts": [{"text": msg.content}]} for msg in history]
    
    # 3. Construir instrucciones del contexto incluyendo el inventario real para la IA
    context_instruction = (
        f"Personaje Actual: {char.name} ({char.race} {char.char_class}). "
        f"Puntos de Vida: {char.hp}/{char.max_hp}. "
        f"Ubicación: {char.location}. "
        f"Inventario Actual: {char.inventory}."
    )
    
    # 4. Consumir el motor de IA estructurado
    ai_result = gemini_service.generate_structured_response(context_instruction, formatted_history)
    ai_narrative = ai_result.get("narrative", "")
    hp_change_data = ai_result.get("hp_change")
    inventory_change_data = ai_result.get("inventory_changes")
    environment_change_data = ai_result.get("environment_changes")

    # Si la IA falló catastróficamente o devolvió un mensaje de error simulado
    if "Error" in ai_narrative or ai_narrative.startswith("Error de"):
        raise HTTPException(status_code=502, detail=ai_narrative)
    
    # 5. ORQUESTACIÓN TRANSACCIONAL EN CASCADA SEGURO (TRY/EXCEPT AISLADOS)
    
    # A. Mutación de Puntos de Vida (HP)
    if hp_change_data:
        try:
            hp_schema = HpMutationSchema(
                amount=hp_change_data["amount"],
                reason=hp_change_data["reason"]
            )
            mutation_service.apply_hp_mutation(character_id=data.character_id, hp_mutation=hp_schema)
        except Exception as mutation_error:
            print(f"❌ Error aplicando mutación de salud: {str(mutation_error)}")

    # B. Mutación de Inventario (Sincronizado con la firma real del servicio)
    if inventory_change_data and inventory_change_data.get("mutations"):
        try:
            from app.schemas.inventory_mutation import InventoryMutationListSchema
            inv_schema = InventoryMutationListSchema(**inventory_change_data)
            mutation_service.apply_inventory_mutations(character_id=data.character_id, inventory_mutations=inv_schema)
        except Exception as inv_error:
            print(f"❌ Error aplicando mutación de inventario: {str(inv_error)}")

    # C. Mutación de Entorno y Localización
    if environment_change_data:
        try:
            from app.schemas.environment_mutation import EnvironmentMutationSchema
            env_schema = EnvironmentMutationSchema(**environment_change_data)
            mutation_service.apply_environment_mutations(character_id=data.character_id, env_mutation=env_schema)
        except Exception as env_error:
            print(f"❌ Error aplicando mutación de entorno: {str(env_error)}")

    # 6. Persistir la narrativa final generada por el DM en el historial de chat
    chat_service.save_message(data.character_id, "assistant", ai_narrative)
    
    return {"response": ai_narrative}

# --- Endpoints heredados para compatibilidad del Frontend ---
@app.post("/game/chat")
def process_chat(request: ChatRequest, db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.id == request.character_id).first()
    if not char: 
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    context_instruction = f"Personaje: {char.name}. HP: {char.hp}/{char.max_hp}."
    ai_response = gemini_service.generate_response(context_instruction, request.history)
    return {"response": ai_response}

@app.post("/game/roll")
def process_action_roll(request: ActionRollRequest, db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.id == request.character_id).first()
    if not char: 
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    roll_result = dice_service.resolve_d20_roll(char, request.target_name, request.force_advantage, request.force_disadvantage)
    context_instruction = f"Resultado de la tirada de dados d20 en el sistema: {roll_result['total']}."
    ai_narrative = gemini_service.generate_response(context_instruction, request.history)
    
    return {"roll_details": roll_result, "narrative": ai_narrative}

@app.post("/characters/", response_model=CharacterResponse, status_code=201)
def create_character(char_data: CharacterCreate, db: Session = Depends(get_db)):
    db_char = Character(
        name=char_data.name, race=char_data.race, char_class=char_data.char_class,
        stats={"strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 10, "wisdom": 10, "charisma": 10}, 
        hp=12, max_hp=12
    )
    db.add(db_char)
    db.commit()
    db.refresh(db_char)
    return db_char

@app.get("/characters/{character_id}", response_model=CharacterResponse)
def get_character(character_id: int, db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.id == character_id).first()
    if not char: 
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    return char