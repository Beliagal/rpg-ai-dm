import React, { useState } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    
    onSendMessage(input.trim());
    setInput('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 mt-2">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        disabled={disabled}
        placeholder={disabled ? "Espera a que el DM termine..." : "Ej: Desenvaino mi espada corta y avanzo con sigilo..."}
        className="flex-1 bg-slate-950 text-slate-100 text-sm border border-slate-800 rounded-lg px-4 py-3 focus:outline-none focus:border-amber-500 disabled:opacity-50 transition-colors"
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 text-slate-950 disabled:text-slate-600 font-bold px-6 py-3 rounded-lg text-sm tracking-wide transition-colors duration-150"
      >
        Narrar
      </button>
    </form>
  );
}