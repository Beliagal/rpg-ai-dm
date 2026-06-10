'use client';

import { useGameSession } from '@/hooks/useGameSession';
import { ChatLog } from '@/components/chat/ChatLog';
import { ChatInput } from '@/components/chat/ChatInput';

export default function Home() {
  // Inicializamos con el personaje con ID 1 para la sesión de desarrollo
  const { character, messages, isLoading, error, sendAction } = useGameSession(1);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 flex flex-col items-center justify-center font-sans">
      <div className="w-full max-w-4xl flex flex-col gap-4">
        
        {/* Cabecera de Estado Sincronizada */}
        <header className="border-b border-slate-800 pb-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold tracking-wide text-amber-500">RPG AI Dungeon Master</h1>
            <p className="text-xs text-slate-400 mt-1">
              Ubicación: <span className="text-slate-200 font-medium">{character ? character.location : 'Cargando...'}</span>
            </p>
          </div>
          {character && (
            <div className="text-sm bg-slate-900 border border-slate-800 px-3 py-2 rounded-md flex items-center gap-2">
              <span className="font-semibold text-slate-300">{character.name} ({character.char_class})</span>
              <span className="text-slate-600">|</span>
              <span className="text-red-400 font-bold">❤️ {character.hp} / {character.max_hp} HP</span>
            </div>
          )}
        </header>

        {error && (
          <div className="bg-red-950/50 border border-red-800 text-red-200 text-sm p-3 rounded-lg">
            ⚠️ {error}
          </div>
        )}

        {/* Consola de juego */}
        <ChatLog messages={messages} />
        
        {/* Barra inferior corregida con la propiedad 'onSend' que exige el componente */}
        <div className="mt-2">
          <ChatInput onSend={sendAction} disabled={isLoading || !character} />
        </div>

      </div>
    </main>
  );
}