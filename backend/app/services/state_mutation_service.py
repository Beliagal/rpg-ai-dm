import logging
from sqlalchemy.orm import Session
from app.models.character import Character
from app.schemas.ai_responses import HpMutationSchema
from app.schemas.inventory_mutation import InventoryMutationListSchema
from sqlalchemy.orm.attributes import flag_modified
from app.schemas.environment_mutation import EnvironmentMutationSchema

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
    
    def apply_inventory_mutations(self, character_id: int, inventory_mutations: InventoryMutationListSchema) -> Character:
        """
        Modifica el estado del inventario del personaje de forma transaccional.
        Suma o resta elementos basándose en las mutaciones calculadas por la IA.
        """
        if not inventory_mutations.mutations:
            return self.db.query(Character).filter(Character.id == character_id).first()

        char = self.db.query(Character).filter(Character.id == character_id).first()
        if not char:
            raise ValueError(f"Personaje con ID {character_id} no encontrado.")

        # Garantizamos que trabajamos con una lista mutable (Deep copy implícito por SQLAlchemy)
        current_inventory = list(char.inventory) if char.inventory else []

        for mutation in inventory_mutations.mutations:
            item_name_lower = mutation.name.strip().lower()
            
            # Buscar si el ítem ya existe en el inventario actual
            existing_item = None
            for item in current_inventory:
                if isinstance(item, dict) and item.get("name", "").strip().lower() == item_name_lower:
                    existing_item = item
                    break

            if mutation.action == "add":
                if existing_item:
                    # Si ya existe, acumulamos la cantidad
                    existing_item["quantity"] = existing_item.get("quantity", 1) + mutation.quantity
                else:
                    # Si es nuevo, lo construimos respetando el formato que espera tu propiedad armor_class
                    new_item = {
                        "name": mutation.name.strip(),
                        "quantity": mutation.quantity,
                        "type": mutation.type.lower() if mutation.type else "utility",
                        "equipped": False,
                        **mutation.properties
                    }
                    current_inventory.append(new_item)

            elif mutation.action == "remove":
                if existing_item:
                    current_qty = existing_item.get("quantity", 1)
                    new_qty = current_qty - mutation.quantity
                    if new_qty <= 0:
                        current_inventory.remove(existing_item)
                    else:
                        existing_item["quantity"] = new_qty
                # Si no existía el ítem a remover, se ignora de forma segura para evitar excepciones en mitad de la partida

        # Forzamos la actualización en el ORM reasignando la estructura modificada
        char.inventory = current_inventory
        
        # Notificamos explícitamente a SQLAlchemy que el JSON interno ha mutado
        flag_modified(char, "inventory")
        
        try:
            self.db.commit()
            self.db.refresh(char)
            return char
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Fallo crítico al persistir la mutación del inventario: {str(e)}")

    def apply_environment_mutations(self, character_id: int, env_mutation: EnvironmentMutationSchema) -> Character:
        """
        Actualiza de forma transaccional la ubicación del personaje y procesa
        las alteraciones del entorno provocadas en el turno.
        """
        if not env_mutation.new_location and not env_mutation.world_flags:
            return self.db.query(Character).filter(Character.id == character_id).first()

        char = self.db.query(Character).filter(Character.id == character_id).first()
        if not char:
            raise ValueError(f"Personaje con ID {character_id} no encontrado.")

        # Actualización de la localización física
        if env_mutation.new_location:
            new_loc_clean = env_mutation.new_location.strip()
            if new_loc_clean and char.location != new_loc_clean:
                char.location = new_loc_clean

        try:
            self.db.commit()
            self.db.refresh(char)
            return char
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Fallo crítico al persistir la mutación del entorno: {str(e)}")