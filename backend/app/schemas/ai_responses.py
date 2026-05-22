from pydantic import BaseModel, Field
from typing import Optional

class HpMutationSchema(BaseModel):
    """
    Esquema que representa una alteración mecánica en los Puntos de Vida (HP) del personaje.
    """
    amount: int = Field(
        ..., 
        description="Cantidad exacta de puntos de vida a alterar. Debe ser un entero NEGATIVO para representar daño o un entero POSITIVO para representar curación."
    )
    reason: str = Field(
        ..., 
        description="Breve justificación mecánica u origen de la alteración dentro de la narrativa (ej. 'Ataque de trasgo', 'Trampa de flechas', 'Efecto de poción de curación')."
    )

class StateMutationResponseSchema(BaseModel):
    """
    Contrato estricto exigido a la API de Google Gemini. 
    Fuerza al modelo de lenguaje a separar la experiencia inmersiva del jugador de las mutaciones mecánicas de las reglas del SRD 5e.
    """
    narrative: str = Field(
        ..., 
        description="La respuesta inmersiva, descriptiva y en tercera persona del Dungeon Master dirigida al jugador. Sigue estrictamente el SYSTEM_PROMPT habitual."
    )
    hp_change: Optional[HpMutationSchema] = Field(
        None, 
        description="Bloque de mutación de salud. Se debe rellenar ÚNICAMENTE si la acción del jugador o el evento narrativo resulta en una alteración directa de sus puntos de vida actuales."
    )