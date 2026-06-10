import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useGameSession } from './useGameSession';
import { apiService, GameTurnResponse } from '@/services/api';
import { Character } from '@/types/rpg';

// Tipado extendido local para reflejar el estado del personaje mutado con campos SRD
interface MutatedCharacter extends Character {
  conditions: string[];
  spell_slots: Record<string, number>;
}

// Mockear el servicio de API de forma explícita
vi.mock('@/services/api', () => ({
  apiService: {
    getCharacter: vi.fn(),
    sendPlayerAction: vi.fn(),
  },
}));

describe('useGameSession Hook', () => {
  const mockCharacterId = 1;

  const baseMockCharacter = {
    id: mockCharacterId,
    name: 'Regdar',
    race: 'Human',
    char_class: 'Fighter',
    hp: 20,
    max_hp: 26,
    location: 'Cripta Oscura',
    inventory: [
      { name: 'Espada Larga', quantity: 1, type: 'weapon', equipped: true },
      { name: 'Poción de Curación', quantity: 2, type: 'potion', equipped: false },
    ],
    stats: { strength: 16, dexterity: 12, constitution: 14, intelligence: 8, wisdom: 10, charisma: 10 }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiService.getCharacter).mockResolvedValue(baseMockCharacter as unknown as Character);
  });

  it('debería inicializar la sesión cargando el personaje correctamente', async () => {
    const { result } = renderHook(() => useGameSession(mockCharacterId));

    await act(async () => {
      await Promise.resolve();
    });

    expect(apiService.getCharacter).toHaveBeenCalledWith(mockCharacterId);
    expect(result.current.character).toEqual(baseMockCharacter);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('debería enviar una acción narrativa y reconciliar el estado mutado y el inventario', async () => {
    const { result } = renderHook(() => useGameSession(mockCharacterId));

    await act(async () => {
      await Promise.resolve();
    });

    const mockBackendResponse: GameTurnResponse = {
      narrative: 'Atacas al orco y tu espada brilla con fuerza. Recibes 5 de daño.',
      character_id: mockCharacterId,
      hp_current: 15,
      hp_max: 26,
      location: 'Cripta Oscura - Pasillo Norte',
      conditions: ['Prone'],
      spell_slots: { '1': 1 },
      inventory: [
        { name: 'Espada Larga', quantity: 1 },
        { name: 'Antorcha', quantity: 3 }
      ],
    };

    vi.mocked(apiService.sendPlayerAction).mockResolvedValue(mockBackendResponse);

    await act(async () => {
      await result.current.sendAction('Ataco con mi espada larga.');
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]).toMatchObject({ role: 'user', content: 'Ataco con mi espada larga.' });
    expect(result.current.messages[1]).toMatchObject({ role: 'assistant', content: mockBackendResponse.narrative });

    // Hacemos un cast seguro al tipo extendido MutatedCharacter en lugar de usar un any genérico
    const updatedChar = result.current.character as unknown as MutatedCharacter;
    expect(updatedChar).not.toBeNull();
    expect(updatedChar.hp).toBe(15);
    expect(updatedChar.location).toBe('Cripta Oscura - Pasillo Norte');
    expect(updatedChar.conditions).toContain('Prone');
    expect(updatedChar.spell_slots).toEqual({ '1': 1 });

    expect(updatedChar.inventory).toEqual([
      { name: 'Espada Larga', quantity: 1, type: 'weapon', equipped: true },
      { name: 'Antorcha', quantity: 3, type: 'misc', equipped: false }
    ]);
  });

  it('debería gestionar los errores de comunicación con el DM de forma controlada', async () => {
    const { result } = renderHook(() => useGameSession(mockCharacterId));

    await act(async () => {
      await Promise.resolve();
    });

    vi.mocked(apiService.sendPlayerAction).mockRejectedValue(new Error('Ollama connection timeout'));

    await act(async () => {
      await result.current.sendAction('Intento abrir el cofre.');
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe('Ollama connection timeout');
    expect(result.current.messages).toHaveLength(1);
  });
});