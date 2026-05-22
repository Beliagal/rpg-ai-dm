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

# --- Esquema nuevo para persistencia ---
class ChatMessage(BaseModel):
    character_id: int
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)

# --- Esquemas originales para compatibilidad ---
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

# --- Ciclo de vida ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="RPG AI Dungeon Master API", 
    description="Motor de Backend con soporte para persistencia de historial",
    version="0.3.1",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoint de Control (Health Check) ---
@app.get("/")
def health_check():
    """Valida el estado operativo mínimo de la API para las suites de prueba."""
    return {"status": "ok", "version": "0.3.1"}

# --- Nuevo Endpoint de Narrativa (Persistente) ---
@app.post("/narrate")
async def narrate(data: ChatMessage, db: Session = Depends(get_db)):
    chat_service = ChatService(db)
    
    char = db.query(Character).filter(Character.id == data.character_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    # 1. Persistir el mensaje actual enviado por el jugador
    chat_service.save_message(data.character_id, data.role, data.content)
    
    # 2. Recuperar el historial con la ventana deslizante (incluye el mensaje actual)
    history = chat_service.get_history(data.character_id, limit=10)
    formatted_history = [{"role": msg.role, "parts": [{"text": msg.content}]} for msg in history]
    
    # 3. Construir instrucciones contextuales corregidas (char.char_class)
    context_instruction = f"Personaje Actual: {char.name} ({char.race} {char.char_class}). Puntos de Vida: {char.hp}/{char.max_hp}. Ubicación: {char.location}."
    
    # 4. Enviar a Gemini controlando excepciones externas
    ai_narrative = gemini_service.generate_response(context_instruction, formatted_history)
    
    if "Error" in ai_narrative or ai_narrative.startswith("Error de"):
        raise HTTPException(status_code=502, detail=ai_narrative)
    
    # 5. Guardar la respuesta generada por el DM en la base de datos
    chat_service.save_message(data.character_id, "assistant", ai_narrative)
    
    return {"response": ai_narrative}

# --- Endpoints originales (Preservados para compatibilidad del Frontend) ---
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
        name=char_data.name, 
        race=char_data.race, 
        char_class=char_data.char_class,
        stats={"strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 10, "wisdom": 10, "charisma": 10}, 
        hp=12, 
        max_hp=12
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