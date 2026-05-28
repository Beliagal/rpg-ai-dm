from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.core.database import engine, Base, get_db
from app.models.character import Character
from app.models.message import Message  
from app.services.dice_service import dice_service
from app.services.chat_service import ChatService
from app.services.state_mutation_service import StateMutationService
from app.schemas.ai_responses import StateMutationResponseSchema

# Único servicio de IA habilitado (Local Offline)
from app.services.local_ai_service import local_ai_service

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
    version="0.5.0", 
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
    return {"status": "ok", "version": "0.5.0", "ai_engine": "local_ollama"}

# --- Endpoint de Narrativa con Automatización de Estado ---
@app.post("/narrate")
async def narrate(data: ChatMessage, db: Session = Depends(get_db)):
    try:
        chat_service = ChatService(db)
        mutation_service = StateMutationService(db)
        
        char = db.query(Character).filter(Character.id == data.character_id).first()
        if not char:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")

        # Lógica de persistencia e historial de chat
        chat_service.save_message(data.character_id, data.role, data.content)
        history = chat_service.get_history(data.character_id, limit=10)
        
        formatted_history = [{"role": msg.role, "parts": [{"text": msg.content}]} for msg in history]
        
        context_instruction = (
            f"Personaje Actual: {char.name} ({char.race} {char.char_class}). "
            f"Puntos de Vida: {char.hp}/{char.max_hp}. "
            f"Ubicación: {char.location}. "
            f"Inventario Actual: {char.inventory}."
        )
        
        # Consumo asíncrono de IA Local
        ai_result_dict = await local_ai_service.generate_structured_response(context_instruction, formatted_history)
        
        # Hidratación del diccionario a objeto Pydantic para mantener los atributos requeridos por StateMutationService
        ai_result = StateMutationResponseSchema.model_validate(ai_result_dict)
        
        # Inserción de lógica de mutaciones mediante los objetos validados
        if ai_result.hp_change:
            mutation_service.apply_hp_mutation(char.id, ai_result.hp_change)
            
        if ai_result.inventory_changes:
            mutation_service.apply_inventory_mutations(char.id, ai_result.inventory_changes)
            
        if ai_result.environment_changes:
            mutation_service.apply_environment_mutations(char.id, ai_result.environment_changes)
        
        if ai_result.narrative:
            chat_service.save_message(data.character_id, "assistant", ai_result.narrative)
            
        return {"response": ai_result.narrative}

    except Exception as e:
        import traceback
        print("🚨 ERROR CRÍTICO EN NARRATE:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoints auxiliares para compatibilidad ---
@app.post("/game/chat")
async def process_chat(request: ChatRequest, db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.id == request.character_id).first()
    if not char: 
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    context_instruction = f"Personaje: {char.name}. HP: {char.hp}/{char.max_hp}."
    
    ai_result_dict = await local_ai_service.generate_structured_response(context_instruction, request.history)
    ai_result = StateMutationResponseSchema.model_validate(ai_result_dict)
    
    return {"response": ai_result.narrative}

@app.post("/game/roll")
async def process_action_roll(request: ActionRollRequest, db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.id == request.character_id).first()
    if not char: 
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    
    roll_result = dice_service.resolve_d20_roll(char, request.target_name, request.force_advantage, request.force_disadvantage)
    context_instruction = f"Resultado de la tirada de dados d20 en el sistema: {roll_result['total']}."
    
    ai_result_dict = await local_ai_service.generate_structured_response(context_instruction, request.history)
    ai_result = StateMutationResponseSchema.model_validate(ai_result_dict)
    
    return {"roll_details": roll_result, "narrative": ai_result.narrative}

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