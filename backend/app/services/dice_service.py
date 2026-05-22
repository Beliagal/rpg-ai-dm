import random
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.character import Character

class DiceService:
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
        "engaño": "charisma",
        "intimidacion": "charisma",
        "persuasion": "charisma"
    }

    def roll_dice(self, faces: int) -> int:
        return random.randint(1, faces)

    def calculate_stat_modifier(self, score: int) -> int:
        return (score - 10) // 2

    def resolve_d20_roll(
        self, 
        character: "Character", 
        target_name: str, 
        force_advantage: bool = False, 
        force_disadvantage: bool = False
    ) -> Dict[str, Any]:
        target_clean = target_name.strip().lower()
        
        if target_clean in self.SKILL_TO_STAT_MAP:
            stat_key = self.SKILL_TO_STAT_MAP[target_clean]
            is_skill = True
        elif target_clean in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            stat_key = target_clean
            is_skill = False
        else:
            raise ValueError(f"El objetivo de tirada '{target_name}' no es una habilidad o estadística válida del SRD.")

        has_advantage = force_advantage
        has_disadvantage = force_disadvantage

        if isinstance(character.conditions, list):
            conditions_clean = [c.lower() for c in character.conditions]
            if "envenenado" in conditions_clean or "asustado" in conditions_clean:
                has_disadvantage = True

        if has_advantage and has_disadvantage:
            roll_type = "normal"
        elif has_advantage:
            roll_type = "advantage"
        elif has_disadvantage:
            roll_type = "disadvantage"
        else:
            roll_type = "normal"

        dice_1 = self.roll_dice(20)
        dice_2 = self.roll_dice(20) if roll_type != "normal" else None

        if roll_type == "normal":
            final_dice = dice_1
        elif roll_type == "advantage":
            final_dice = max(dice_1, dice_2)
        elif roll_type == "disadvantage":
            final_dice = min(dice_1, dice_2)

        character_stats = character.stats if isinstance(character.stats, dict) else {}
        stat_score = character_stats.get(stat_key, 10)
        stat_modifier = self.calculate_stat_modifier(stat_score)

        applied_proficiency_bonus = 0
        is_proficient = False
        
        if is_skill and isinstance(character.proficiencies, dict):
            skills_list = character.proficiencies.get("skills", [])
            if target_clean in [s.lower() for s in skills_list]:
                applied_proficiency_bonus = getattr(character, "proficiency_bonus", 0)
                is_proficient = True
        elif not is_skill and isinstance(character.proficiencies, dict):
            saves_list = character.proficiencies.get("saving_throws", [])
            if stat_key in [s.lower() for s in saves_list]:
                applied_proficiency_bonus = getattr(character, "proficiency_bonus", 0)
                is_proficient = True

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

dice_service = DiceService()