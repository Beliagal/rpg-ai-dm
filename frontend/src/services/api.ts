import { Character, ChatMessagePayload, NarrateResponse } from '@/types/rpg';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiService = {
  /**
   * Recupera la ficha completa de un personaje por su ID.
   */
  async getCharacter(characterId: number): Promise<Character> {
    const response = await fetch(`${API_BASE_URL}/characters/${characterId}`);
    if (!response.ok) {
      throw new Error(`Error al recuperar el personaje (${response.status})`);
    }
    return response.json();
  },

  /**
   * Envía la acción del jugador al Dungeon Master y recupera la narrativa estructurada.
   */
  async sendNarrativeAction(payload: ChatMessagePayload): Promise<NarrateResponse> {
    const response = await fetch(`${API_BASE_URL}/narrate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Error en el motor de narrativa (${response.status})`);
    }
    return response.json();
  }
};