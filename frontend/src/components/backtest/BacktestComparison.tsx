import React from 'react';
import { Layers } from 'lucide-react';

export const BacktestComparison = () => {
  return (
    <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full">
      <div className="flex items-center gap-2 mb-4 border-b border-slate-800/80 pb-3">
        <Layers className="text-[#3b82f6]" size={16} />
        <h3 className="font-black text-slate-200 text-xs uppercase tracking-widest">Strategy Comparison</h3>
      </div>
      <div className="flex flex-col items-center justify-center py-10">
        <Layers size={32} className="text-slate-700 mb-4" />
        <h4 className="font-bold text-sm text-slate-400">No Secondary Runs Found</h4>
        <p className="text-xs text-slate-600 mt-1 max-w-sm text-center">
          Run multiple backtests to pin them to the comparison board. You can overlay equity curves and compare risk metrics side-by-side.
        </p>
      </div>
    </div>
  );
};
