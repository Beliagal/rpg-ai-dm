import logging
from sqlalchemy.orm import Session
from app.models.character import Character
from app.schemas.ai_responses import HpMutationSchema

logger = logging.getLogger(__name__)

class StateMutationService:
    """
    Servicio especializado en procesar de forma transaccional las mutaciones de estado
    del personaje dictadas por el motor de inteligencia artificial.
    """
    def __init__(self, db: Session):
        self.db = db

    def apply_hp_mutation(self, character_id: int, hp_mutation: HpMutationSchema) -> Character:
        """
        Modifica de forma segura los Puntos de Vida (HP) actuales de un personaje.
        Garantiza que el valor nunca sea menor que 0 ni supere el max_hp configurado,
        cumpliendo estrictamente las reglas mecánicas del SRD 5e.
        
        :param character_id: ID único del personaje en la base de datos.
        :param hp_mutation: Instancia validada de HpMutationSchema con amount y reason.
        :return: El objeto Character modificado y actualizado.
        :raises ValueError: Si el personaje no existe en la persistencia.
        """
        char = self.db.query(Character).filter(Character.id == character_id).first()
        if not char:
            raise ValueError(f"Character with ID {character_id} not found in database.")

        old_hp = char.hp
        # amount es negativo para daño y positivo para sanación
        new_hp = old_hp + hp_mutation.amount

        # Aplicar límites mecánicos de D&D 5e (0 <= hp <= max_hp)
        if new_hp > char.max_hp:
            new_hp = char.max_hp
        elif new_hp < 0:
            new_hp = 0

        char.hp = new_hp
        
        # Guardar los cambios en la base de datos
        self.db.commit()
        self.db.refresh(char)

        # Log del servidor para trazabilidad de auditoría mecánica
        mutation_type = "DAMAGE" if hp_mutation.amount < 0 else "HEAL"
        logger.info(
            f"🔮 [STATE MUTATION - {mutation_type}] {char.name} (ID: {character_id}): "
            f"HP changed from {old_hp} to {new_hp}/{char.max_hp}. Reason: {hp_mutation.reason}"
        )

        return char