import React from 'react';
import { Message } from '@/hooks/useGameSession';

interface ChatLogProps {
  messages: Message[];
}

export const ChatLog: React.FC<ChatLogProps> = ({ messages }) => {
  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-slate-500 text-sm italic">
        Describe tu primera acción para que el Dungeon Master comience la crónica...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((msg, idx) => {
        const isUser = msg.role === 'user';
        return (
          <div
            key={idx}
            className={`flex flex-col max-w-[85%] ${isUser ? 'ml-auto items-end' : 'mr-auto items-start'}`}
          >
            <span className="text-[10px] text-slate-500 mb-1 px-1">
              {isUser ? 'Tú (Acción)' : 'Dungeon Master'}
            </span>
            <div
              className={`rounded-lg px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${
                isUser
                  ? 'bg-amber-600 text-slate-50 font-medium rounded-tr-none'
                  : 'bg-slate-850 border border-slate-800 text-slate-300 rounded-tl-none serif-text'
              }`}
            >
              {msg.content}
            </div>
          </div>
        );
      })}
    </div>
  );
};