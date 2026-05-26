import { useState, useEffect, useCallback } from 'react';
import { Character, ChatMessagePayload } from '@/types/rpg';
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

  // Carga inicial de la ficha del personaje
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

  const sendAction = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const payload: ChatMessagePayload = {
        character_id: characterId,
        role: 'user',
        content,
      };

      const data = await apiService.sendNarrativeAction(payload);

      const dmMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, dmMessage]);

      const updatedCharacter = await apiService.getCharacter(characterId);
      setCharacter(updatedCharacter);

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Fallo de comunicación con el DM';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [characterId, isLoading]);

  return {
    character,
    messages,
    isLoading,
    error,
    sendAction,
  };
}