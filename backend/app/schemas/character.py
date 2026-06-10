from pydantic import BaseModel
from typing import Dict, List, Any

class CharacterStatusDashboardSchema(BaseModel):
    id: int
    name: str
    race: str
    char_class: str
    level: int
    xp: int
    gold: int
    hp: int
    max_hp: int
    status_percentage_hp: float
    armor_class: int
    proficiency_bonus: int
    location: str
    stats: Dict[str, int]
    modifiers: Dict[str, int]
    spell_slots: Dict[str, Dict[str, int]]
    conditions: List[str]
    current_weight: float
    carrying_capacity: float

    class Config:
        from_attributes = True