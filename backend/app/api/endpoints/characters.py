from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.character import Character
from app.schemas.character import CharacterStatusDashboardSchema

router = APIRouter()

@router.get("/{character_id}/dashboard", response_model=CharacterStatusDashboardSchema)
def get_character_dashboard_status(character_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un desglose en tiempo real y de solo lectura de las estadísticas, 
    propiedades calculadas y recursos del personaje para el Dashboard del Frontend.
    """
    character = db.get(Character, character_id)
    if not character:
        raise HTTPException(
            status_code=404, 
            detail=f"Character with ID {character_id} not found."
        )
    
    # Calcular porcentaje para la UI de manera segura
    status_percentage_hp = round((character.hp / character.max_hp) * 100, 2) if character.max_hp > 0 else 0.0

    return {
        "id": character.id,
        "name": character.name,
        "race": character.race,
        "char_class": character.char_class,
        "level": character.level,
        "xp": character.xp,
        "gold": character.gold,
        "hp": character.hp,
        "max_hp": character.max_hp,
        "status_percentage_hp": status_percentage_hp,
        "armor_class": character.armor_class,
        "proficiency_bonus": character.proficiency_bonus,
        "location": character.location,
        "stats": character.stats,
        "modifiers": character.modifiers,
        "spell_slots": character.spell_slots,
        "conditions": character.conditions,
        "current_weight": character.current_weight,
        "carrying_capacity": character.carrying_capacity
    }