import React from 'react';
import { Character } from '@/types/rpg';
import { SpellSlots } from '@/services/api';

// Interfaz extendida para pintar con seguridad los metadatos SRD mutados
interface CharacterSheetProps {
  character: Character & {
    conditions?: string[];
    spell_slots?: SpellSlots;
  };
}

export const CharacterSheet: React.FC<CharacterSheetProps> = ({ character }) => {
  const hpPercentage = Math.max(0, Math.min(100, (character.hp / character.max_hp) * 100));

  // Determinar color de la barra de vida según el estado de salud
  const getHpBarColor = () => {
    if (hpPercentage > 50) return 'bg-emerald-600';
    if (hpPercentage > 20) return 'bg-amber-500';
    return 'bg-rose-600 animate-pulse';
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 border-l border-slate-800 text-slate-200 text-sm">
      {/* CABECERA: IDENTIDAD */}
      <div className="p-4 bg-slate-950 border-b border-slate-800">
        <h2 className="text-xl font-bold tracking-tight text-amber-500 truncate">{character.name}</h2>
        <p className="text-xs text-slate-400 font-mono mt-0.5 uppercase tracking-wider">
          {character.race} • {character.char_class}
        </p>
      </div>

      {/* ESTADO VITAL (HP) */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/50">
        <div className="flex justify-between font-medium text-xs font-mono mb-1.5 text-slate-300">
          <span>PUNTOS DE VIDA</span>
          <span className={character.hp <= character.max_hp * 0.2 ? 'text-rose-400' : 'text-slate-400'}>
            {character.hp} / {character.max_hp}
          </span>
        </div>
        <div className="h-2.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800/60">
          <div 
            className={`h-full transition-all duration-500 ease-out ${getHpBarColor()}`}
            style={{ width: `${hpPercentage}%` }}
          />
        </div>
      </div>

      {/* ATRIBUTOS BASE (STATS) */}
      <div className="p-4 border-b border-slate-800">
        <h3 className="text-xs font-bold text-slate-400 font-mono tracking-wider uppercase mb-3">Atributos</h3>
        <div className="grid grid-cols-3 gap-2 text-center">
          {Object.entries(character.stats || {}).map(([stat, val]) => {
            const modifier = Math.floor((val - 10) / 2);
            const modSign = modifier >= 0 ? `+${modifier}` : `${modifier}`;
            return (
              <div key={stat} className="bg-slate-950/60 border border-slate-800/40 p-2 rounded flex flex-col justify-center">
                <span className="text-[10px] font-bold text-slate-500 font-mono uppercase tracking-tight">{stat.substring(0, 3)}</span>
                <span className="text-base font-semibold text-slate-200 mt-0.5">{val}</span>
                <span className="text-[10px] text-amber-500/80 font-mono font-medium mt-0.5">{modSign}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ESTADOS ALTERADOS (CONDITIONS) */}
      {character.conditions && character.conditions.length > 0 && (
        <div className="p-4 border-b border-slate-800 bg-rose-950/10">
          <h3 className="text-xs font-bold text-rose-400 font-mono tracking-wider uppercase mb-2">Estados Alterados</h3>
          <div className="flex flex-wrap gap-1.5">
            {character.conditions.map((cond, idx) => (
              <span 
                key={idx} 
                className="px-2 py-0.5 text-xs font-semibold rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 uppercase tracking-wide font-mono"
              >
                {cond}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ESPACIOS DE CONJURO (SPELL SLOTS) */}
      {character.spell_slots && Object.keys(character.spell_slots).length > 0 && (
        <div className="p-4 border-b border-slate-800">
          <h3 className="text-xs font-bold text-slate-400 font-mono tracking-wider uppercase mb-2">Espacios de Conjuro</h3>
          <div className="space-y-2">
            {Object.entries(character.spell_slots).map(([level, slots]) => (
              <div key={level} className="flex justify-between items-center bg-slate-950/30 px-3 py-1.5 rounded border border-slate-800/40">
                <span className="text-xs font-medium text-slate-300 font-mono">Nivel {level}</span>
                <span className="text-xs bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded font-mono font-bold border border-amber-500/10">
                  {slots} Disponibles
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* INVENTARIO */}
      <div className="p-4 flex-1 overflow-y-auto">
        <h3 className="text-xs font-bold text-slate-400 font-mono tracking-wider uppercase mb-2">Inventario</h3>
        {character.inventory && character.inventory.length > 0 ? (
          <ul className="space-y-1.5">
            {character.inventory.map((item, idx) => (
              <li 
                key={idx} 
                className={`flex justify-between items-center px-3 py-2 rounded text-xs border ${
                  item.equipped 
                    ? 'bg-amber-600/10 border-amber-500/20 text-amber-200 font-medium' 
                    : 'bg-slate-950/40 border-slate-800/40 text-slate-400'
                }`}
              >
                <div className="flex flex-col gap-0.5">
                  <span>{item.name}</span>
                  {item.equipped && (
                    <span className="text-[9px] text-amber-500/80 uppercase font-bold font-mono tracking-tight">Equipado</span>
                  )}
                </div>
                <span className="font-mono text-slate-500 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                  x{item.quantity}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-slate-600 italic mt-1">El inventario está completamente vacío.</p>
        )}
      </div>
    </div>
  );
};