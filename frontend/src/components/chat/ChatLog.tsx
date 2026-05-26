import React from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatLogProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatLog({ messages, isLoading }: ChatLogProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-900 border border-slate-800 rounded-lg min-h-[400px] max-h-[600px]">
      {messages.length === 0 && (
        <div className="text-slate-500 text-center mt-10 italic">
          La taberna está en silencio. Describe tu primera acción para comenzar la aventura...
        </div>
      )}

      {messages.map((msg, index) => {
        const isDM = msg.role === 'assistant';
        return (
          <div
            key={index}
            className={`flex ${isDM ? 'justify-start' : 'justify-end'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 text-sm leading-relaxed ${
                isDM
                  ? 'bg-slate-800 text-slate-100 border-l-4 border-amber-500 rounded-bl-none'
                  : 'bg-amber-700 text-amber-50 rounded-br-none font-medium'
              }`}
            >
              <div className="text-xs opacity-50 mb-1 font-semibold tracking-wider">
                {isDM ? '🔮 DUNGEON MASTER' : '⚔️ JUGADOR'}
              </div>
              <p className="whitespace-pre-line">{msg.content}</p>
            </div>
          </div>
        );
      })}

      {isLoading && (
        <div className="flex justify-start">
          <div className="bg-slate-800 text-slate-400 text-sm italic rounded-lg p-3 rounded-bl-none animate-pulse">
            🔮 El Dungeon Master está consultando los dados y tejiendo el destino...
          </div>
        </div>
      )}
    </div>
  );
}