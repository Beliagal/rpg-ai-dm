// @vitest-environment jsdom
import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useGameSession } from './useGameSession';
import { apiService } from '@/services/api';

vi.mock('@/services/api', () => ({
  apiService: {
    getCharacter: vi.fn(),
    sendNarrativeAction: vi.fn(),
  },
}));

const mockCharacter = {
  id: 1,
  name: 'Ragnar',
  race: 'Humano',
  char_class: 'Guerrero',
  hp: 20,
  max_hp: 20,
  location: 'Taberna del Dragón Verde',
  stats: { strength: 16, dexterity: 12, constitution: 14, intelligence: 10, wisdom: 11, charisma: 13 },
  inventory: [],
};

describe('useGameSession Hook', () => {
  it('debería inicializar el estado del personaje correctamente al cargar', async () => {
    vi.mocked(apiService.getCharacter).mockResolvedValueOnce(mockCharacter);

    const { result } = renderHook(() => useGameSession(1));

    expect(result.current.isLoading).toBe(true);
    expect(result.current.character).toBeNull();

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.character).toEqual(mockCharacter);
    expect(result.current.error).toBeNull();
  });

  it('debería manejar errores si la API de inicialización falla', async () => {
    vi.mocked(apiService.getCharacter).mockRejectedValueOnce(new Error('Error de conexión de red'));

    const { result } = renderHook(() => useGameSession(1));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.character).toBeNull();
    expect(result.current.error).toBe('Error de conexión de red');
  });

  it('debería añadir la acción del jugador y la respuesta del DM en orden', async () => {
    vi.mocked(apiService.getCharacter).mockResolvedValueOnce(mockCharacter);
    
    const { result } = renderHook(() => useGameSession(1));
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    const mockNarrativeResponse = { response: 'El tabernero te mira de reojo.' };
    const mockUpdatedCharacter = { ...mockCharacter, location: 'Barra de la taberna' };

    vi.mocked(apiService.sendNarrativeAction).mockResolvedValueOnce(mockNarrativeResponse);
    vi.mocked(apiService.getCharacter).mockResolvedValueOnce(mockUpdatedCharacter);

    await act(async () => {
      await result.current.sendAction('Examino las salidas.');
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.messages[0].content).toBe('Examino las salidas.');
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toBe(mockNarrativeResponse.response);

    expect(result.current.character?.location).toBe('Barra de la taberna');
  });
});