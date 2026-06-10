import pytest
from unittest.mock import patch
from app.models.character import Character
from app.services.dice_service import dice_service

@pytest.fixture(name="standard_character")
def fixture_standard_character():
    """Crea un personaje con competencias y modificadores claros para predecir resultados."""
    return Character(
        name="Regdar",
        char_class="Fighter",
        level=3,  # Proficiency Bonus = +2
        hp=26,
        max_hp=26,
        stats={
            "strength": 16,      # Modificador: +3
            "dexterity": 12,     # Modificador: +1
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 8,         # Modificador: -1
            "charisma": 10
        },
        proficiencies={
            "skills": ["Atletismo", "Percepción"],
            "saving_throws": ["strength", "constitution"]
        },
        conditions=[],
        inventory=[]
    )


def test_resolve_d20_roll_skill_with_proficiency(standard_character):
    """Comprueba que una habilidad con competencia suma Modificador + Proficiency."""
    # Forzamos que el dado saque un 10 para hacer la matemática predecible:
    # 10 (dado) + 3 (Fuerza) + 2 (Competencia en Atletismo) = 15
    with patch.object(dice_service, 'roll_dice', return_value=10):
        result = dice_service.resolve_d20_roll(
            character=standard_character,
            target_name="atletismo"
        )
        
        assert result["stat_used"] == "strength"
        assert result["stat_modifier"] == 3
        assert result["proficiency_bonus_applied"] == 2
        assert result["is_proficient"] is True
        assert result["total"] == 15


def test_resolve_d20_roll_text_normalization(standard_character):
    """Verifica que tolera tildes y mayúsculas de la IA mapeando a la misma habilidad."""
    with patch.object(dice_service, 'roll_dice', return_value=10):
        # "Percepción" con tilde y mayúscula debe resolver a wisdom y aplicar competencia
        result = dice_service.resolve_d20_roll(
            character=standard_character,
            target_name="  Percepción  "
        )
        
        assert result["stat_used"] == "wisdom"
        assert result["stat_modifier"] == -1
        assert result["proficiency_bonus_applied"] == 2  # Regdar es competente en Percepción
        assert result["total"] == 11  # 10 - 1 + 2


def test_resolve_d20_roll_automatic_disadvantage_by_condition(standard_character):
    """Un personaje envenenado debe tirar con desventaja automáticamente."""
    standard_character.conditions = ["Envenenado"]
    
    # Simulamos dos tiradas de dados: un 18 y un 5. Al ser desventaja, debe elegir el 5.
    with patch.object(dice_service, 'roll_dice') as mock_roll:
        mock_roll.side_effect = [18, 5]
        
        result = dice_service.resolve_d20_roll(
            character=standard_character,
            target_name="dexterity"  # Atributo puro, sin competencia
        )
        
        assert result["roll_type"] == "disadvantage"
        assert result["dice_selected"] == 5
        assert result["stat_modifier"] == 1
        assert result["total"] == 6  # 5 + 1 + 0


def test_resolve_d20_roll_invalid_target(standard_character):
    """El sistema debe rechazar limpiamente cualquier habilidad inventada."""
    with pytest.raises(ValueError, match="no es una habilidad o estadística válida del SRD"):
        dice_service.resolve_d20_roll(
            character=standard_character,
            target_name="comerciar"
        )