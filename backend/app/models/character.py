from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    race = Column(String, nullable=False)
    char_class = Column(String, nullable=False)
    
    # Progreso y Recursos del SRD
    level = Column(Integer, default=1, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    hp = Column(Integer, nullable=False)
    max_hp = Column(Integer, nullable=False)
    gold = Column(Integer, default=10, nullable=False)
    location = Column(String, default="Taberna de la Sangre de Dragón")

    # Características Puras
    stats = Column(JSON, nullable=False)

    # Bloques Elásticos del SRD
    proficiencies = Column(JSON, default=dict, nullable=False)
    conditions = Column(JSON, default=list, nullable=False)
    spell_slots = Column(JSON, default=dict, nullable=False)
    inventory = Column(JSON, default=list, nullable=False)

    # Relación para persistencia de historial
    messages = relationship(
        "Message", 
        back_populates="character", 
        cascade="all, delete-orphan",
        lazy="select"
    )

    @property
    def proficiency_bonus(self) -> int:
        """Calcula el Bonificador de Competencia (BC) oficial que escala según el nivel."""
        if self.level <= 4:
            return 2
        elif self.level <= 8:
            return 3
        elif self.level <= 12:
            return 4
        elif self.level <= 16:
            return 5
        return 6

    @property
    def modifiers(self) -> dict[str, int]:
        """Calcula dinámicamente los modificadores de todas las características."""
        base_stats = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        return {
            stat: (self.stats.get(stat, 10) - 10) // 2 
            for stat in base_stats
        }

    @property
    def armor_class(self) -> int:
        """
        Calcula dinámicamente la Clase de Armadura (CA) según las reglas del SRD.
        Inspecciona el inventario en busca de armaduras equipadas.
        """
        dex_mod = self.modifiers.get("dexterity", 0)
        base_ca = 10 + dex_mod
        has_shield = False

        if isinstance(self.inventory, list):
            for item in self.inventory:
                if not isinstance(item, dict) or not item.get("equipped", False):
                    continue
                
                item_type = item.get("type", "").lower()
                if item_type == "shield":
                    has_shield = True
                elif item_type == "light_armor":
                    base_ca = item.get("ac_base", 11) + dex_mod
                elif item_type == "medium_armor":
                    base_ca = item.get("ac_base", 13) + min(dex_mod, 2)
                elif item_type == "heavy_armor":
                    base_ca = item.get("ac_base", 16)

        if has_shield:
            base_ca += 2

        return base_ca

    @property
    def carrying_capacity(self) -> float:
        """Capacidad de carga máxima reglamentaria del SRD (Fuerza x 15 libras)."""
        return self.stats.get("strength", 10) * 15.0

    @property
    def current_weight(self) -> float:
        """Calcula el peso total del inventario actual."""
        total_weight = 0.0
        if isinstance(self.inventory, list):
            for item in self.inventory:
                if isinstance(item, dict):
                    total_weight += item.get("weight", 0.0) * item.get("quantity", 1)
        return total_weight

    def has_spell_slots(self, spell_level: int) -> bool:
        """Verifica si el personaje tiene espacios de conjuro disponibles para un nivel."""
        level_str = str(spell_level)
        if not isinstance(self.spell_slots, dict) or level_str not in self.spell_slots:
            return False
        
        slot_data = self.spell_slots[level_str]
        if not isinstance(slot_data, dict):
            return False
            
        return slot_data.get("current", 0) > 0

    def consume_spell_slot(self, spell_level: int) -> None:
        """
        Decrementa un espacio de conjuro activo.
        
        :raises ValueError: Si el personaje no dispone de espacios libres de ese nivel.
        """
        level_str = str(spell_level)
        if not self.has_spell_slots(spell_level):
            raise ValueError(f"No quedan espacios de conjuro de nivel {spell_level} disponibles.")
        
        # Clonamos y mutamos el diccionario para asegurar la detección de cambios del ORM
        updated_slots = dict(self.spell_slots)
        updated_slots[level_str]["current"] -= 1
        self.spell_slots = updated_slots

    def evaluate_automatic_conditions(self) -> None:
        """
        Evalúa el estado del personaje para aplicar o remover condiciones automáticas
        del SRD (Inconsciente por HP, Exhausto/Sobrecargado por peso).
        """
        current_conditions = list(self.conditions) if self.conditions else []

        # Regla SRD: Estado Inconsciente a 0 HP
        if self.hp == 0:
            if "Unconscious" not in current_conditions:
                current_conditions.append("Unconscious")
        else:
            if "Unconscious" in current_conditions:
                current_conditions.remove("Unconscious")

        # Regla SRD Opcional/Variante: Encumbered (Sobrecargado)
        if self.current_weight > self.carrying_capacity:
            if "Encumbered" not in current_conditions:
                current_conditions.append("Encumbered")
        else:
            if "Encumbered" in current_conditions:
                current_conditions.remove("Encumbered")

        self.conditions = current_conditions