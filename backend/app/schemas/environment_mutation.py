from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class EnvironmentMutationSchema(BaseModel):
    """
    Define los cambios en el entorno y la ubicación del personaje 
    calculados por el DM tras la acción del jugador.
    """
    new_location: Optional[str] = Field(
        None, 
        description="El nombre de la nueva localización si el personaje se ha desplazado (ej. 'Sótano de la Taberna')."
    )
    world_flags: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Flags de estado modificados en la escena actual. Ej: {'cofre_madera_abierto': True, 'trampa_fuego_activa': False}"
    )