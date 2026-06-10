import random
import unicodedata
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.character import Character

class DiceService:
    # Diccionario base mapeado de forma limpia (sin tildes y en minúsculas)
    # para garantizar coincidencias robustas con la IA o la UI.
    SKILL_TO_STAT_MAP = {
        "atletismo": "strength",
        "acrobacias": "dexterity",
        "juego de manos": "dexterity",
        "sigilo": "dexterity",
        "arcanos": "intelligence",
        "historia": "intelligence",
        "investigar": "intelligence",
        "naturaleza": "intelligence",
        "religion": "intelligence",
        "averiguar intenciones": "wisdom",
        "medicina": "wisdom",
        "percepcion": "wisdom",
        "perspicacia": "wisdom",
        "supervivencia": "wisdom",
        "actuacion": "charisma",
        "engano": "charisma",
        "intimidacion": "charisma",
        "persuasion": "charisma"
    }

    def _normalize_text(self, text: str) -> str:
        """Elimina acentos, espacios extra y convierte a minúsculas."""
        text_clean = text.strip().lower()
        # Remueve diacríticos (tildes) de forma estándar en Python
        return "".join(
            c for c in unicodedata.normalize('NFD', text_clean)
            if unicodedata.category(c) != 'Mn'
        )

    def roll_dice(self, faces: int) -> int:
        """Genera un número aleatorio simulando las caras de un dado."""
        return random.randint(1, faces)

    def resolve_d20_roll(
        self, 
        character: "Character", 
        target_name: str, 
        force_advantage: bool = False, 
        force_disadvantage: bool = False
    ) -> Dict[str, Any]:
        """
        Resuelve una tirada de d20 calculando de forma dinámica ventajas/desventajas
        por estados del SRD, modificadores de características y bonos de competencia.
        """
        target_clean = self._normalize_text(target_name)
        
        # Determinamos si es Check de Habilidad o Salvación/Atributo Puro
        if target_clean in self.SKILL_TO_STAT_MAP:
            stat_key = self.SKILL_TO_STAT_MAP[target_clean]
            is_skill = True
        elif target_clean in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            stat_key = target_clean
            is_skill = False
        else:
            raise ValueError(f"El objetivo de tirada '{target_name}' no es una habilidad o estadística válida del SRD.")

        # Gestión estructural de ventajas y desventajas
        has_advantage = force_advantage
        has_disadvantage = force_disadvantage

        # Soporte bilingüe para las condiciones mecánicas restrictivas de d20
        if isinstance(character.conditions, list):
            conditions_normalized = [self._normalize_text(str(c)) for c in character.conditions]
            disadvantage_triggers = ["envenenado", "poisoned", "asustado", "frightened"]
            
            if any(trigger in conditions_normalized for trigger in disadvantage_triggers):
                has_disadvantage = True

        # Resolver el tipo de tirada resultante
        if has_advantage and has_disadvantage:
            roll_type = "normal"
        elif has_advantage:
            roll_type = "advantage"
        elif has_disadvantage:
            roll_type = "disadvantage"
        else:
            roll_type = "normal"

        # Ejecución física de los dados
        dice_1 = self.roll_dice(20)
        dice_2 = self.roll_dice(20) if roll_type != "normal" else None

        if roll_type == "normal":
            final_dice = dice_1
        elif roll_type == "advantage":
            final_dice = max(dice_1, dice_2)
        elif roll_type == "disadvantage":
            final_dice = min(dice_1, dice_2)

        # FUENTE DE VERDAD: Extraemos el modificador directamente calculado por el modelo
        character_modifiers = character.modifiers if hasattr(character, "modifiers") else {}
        stat_modifier = character_modifiers.get(stat_key, 0)

        applied_proficiency_bonus = 0
        is_proficient = False
        
        # Evaluación de Competencias (Proficiencies)
        if isinstance(character.proficiencies, dict):
            if is_skill:
                skills_list = character.proficiencies.get("skills", [])
                skills_normalized = [self._normalize_text(s) for s in skills_list]
                if target_clean in skills_normalized:
                    applied_proficiency_bonus = character.proficiency_bonus
                    is_proficient = True
            else:
                saves_list = character.proficiencies.get("saving_throws", [])
                saves_normalized = [self._normalize_text(s) for s in saves_list]
                if stat_key in saves_normalized or target_clean in saves_normalized:
                    applied_proficiency_bonus = character.proficiency_bonus
                    is_proficient = True

        # Operación matemática final según las reglas SRD
        total = final_dice + stat_modifier + applied_proficiency_bonus

        return {
            "target": target_name,
            "stat_used": stat_key,
            "roll_type": roll_type,
            "dice_results": [dice_1, dice_2] if roll_type != "normal" else [dice_1],
            "dice_selected": final_dice,
            "stat_modifier": stat_modifier,
            "proficiency_bonus_applied": applied_proficiency_bonus,
            "is_proficient": is_proficient,
            "total": total
        }

# Instancia singleton para inyección en controladores/rutas
dice_service = DiceService()