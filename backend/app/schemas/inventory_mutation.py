from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

class ItemMutationSchema(BaseModel):
    """Define el impacto de la IA sobre un objeto específico del inventario."""
    action: Literal["add", "remove"] = Field(
        ..., 
        description="Determina si el objeto se añade al inventario o se sustrae de él."
    )
    name: str = Field(
        ..., 
        description="Nombre exacto del objeto (ej. 'Poción de curación ligera', 'Espada corta')."
    )
    quantity: int = Field(
        default=1, 
        ge=1, 
        description="Cantidad de unidades a alterar. Debe ser mayor o igual a 1."
    )
    # Metadatos elásticos por si la IA genera un ítem nuevo con propiedades mecánicas
    type: Optional[str] = Field(default="utility", description="Categoría: weapon, light_armor, heavy_armor, shield, potion, utility, etc.")
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Atributos específicos del objeto, ej: ac_base, damage_dice, etc."
    )

class InventoryMutationListSchema(BaseModel):
    """Contrato contenedor para permitir múltiples alteraciones de objetos en un solo turno."""
    mutations: List[ItemMutationSchema] = Field(default_factory=list)