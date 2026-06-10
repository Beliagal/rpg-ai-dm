import logging
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.character import Character
from app.schemas.ai_responses import HpMutationSchema, SpellMutationSchema
from app.schemas.inventory_mutation import InventoryMutationListSchema
from app.schemas.environment_mutation import EnvironmentMutationSchema

logger = logging.getLogger(__name__)

class StateMutationService:
    """
    Servicio de Capa de Aplicación encargado de la mutación e integridad del estado
    del personaje, forzando las reglas de juego del SRD 5e de manera transaccional.
    """
    def __init__(self, db: Session):
        self.db = db

    def _get_character(self, character_id: int) -> Character:
        """Recupera un personaje de forma limpia o lanza una excepción controlada."""
        char = self.db.query(Character).filter(Character.id == character_id).first()
        if not char:
            raise ValueError(f"Character with ID {character_id} not found in database.")
        return char

    def apply_hp_mutation(self, character_id: int, hp_mutation: HpMutationSchema) -> Character:
        """
        Modifica los Puntos de Vida (HP) actuales limitando por las cotas mecánicas [0, max_hp].
        Aplica reactivamente estados derivados como 'Unconscious'.
        """
        char = self._get_character(character_id)
        old_hp = char.hp
        
        new_hp = old_hp + hp_mutation.amount
        if new_hp > char.max_hp:
            new_hp = char.max_hp
        elif new_hp < 0:
            new_hp = 0

        char.hp = new_hp
        char.evaluate_automatic_conditions()
        
        flag_modified(char, "conditions")

        try:
            self.db.commit()
            self.db.refresh(char)
            
            mutation_type = "DAMAGE" if hp_mutation.amount < 0 else "HEAL"
            logger.info(
                f"🔮 [SRD MUTATION - {mutation_type}] {char.name} (ID: {character_id}): "
                f"HP {old_hp} -> {new_hp}/{char.max_hp}. Reason: {hp_mutation.reason}"
            )
            return char
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Fallo crítico al persistir mutación de HP: {str(e)}")

    def apply_inventory_mutations(self, character_id: int, inventory_mutations: InventoryMutationListSchema) -> Character:
        """
        Modifica el inventario calculando dinámicamente el peso y alterando 
        el estado de carga (Encumbered) si se superan los límites del SRD.
        """
        if not inventory_mutations.mutations:
            return self._get_character(character_id)

        char = self._get_character(character_id)
        current_inventory = list(char.inventory) if char.inventory else []

        for mutation in inventory_mutations.mutations:
            item_name_lower = mutation.name.strip().lower()
            existing_item = next(
                (item for item in current_inventory 
                 if isinstance(item, dict) and item.get("name", "").strip().lower() == item_name_lower),
                None
            )

            if mutation.action == "add":
                if existing_item:
                    existing_item["quantity"] = existing_item.get("quantity", 1) + mutation.quantity
                else:
                    new_item = {
                        "name": mutation.name.strip(),
                        "quantity": mutation.quantity,
                        "type": mutation.type.lower() if mutation.type else "utility",
                        "equipped": False,
                        "weight": float(mutation.properties.get("weight", 0.0)),
                        **mutation.properties
                    }
                    current_inventory.append(new_item)

            elif mutation.action == "remove":
                if existing_item:
                    new_qty = existing_item.get("quantity", 1) - mutation.quantity
                    if new_qty <= 0:
                        current_inventory.remove(existing_item)
                    else:
                        existing_item["quantity"] = new_qty

        char.inventory = current_inventory
        char.evaluate_automatic_conditions()
        
        flag_modified(char, "inventory")
        flag_modified(char, "conditions")

        try:
            self.db.commit()
            self.db.refresh(char)
            return char
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Fallo crítico al persistir mutación de inventario: {str(e)}")

    def apply_environment_mutations(self, character_id: int, env_mutation: EnvironmentMutationSchema) -> Character:
        """Actualiza de forma segura la localización del personaje en el mundo."""
        if not env_mutation.new_location:
            return self._get_character(character_id)

        char = self._get_character(character_id)
        new_loc_clean = env_mutation.new_location.strip()
        
        if new_loc_clean and char.location != new_loc_clean:
            char.location = new_loc_clean

        try:
            self.db.commit()
            self.db.refresh(char)
            return char
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Fallo crítico al persistir mutación de entorno: {str(e)}")

    def apply_long_rest(self, character_id: int) -> Character:
        """
        Ejecuta la mecánica oficial de Descanso Largo (Long Rest) del SRD:
        Restablece por completo la vida (HP) y recupera la totalidad de los espacios de conjuro (Spell Slots).
        """
        char = self._get_character(character_id)
        
        char.hp = char.max_hp
        
        slots_modified = False
        if char.spell_slots and isinstance(char.spell_slots, dict):
            updated_slots = {}
            for level, data in char.spell_slots.items():
                if isinstance(data, dict) and "max" in data:
                    updated_slots[level] = {
                        "current": data["max"],
                        "max": data["max"]
                    }
                    slots_modified = True
                else:
                    updated_slots[level] = data
            char.spell_slots = updated_slots

        char.evaluate_automatic_conditions()
        
        if slots_modified:
            flag_modified(char, "spell_slots")
        flag_modified(char, "conditions")

        try:
            self.db.commit()
            self.db.refresh(char)
            logger.info(f"🏕️ [SRD MECHANICS] {char.name} (ID: {character_id}) completó un Descanso Largo de forma exitosa.")
            return char
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Fallo crítico al ejecutar Descanso Largo: {str(e)}")
        
    def apply_spell_usage(self, character_id: int, spell_level: int) -> Character:
        """
        Valida y procesa el uso manual o por API de un espacio de conjuro.
        Esta operación es atómica: si no hay slots, la mutación no ocurre.
        """
        char = self._get_character(character_id)
        
        try:
            char.consume_spell_slot(spell_level)
            flag_modified(char, "spell_slots")
            
            self.db.commit()
            self.db.refresh(char)
            logger.info(f"✨ [SRD SPELL] {char.name} gastó un slot de nivel {spell_level}.")
            return char
            
        except ValueError as e:
            logger.warning(f"🚫 [SRD REJECTED] Intento ilegal de uso de hechizo: {str(e)}")
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Error inesperado procesando hechizo: {str(e)}")

    def apply_spell_mutation(self, character_id: int, spell_mutation: SpellMutationSchema) -> Character:
        """
        Procesa la mutación estructural mapeada directamente desde la respuesta JSON de la IA.
        """
        return self.apply_spell_usage(character_id, spell_mutation.level)
    
    def apply_mutations(self, character_id: int, ai_response: dict) -> Character:
        """
        Punto de entrada único y orquestador para procesar de forma secuencial 
        todas las mutaciones mecánicas devueltas por el motor de IA.
        """
        char = self._get_character(character_id)

        # 1. Mutación de Puntos de Vida (HP)
        hp_data = ai_response.get("hp_change")
        if hp_data:
            from app.schemas.ai_responses import HpMutationSchema
            # Si viene como dict crudo desde el LLM, lo cargamos en su esquema
            if isinstance(hp_data, dict):
                hp_data = HpMutationSchema.model_validate(hp_data)
            self.apply_hp_mutation(character_id, hp_data)

        # 2. Mutación de Inventario
        inv_data = ai_response.get("inventory_changes")
        if inv_data:
            from app.schemas.inventory_mutation import InventoryMutationListSchema
            if isinstance(inv_data, dict):
                inv_data = InventoryMutationListSchema.model_validate(inv_data)
            self.apply_inventory_mutations(character_id, inv_data)

        # 3. Mutación de Entorno (Localización)
        env_data = ai_response.get("environment_changes")
        if env_data:
            from app.schemas.environment_mutation import EnvironmentMutationSchema
            if isinstance(env_data, dict):
                env_data = EnvironmentMutationSchema.model_validate(env_data)
            self.apply_environment_mutations(character_id, env_data)

        # 4. Mutación de Espacios de Conjuro (Spell Slots)
        spell_data = ai_response.get("spell_used")
        if spell_data:
            from app.schemas.ai_responses import SpellMutationSchema
            if isinstance(spell_data, dict):
                spell_data = SpellMutationSchema.model_validate(spell_data)
            self.apply_spell_mutation(character_id, spell_data)

        return char