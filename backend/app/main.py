from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.core.database import engine, Base, get_db
from app.models.character import Character
from app.services.dice_service import dice_service
from app.services.local_ai_service import local_ai_service

# IMPORTACIÓN DEL ROUTER DESACOPLADO
from app.api.chat import router as chat_router

# Esquemas remanentes de gestión de personajes (Se pueden desacoplar a app/api/characters.py en el futuro)
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

# REGISTRO LIMPIO DE RUTAS DESACOPLADAS
app.include_router(chat_router)

@app.get("/")
def health_check():
    return {"status": "ok", "version": "0.5.0", "ai_engine": "local_ollama"}

# --- Endpoints auxiliares de Personajes ---
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