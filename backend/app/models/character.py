from sqlalchemy import Column, Integer, String, JSON
from app.core.database import Base

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)  # Corregido: un único envoltorio Column
    race = Column(String, nullable=False)
    char_class = Column(String, nullable=False)
    
    # Progreso y Recursos del SRD
    level = Column(Integer, default=1, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    hp = Column(Integer, nullable=False)
    max_hp = Column(Integer, nullable=False)
    gold = Column(Integer, default=10, nullable=False)
    location = Column(String, default="Taberna de la Sangre de Dragón")

    # Características Puras (Fuerza, Destreza, Constitución, Inteligencia, Sabiduría, Carisma)
    stats = Column(JSON, nullable=False)

    # Bloques Elásticos del SRD (Competencias, Condiciones e Inventario)
    proficiencies = Column(JSON, nullable=False)
    conditions = Column(JSON, nullable=False)
    spell_slots = Column(JSON, nullable=False)
    inventory = Column(JSON, nullable=False)

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
    def armor_class(self) -> int:
        """
        Calcula dinámicamente la Clase de Armadura (CA) según las reglas del SRD.
        Inspecciona el inventario en busca de armaduras equipadas.
        """
        dex_mod = (self.stats.get("dexterity", 10) - 10) // 2
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