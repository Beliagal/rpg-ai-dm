import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session

from app.models.character import Character
from app.services.chat_service import ChatService

pytestmark = pytest.mark.asyncio

@pytest.fixture(name="db_session")
def fixture_db_session():
    return MagicMock(spec=Session)

@pytest.fixture(name="mock_character")
def fixture_mock_character():
    character = MagicMock(spec=Character)
    character.id = 1
    character.name = "Regdar"
    character.race = "Human"
    character.char_class = "Fighter"
    character.level = 3
    character.hp = 20
    character.max_hp = 26
    character.gold = 150
    character.location = "Cripta Oscura"
    character.modifiers = {"strength": 3}
    character.conditions = []
    character.spell_slots = {}
    character.current_weight = 45.0
    character.carrying_capacity = 240.0
    character.inventory = []
    return character


async def test_process_player_turn_without_roll(db_session, mock_character):
    db_session.get.return_value = mock_character
    
    ai_mock_response = {
        "narrative": "Te sientas en la taberna a descansar.",
        "roll_intent": {"requires_roll": False, "roll_target": None, "dc": 15},
        "hp_change": None,
        "inventory_changes": None,
        "environment_changes": None,
        "spell_used": None
    }

    chat_service = ChatService(db_session)
    
    # Parcheamos los servicios en sus módulos originales, no en chat_service
    with patch("app.services.local_ai_service.local_ai_service.generate_structured_response", new_callable=AsyncMock) as mock_ai, \
         patch("app.services.state_mutation_service.StateMutationService.apply_mutations") as mock_mutations:
        
        mock_ai.return_value = ai_mock_response
        result = await chat_service.process_player_turn(character_id=1, player_action="Descanso.")
        
        assert result["narrative"] == ai_mock_response["narrative"]
        mock_mutations.assert_called_once_with(mock_character.id, ai_mock_response)


async def test_process_player_turn_with_successful_roll_interception(db_session, mock_character):
    db_session.get.return_value = mock_character
    
    first_ai_response = {
        "narrative": "Arremetes contra la puerta...",
        "roll_intent": {"requires_roll": True, "roll_target": "atletismo", "dc": 14},
        "hp_change": None,
        "inventory_changes": None,
        "environment_changes": None,
        "spell_used": None
    }
    
    second_ai_response = {
        "narrative": "La puerta cede ante tu fuerza letal.",
        "roll_intent": {"requires_roll": False, "roll_target": None, "dc": 14},
        "hp_change": None,
        "inventory_changes": None,
        "environment_changes": None,
        "spell_used": None
    }

    mock_roll_result = {
        "target": "atletismo",
        "stat_used": "strength",
        "roll_type": "normal",
        "dice_results": [11],
        "dice_selected": 11,
        "stat_modifier": 3,
        "proficiency_bonus_applied": 0,
        "is_proficient": False,
        "total": 14
    }

    chat_service = ChatService(db_session)
    
    # Parcheamos los servicios en sus módulos originales, no en chat_service
    with patch("app.services.local_ai_service.local_ai_service.generate_structured_response", new_callable=AsyncMock) as mock_ai, \
         patch("app.services.dice_service.dice_service.resolve_d20_roll") as mock_dice, \
         patch("app.services.state_mutation_service.StateMutationService.apply_mutations") as mock_mutations:
        
        mock_ai.side_effect = [first_ai_response, second_ai_response]
        mock_dice.return_value = mock_roll_result
        
        result = await chat_service.process_player_turn(character_id=1, player_action="Derribo la puerta.")
        
        assert mock_ai.call_count == 2
        mock_dice.assert_called_once_with(mock_character, "atletismo")
        mock_mutations.assert_called_once_with(mock_character.id, second_ai_response)
        assert result["narrative"] == "La puerta cede ante tu fuerza letal."