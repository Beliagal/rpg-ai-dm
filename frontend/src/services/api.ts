import { Character } from '@/types/rpg';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Estructura exacta para los objetos del inventario
export interface InventoryItem {
  name: string;
  quantity: number;
}

// Estructura exacta para los espacios de conjuro (ej: { "1": 3, "2": 1 })
export type SpellSlots = Record<string, number>;

// Contrato estricto y seguro devuelto por el ChatService del backend
export interface GameTurnResponse {
  narrative: string;
  character_id: number;
  hp_current: number;
  hp_max: number;
  conditions: string[];
  location: string;
  inventory: InventoryItem[];
  spell_slots: SpellSlots;
}

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
   * Envía la acción narrativa del jugador al orquestador en dos tiempos del backend.
   * Retorna la narrativa del DM y el estado mutado del personaje de forma atómica.
   */
  async sendPlayerAction(characterId: number, playerAction: string): Promise<GameTurnResponse> {
    const response = await fetch(`${API_BASE_URL}/api/chat/turn`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        character_id: characterId,
        player_action: playerAction
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error en el turno de juego (${response.status})`);
    }
    return response.json();
  }
};