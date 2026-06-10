import React, { useEffect, useRef } from 'react';
import { useGameSession } from '@/hooks/useGameSession';

// Usamos el alias absoluto apuntando directamente a la carpeta chat
import { CharacterSheet } from '@/components/chat/CharacterSheet';
import { ChatLog } from '@/components/chat/ChatLog';
import { ChatInput } from '@/components/chat/ChatInput';

interface GameScreenProps {
  characterId: number;
}

export const GameScreen: React.FC<GameScreenProps> = ({ characterId }) => {
  const { character, messages, isLoading, error, sendAction } = useGameSession(characterId);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll hacia abajo cada vez que entra un nuevo mensaje
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!character && isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-white">
        <div className="animate-pulse text-lg font-medium">Invocando al Dungeon Master...</div>
      </div>
    );
  }

  if (error && !character) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-900 text-red-400 p-4 text-center">
        <div>
          <h2 className="text-xl font-bold mb-2">Error Crítico</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* SECCIÓN IZQUIERDA: ÁREA DE JUEGO Y CHAT */}
      <div className="flex flex-1 flex-col h-full border-r border-slate-800">
        {/* Cabecera de la localización actual */}
        <header className="bg-slate-900 px-6 py-4 border-b border-slate-800 flex justify-between items-center">
          <div>
            <span className="text-xs font-semibold tracking-wider text-amber-500 uppercase">Localización Actual</span>
            <h1 className="text-lg font-bold text-slate-200">{character?.location || 'Explorando...'}</h1>
          </div>
          {isLoading && (
            <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-3 py-1 rounded-full animate-pulse">
              El DM está pensando...
            </span>
          )}
        </header>

        {/* Historial de Mensajes Narrativos */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <ChatLog messages={messages} />
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded text-sm">
              ⚠ {error}
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Barra de Entrada de Acciones */}
        <footer className="p-4 bg-slate-900/50 border-t border-slate-800">
          <ChatInput onSend={sendAction} disabled={isLoading} />
        </footer>
      </div>

      {/* SECCIÓN DERECHA: FICHA LATERAL DEL PERSONAJE */}
      <aside className="w-80 h-full bg-slate-900 overflow-y-auto hidden md:block">
        {character && <CharacterSheet character={character} />}
      </aside>
    </div>
  );
};