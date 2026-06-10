import { useState, useEffect, useCallback } from 'react';
import { Character } from '@/types/rpg';
import { apiService } from '@/services/api';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function useGameSession(characterId: number) {
  const [character, setCharacter] = useState<Character | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Carga inicial de la ficha del personaje al entrar a la mesa de juego
  useEffect(() => {
    async function initSession() {
      try {
        setIsLoading(true);
        const data = await apiService.getCharacter(characterId);
        setCharacter(data);
        setError(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al iniciar la sesión';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    }
    initSession();
  }, [characterId]);

  /**
   * Ejecuta un turno completo de juego: envía la acción, pinta la pantalla
   * y muta el estado del personaje de manera síncrona con el backend.
   */
  const sendAction = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Inyección optimista del mensaje del jugador
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // Petición única al orquestador backend
      const data = await apiService.sendPlayerAction(characterId, content);

      // Añadimos la respuesta narrativa del DM
      const dmMessage: Message = {
        role: 'assistant',
        content: data.narrative,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, dmMessage]);

      // Mapeamos el estado mutado directamente al estado de React garantizando compatibilidad estructural
      setCharacter((prevChar) => {
        if (!prevChar) return null;

        // Conciliamos el inventario simplificado del backend con el del dominio del frontend
        const updatedInventory = data.inventory.map((apiItem) => {
          // Buscamos si el personaje ya tenía este objeto para preservar sus propiedades avanzadas (type, equipped)
          const existingItem = prevChar.inventory.find(
            (i) => i.name.toLowerCase() === apiItem.name.toLowerCase()
          );

          return {
            name: apiItem.name,
            quantity: apiItem.quantity,
            type: existingItem ? existingItem.type : 'misc',
            equipped: existingItem ? existingItem.equipped : false,
          };
        });

        return {
          ...prevChar,
          hp: data.hp_current,
          max_hp: data.hp_max,
          location: data.location,
          conditions: data.conditions,
          spell_slots: data.spell_slots,
          inventory: updatedInventory,
        };
      });

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Fallo de comunicación con el DM';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [characterId, isLoading]);

  // Retorno explícito de la API pública del hook para resolver los avisos del linter
  return {
    character,
    messages,
    isLoading,
    error,
    sendAction,
  };
}