import random
from typing import Dict, Any, Tuple
from app.models.character import Character

class DiceService:
    def __init__(self):
        # Mapeo oficial del SRD que vincula cada habilidad con su característica raíz
        self.SKILL_TO_STAT_MAP = {
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
            "engaño": "charisma",
            "intimidacion": "charisma",
            "persuasion": "charisma"
        }

    def roll_dice(self, faces: int) -> int:
        """Simula de forma pura el lanzamiento de un dado físico de N caras."""
        return random.randint(1, faces)

    def calculate_stat_modifier(self, score: int) -> int:
        """Aplica la fórmula matemática estricta del SRD: (Puntuación - 10) // 2."""
        return (score - 10) // 2

    def resolve_d20_roll(
        self, 
        character: Character, 
        target_name: str, 
        force_advantage: bool = False, 
        force_disadvantage: bool = False
    ) -> Dict[str, Any]:
        """
        Ejecuta y desglosa una prueba oficial de característica o habilidad con d20.
        Calcula modificadores, competencias y evalúa estados alterados en caliente.
        """
        target_clean = target_name.lower().strip()
        
        # 1. Determinar la característica raíz correspondiente
        if target_clean in self.SKILL_TO_STAT_MAP:
            stat_key = self.SKILL_TO_STAT_MAP[target_clean]
            is_skill = True
        else:
            # Si no está en el mapa de habilidades, se asume que es una tirada de característica pura
            stat_key = target_clean
            is_skill = False

        stat_score = character.stats.get(stat_key, 10)
        stat_modifier = self.calculate_stat_modifier(stat_score)

        # 2. Evaluar condiciones de la ficha para aplicar Desventaja nativa (Módulo Beta)
        conditions_clean = [c.lower() for c in character.conditions] if character.conditions else []
        
        # El estado Envenenado o Derribado imponen desventaja en tiradas de ataque/característica
        if "envenenado" in conditions_clean or "derribado" in conditions_clean:
            force_disadvantage = True

        # Evitar el solapamiento mutuo: si hay ventaja y desventaja a la vez, se anulan (regla del SRD)
        if force_advantage and force_disadvantage:
            force_advantage = False
            force_disadvantage = False

        # 3. Ejecutar la física de los dados d20
        dice_1 = self.roll_dice(20)
        dice_2 = self.roll_dice(20)
        
        if force_advantage:
            final_dice = max(dice_1, dice_2)
            roll_type = "ventaja"
        elif force_disadvantage:
            final_dice = min(dice_1, dice_2)
            roll_type = "desventaja"
        else:
            final_dice = dice_1
            roll_type = "normal"

        # 4. Verificar si aplica el Bonificador de Competencia (BC)
        applied_proficiency_bonus = 0
        is_proficient = False
        
        if is_skill and isinstance(character.proficiencies, dict):
            skills_list = character.proficiencies.get("skills", [])
            if target_clean in [s.lower() for s in skills_list]:
                applied_proficiency_bonus = character.proficiency_bonus
                is_proficient = True
        elif not is_skill and isinstance(character.proficiencies, dict):
            # Comprobación para Tiradas de Salvación puras si se requiriera en el futuro
            saves_list = character.proficiencies.get("saving_throws", [])
            if stat_key in [s.lower() for s in saves_list]:
                applied_proficiency_bonus = character.proficiency_bonus
                is_proficient = True

        # 5. Cómputo del resultado matemático final
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

# Instancia única del servicio expuesta para inyección limpia
dice_service = DiceService()