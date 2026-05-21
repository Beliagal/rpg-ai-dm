import pytest
from unittest.mock import patch
from tests.fixtures import client, db_session

def test_api_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_create_and_get_character_flow(client):
    payload = {"name": "Valeros", "race": "Elfo", "char_class": "Mago"}
    create_response = client.post("/characters", json=payload)
    assert create_response.status_code == 200
    char_id = create_response.json()["id"]
    
    get_response = client.get(f"/characters/{char_id}")
    assert get_response.status_code == 200

@patch("app.services.gemini_service.gemini_service.generate_response")
def test_roll_endpoint_integration(mock_gemini, client):
    mock_gemini.return_value = "Consigues descifrar las runas..."
    char_payload = {"name": "Shadow", "race": "Mediano", "char_class": "Pícaro"}
    char_id = client.post("/characters", json=char_payload).json()["id"]
    
    roll_payload = {"target": "sigilo", "advantage": False, "disadvantage": False, "history": []}
    response = client.post(f"/characters/{char_id}/roll", json=roll_payload)
    assert response.status_code == 200