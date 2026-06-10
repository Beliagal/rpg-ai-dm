from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.inventory_mutation import InventoryMutationListSchema
from app.schemas.environment_mutation import EnvironmentMutationSchema

class HpMutationSchema(BaseModel):
    """Representa una alteración mecánica en los Puntos de Vida (HP) del personaje."""
    amount: int = Field(
        ..., 
        description="Entero NEGATIVO para daño, POSITIVO para curación. Nunca 0."
    )
    reason: str = Field(
        ..., 
        description="Origen de la alteración (ej. 'Ataque de trasgo', 'Trampa de flechas')."
    )

class SpellMutationSchema(BaseModel):
    """Representa el uso de un recurso mágico según el SRD."""
    level: int = Field(..., ge=1, le=9, description="Nivel del espacio de conjuro (1 a 9).")
    name: str = Field(..., description="Nombre del conjuro lanzado.")

class RollIntentSchema(BaseModel):
    """
    Representa la intención de la IA de solicitar una resolución matemática al backend
    antes de proceder con una narrativa definitiva.
    """
    requires_roll: bool = Field(
        False,
        description="Establecer en true si la acción del jugador requiere un chequeo de habilidad o salvación del SRD."
    )
    roll_target: Optional[str] = Field(
        None,
        description="Nombre de la habilidad (ej. 'atletismo', 'sigilo') o estadística pura (ej. 'strength') requerida."
    )
    dc: Optional[int] = Field(
        15,
        description="Clase de Dificultad (CD / DC) asignada por el DM para este reto (por defecto 15)."
    )

class StateMutationResponseSchema(BaseModel):
    """
    Contrato estricto exigido al motor de IA Local (Ollama).
    Sustituye las suposiciones matemáticas del LLM por intenciones validadas por el backend.
    """
    narrative: str = Field(
        ..., 
        description="La respuesta descriptiva en tercera persona del DM. Si 'roll_intent.requires_roll' es true, este campo debe contener una breve descripción del preámbulo o de la tensión previa a lanzar los dados."
    )
    roll_intent: Optional[RollIntentSchema] = Field(
        None,
        description="Bloque de solicitud de dados. Rellenar si la acción requiere evaluar éxito o fracaso mecánico."
    )
    hp_change: Optional[HpMutationSchema] = Field(
        None, 
        description="Bloque de mutación de salud (daño/curación directa sin tirada previa)."
    )
    inventory_changes: Optional[InventoryMutationListSchema] = Field(
        None,
        description="Bloque de mutación de inventario (obtención o pérdida de objetos)."
    )
    environment_changes: Optional[EnvironmentMutationSchema] = Field(
        None,
        description="Bloque de mutación de entorno (cambio de localización geográfica)."
    )
    spell_used: Optional[SpellMutationSchema] = Field(
        None,
        description="Bloque de mutación mágica si se lanza un conjuro."
    )