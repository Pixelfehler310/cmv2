import React from 'react';

export const CommandDeck = () => {
  return (
    <div className="w-full h-full bg-slate-900 text-slate-100 p-4 flex items-center justify-between gap-4 overflow-hidden">
      <div className="flex items-center gap-2">
        <div className="w-12 h-12 bg-slate-700 rounded-full border-2 border-slate-600 flex items-center justify-center">
            <span className="text-xs">IMG</span>
        </div>
        <div>
          <div className="font-bold text-lg">Aragorn</div>
          <div className="text-sm text-green-400 font-mono">HP: 45/58</div>
        </div>
      </div>
      
      <div className="flex-1 flex justify-center gap-2">
        {[1, 2, 3, 4, 5].map(i => (
          <button key={i} className="w-12 h-12 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 flex items-center justify-center transition-colors shadow-sm">
            <span className="font-bold">A{i}</span>
          </button>
        ))}
      </div>

      <button className="bg-amber-600 hover:bg-amber-700 text-white px-6 py-3 rounded-lg font-bold transition-colors shadow-md uppercase tracking-wider text-sm">
        End Turn
      </button>
    </div>
  );
};
