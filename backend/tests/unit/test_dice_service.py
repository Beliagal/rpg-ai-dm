import pytest
from unittest.mock import patch
from app.services.dice_service import dice_service
from tests.fixtures import mock_guerrero

def test_calculate_stat_modifier():
    assert dice_service.calculate_stat_modifier(15) == 2
    assert dice_service.calculate_stat_modifier(13) == 1
    assert dice_service.calculate_stat_modifier(10) == 0
    assert dice_service.calculate_stat_modifier(8) == -1

@patch("app.services.dice_service.dice_service.roll_dice")
def test_resolve_d20_roll_normal_with_proficiency(mock_roll, mock_guerrero):
    mock_roll.return_value = 10
    result = dice_service.resolve_d20_roll(mock_guerrero, target_name="atletismo")
    assert result["dice_selected"] == 10
    assert result["total"] == 14

@patch("app.services.dice_service.dice_service.roll_dice")
def test_resolve_d20_roll_advantage(mock_roll, mock_guerrero):
    mock_roll.side_effect = [5, 15]
    result = dice_service.resolve_d20_roll(mock_guerrero, target_name="sigilo", force_advantage=True)
    assert result["dice_selected"] == 15

@patch("app.services.dice_service.dice_service.roll_dice")
def test_resolve_d20_roll_disadvantage_by_condition(mock_roll, mock_guerrero):
    mock_guerrero.conditions = ["Envenenado"]
    mock_roll.side_effect = [18, 4]
    result = dice_service.resolve_d20_roll(mock_guerrero, target_name="atletismo")
    assert result["dice_selected"] == 4