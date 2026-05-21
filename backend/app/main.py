from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.database import engine, Base, get_db
from app.models.character import Character
from app.services.gemini_service import gemini_service
from app.services.dice_service import dice_service

# Levantamiento automático de las tablas de la BD en caliente
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RPG AI Dungeon Master API", 
    description="Motor de Backend Desacoplado basado en reglas D&D 5e SRD 5.2.1",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# ESQUEMAS DE VALIDACIÓN (PYDANTIC DTOs)
# ==========================================

class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, example="Arthor")
    race: str = Field(..., example="Humano")
    char_class: str = Field(..., example="Guerrero")

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
    proficiencies: Dict[str, List[str]]
    conditions: List[str]
    spell_slots: Dict[str, Dict[str, int]]
    inventory: List[Dict[str, Any]]
    proficiency_bonus: int
    armor_class: int

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str = Field(..., example="Examino los alrededores buscando trampas.")
    character_id: Optional[int] = None
    history: List[dict] = []

class RollRequest(BaseModel):
    target: str = Field(..., example="arcanos", description="Habilidad o Característica a lanzar")
    advantage: bool = Field(False, description="Fuerza ventaja en el lanzamiento")
    disadvantage: bool = Field(False, description="Fuerza desventaja en el lanzamiento")
    history: List[dict] = Field([], description="Historial de mensajes para mantener el hilo narrativo")

# ==========================================
# ENDPOINTS / RUTAS DE LA API
# ==========================================

@app.get("/")
async def health_check():
    """Endpoint de control de estado del sistema."""
    return {
        "status": "online",
        "version": "0.3.0",
        "active_ai_model": gemini_service.model_id
    }

@app.post("/characters", response_model=CharacterResponse)
async def create_character(char_data: CharacterCreate, db: Session = Depends(get_db)):
    """Instancia un personaje en SQLite aplicando las reglas iniciales del SRD 5.2.1."""
    cls_lower = char_data.char_class.lower()

    if "guerrero" in cls_lower:
        base_stats = {"strength": 15, "dexterity": 13, "constitution": 14, "intelligence": 10, "wisdom": 12, "charisma": 8}
        hit_die_base = 10
        proficiencies = {"skills": ["atletismo", "intimidacion"], "saving_throws": ["strength", "constitution"]}
        spell_slots = {}
        initial_items = [
            {"name": "Cota de malla", "type": "heavy_armor", "ac_base": 16, "equipped": True},
            {"name": "Espada larga", "type": "weapon", "damage": "1d8", "equipped": True},
            {"name": "Escudo de madera", "type": "shield", "equipped": True}
        ]
    elif "mago" in cls_lower:
        base_stats = {"strength": 8, "dexterity": 14, "constitution": 12, "intelligence": 15, "wisdom": 13, "charisma": 10}
        hit_die_base = 6
        proficiencies = {"skills": ["arcanos", "investigar"], "saving_throws": ["intelligence", "wisdom"]}
        spell_slots = {"level_1": {"max": 2, "current": 2}}
        initial_items = [
            {"name": "Túnica de erudito", "type": "clothing", "ac_base": 10, "equipped": True},
            {"name": "Bastón arcano", "type": "weapon", "damage": "1d6", "equipped": True},
            {"name": "Libro de conjuros", "type": "item", "equipped": False}
        ]
    elif "pícaro" in cls_lower or "picaro" in cls_lower or "rogue" in cls_lower:
        base_stats = {"strength": 10, "dexterity": 15, "constitution": 12, "intelligence": 12, "wisdom": 10, "charisma": 14}
        hit_die_base = 8
        proficiencies = {"skills": ["sigilo", "acrobacias", "juego de manos", "percepcion"], "saving_throws": ["dexterity", "intelligence"]}
        spell_slots = {}
        initial_items = [
            {"name": "Armadura de cuero", "type": "light_armor", "ac_base": 11, "equipped": True},
            {"name": "Daga sutil", "type": "weapon", "damage": "1d4", "properties": ["finesse"], "equipped": True},
            {"name": "Herramientas de ladrón", "type": "item", "equipped": False}
        ]
    else:
        base_stats = {"strength": 12, "dexterity": 12, "constitution": 12, "intelligence": 12, "wisdom": 12, "charisma": 12}
        hit_die_base = 8
        proficiencies = {"skills": ["percepcion"], "saving_throws": ["constitution"]}
        spell_slots = {}
        initial_items = []

    con_mod = (base_stats["constitution"] - 10) // 2
    calculated_hp = hit_die_base + con_mod

    new_character = Character(
        name=char_data.name,
        race=char_data.race,
        char_class=char_data.char_class,
        level=1,
        xp=0,
        hp=calculated_hp,
        max_hp=calculated_hp,
        gold=15,
        location="Taberna de la Sangre de Dragón",
        stats=base_stats,
        proficiencies=proficiencies,
        conditions=[],
        spell_slots=spell_slots,
        inventory=initial_items
    )

    db.add(new_character)
    db.commit()
    db.refresh(new_character)
    return new_character

@app.get("/characters/{char_id}", response_model=CharacterResponse)
async def get_character(char_id: int, db: Session = Depends(get_db)):
    """Recupera la ficha de personaje con sus propiedades dinámicas calculadas en tiempo de ejecución."""
    char = db.query(Character).filter(Character.id == char_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")
    return char

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Endpoint del chat narrativo estándar con inyección sutil de metadatos."""
    context = ""
    if request.character_id:
        char = db.query(Character).filter(Character.id == request.character_id).first()
        if char:
            context = (
                f"[Contexto Jugador: {char.name}, {char.race} {char.char_class} | "
                f"Nivel: {char.level}, HP: {char.hp}/{char.max_hp}, CA: {char.armor_class}, BC: +{char.proficiency_bonus} | "
                f"Ubicación: {char.location} | "
                f"Estados Activos: {char.conditions or 'Ninguno'} | "
                f"Competencias: {char.proficiencies.get('skills', [])} | "
                f"Slots de Magia: {char.spell_slots or 'No posee'}]"
            )

    full_input = f"{context}\n{request.message}" if context else request.message
    response = gemini_service.generate_response(full_input, request.history)
    
    if "Error" in response:
        raise HTTPException(status_code=500, detail=response)
        
    return {"response": response}

@app.post("/characters/{char_id}/roll")
async def roll_endpoint(char_id: int, request: RollRequest, db: Session = Depends(get_db)):
    """
    Endpoint avanzado de resolución de dados. Computa el d20 según las reglas del SRD, 
    genera un prefijo de arbitraje e invoca la narrativa de Gemini para dictaminar las consecuencias.
    """
    # 1. Recuperar el estado del personaje en base de datos
    char = db.query(Character).filter(Character.id == char_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    # 2. Resolver la matemática de la tirada delegando en el DiceService
    roll_result = dice_service.resolve_d20_roll(
        character=char,
        target_name=request.target,
        force_advantage=request.advantage,
        force_disadvantage=request.disadvantage
    )

    # 3. Construir la directiva de sistema invisible para forzar una resolución coherente en la IA
    system_instruction = (
        f"[SISTEMA: El jugador {char.name} ha ejecutado una prueba de {roll_result['target'].upper()}. "
        f"Resultado del dado: {roll_result['dice_selected']} ({roll_result['roll_type']}). "
        f"Modificador de Característica ({roll_result['stat_used']}): +{roll_result['stat_modifier']}. "
        f"Bono Competencia aplicado: +{roll_result['proficiency_bonus_applied']}. "
        f"TOTAL COMPUTADO POR EL BACKEND: {roll_result['total']}. "
        f"Establece de forma implícita si este total supera la CD de la tarea según la escala del SRD "
        f"(Fácil=10, Media=15, Difícil=20). Narra detalladamente el desenlace físico en base a este total "
        f"y devuelve la palabra al jugador sin delegar nuevas tiradas inmediatamente.]"
    )

    # 4. Enviar el bloque a la IA junto con el historial para que mantenga el hilo
    ai_narrative = gemini_service.generate_response(system_instruction, request.history)

    if "Error" in ai_narrative:
        raise HTTPException(status_code=500, detail=ai_narrative)

    # 5. Retornar tanto la historia de la IA como el desglose numérico para el renderizado del Frontend
    return {
        "roll_details": {
            "target": roll_result["target"],
            "stat_used": roll_result["stat_used"],
            "roll_type": roll_result["roll_type"],
            "dice_raw": roll_result["dice_results"],
            "dice_selected": roll_result["dice_selected"],
            "modifier": roll_result["stat_modifier"],
            "proficiency_bonus": roll_result["proficiency_bonus_applied"],
            "total": roll_result["total"]
        },
        "response": ai_narrative
    }