import pytest
from unittest.mock import patch

def test_api_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_and_get_character_flow(client):
    payload = {"name": "Arthor", "race": "Humano", "char_class": "Guerrero"}
    create_response = client.post("/characters/", json=payload)
    
    # Verificación de creación correcta
    assert create_response.status_code == 201 
    char_data = create_response.json()
    assert char_data["name"] == "Arthor"
    assert char_data["level"] == 1
    
    # Verificación de persistencia
    char_id = char_data["id"]
    get_response = client.get(f"/characters/{char_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Arthor"

@patch("app.main.gemini_service.generate_response")
def test_roll_endpoint_integration(mock_gemini, client):
    # Mock para aislar el test de latencias y consumos en la API de Gemini
    mock_gemini.return_value = "El DM narra que has tenido un gran éxito en tu acción."
    
    payload = {"name": "Shadow", "race": "Mediano", "char_class": "Pícaro"}
    create_response = client.post("/characters/", json=payload)
    assert create_response.status_code == 201
    
    char_id = create_response.json()["id"]

    roll_payload = {
        "character_id": char_id,
        "target_name": "atletismo"
    }
    
    roll_response = client.post("/game/roll", json=roll_payload)
    assert roll_response.status_code == 200
    
    result = roll_response.json()
    assert "roll_details" in result
    assert "narrative" in result
    assert result["roll_details"]["target"] == "atletismo"
    assert result["narrative"] == "El DM narra que has tenido un gran éxito en tu acción."