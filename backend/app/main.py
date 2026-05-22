from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.core.database import engine, Base, get_db
from app.models.character import Character
from app.services.gemini_service import gemini_service
from app.services.dice_service import dice_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="RPG AI Dungeon Master API", 
    description="Motor de Backend Desacoplado basado en reglas D&D 5e SRD 5.2.1",
    version="0.3.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, json_schema_extra={"example": "Arthor"})
    race: str = Field(..., json_schema_extra={"example": "Humano"})
    char_class: str = Field(..., json_schema_extra={"example": "Guerrero"})

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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "RPG AI DM API running"}

@app.post("/characters/", response_model=CharacterResponse, status_code=201)
def create_character(char_data: CharacterCreate, db: Session = Depends(get_db)):
    db_char = Character(
        name=char_data.name,
        race=char_data.race,
        char_class=char_data.char_class,
        level=1,
        xp=0,
        hp=12,
        max_hp=12,
        gold=15,
        location="Taberna del Dragón Verde",
        stats={"strength": 14, "dexterity": 12, "constitution": 14, "intelligence": 10, "wisdom": 13, "charisma": 10},
        proficiencies={"skills": ["atletismo", "percepcion"], "saving_throws": ["strength", "constitution"]},
        conditions=[],
        spell_slots={"1": 0, "2": 0},
        inventory=[]
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

@app.post("/game/chat")
def process_chat(request: ChatRequest, db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.id == request.character_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    system_instruction = (
        f"Eres el Dungeon Master de una partida de D&D 5e. El jugador controla a {char.name}, "
        f"un {char.race} {char.char_class} de nivel {char.level}. "
        f"Ubicación actual: {char.location}. Estado de salud: {char.hp}/{char.max_hp} HP. "
        f"Condiciones actuales: {char.conditions}. Inventario: {char.inventory}. "
        f"Basa tus respuestas estrictamente en este contexto, mantén el tono de fantasía épica, "
        f"describe el entorno basándote en la entrada del usuario y finaliza dándole el turno de acción "
        f"al jugador de forma clara."
    )

    ai_response = gemini_service.generate_response(system_instruction, request.history)
    
    if "Error" in ai_response:
        raise HTTPException(status_code=500, detail=ai_response)
        
    return {"response": ai_response}

@app.post("/game/roll")
def process_action_roll(request: ActionRollRequest, db: Session = Depends(get_db)):
    char = db.query(Character).filter(Character.id == request.character_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    try:
        roll_result = dice_service.resolve_d20_roll(
            character=char,
            target_name=request.target_name,
            force_advantage=request.force_advantage,
            force_disadvantage=request.force_disadvantage
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    system_instruction = (
        f"Actúa como Dungeon Master. El jugador ha intentado realizar una acción basada en '{roll_result['target']}'. "
        f"El motor del backend ha determinado de manera absoluta e inapelable el siguiente resultado físico: "
        f"[Dados brutos lanzados: {roll_result['dice_results']} -> Dado final seleccionado: {roll_result['dice_selected']} bajo modalidad tipo '{roll_result['roll_type']}']. "
        f"Modificador de Característica ({roll_result['stat_used']}): +{roll_result['stat_modifier']}. "
        f"Bono Competencia aplicado: +{roll_result['proficiency_bonus_applied']}. "
        f"TOTAL COMPUTADO POR EL BACKEND: {roll_result['total']}. "
        f"Establece de forma implícita si este total supera la CD de la tarea según la escala del SRD "
        f"(Fácil=10, Media=15, Difícil=20). Narra detalladamente el desenlace físico en base a este total "
        f"y devuelve la palabra al jugador sin delegar nuevas tiradas inmediatamente."
    )

    ai_narrative = gemini_service.generate_response(system_instruction, request.history)

    if "Error" in ai_narrative:
        raise HTTPException(status_code=500, detail=ai_narrative)

    return {
        "roll_details": {
            "target": roll_result["target"],
            "stat_used": roll_result["stat_used"],
            "roll_type": roll_result["roll_type"],
            "dice_raw": roll_result["dice_results"],
            "dice_selected": roll_result["dice_selected"],
            "stat_modifier": roll_result["stat_modifier"],
            "proficiency_bonus_applied": roll_result["proficiency_bonus_applied"],
            "total": roll_result["total"]
        },
        "narrative": ai_narrative
    }