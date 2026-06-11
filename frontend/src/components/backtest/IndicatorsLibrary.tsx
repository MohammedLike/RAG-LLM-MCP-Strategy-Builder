import { useState, useEffect } from 'react';
import { useBacktestStore } from '../../stores/backtestStore';
import { Search, HelpCircle, ArrowRight, Settings } from 'lucide-react';

interface IndicatorsLibraryProps {
  onSelectIndicator: (indicatorName: string, defaults: any, type: 'entry' | 'exit') => void;
}

export const IndicatorsLibrary = ({ onSelectIndicator }: IndicatorsLibraryProps) => {
  const { indicators, fetchIndicators } = useBacktestStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [expandedIndicator, setExpandedIndicator] = useState<string | null>(null);

  useEffect(() => {
    fetchIndicators();
  }, [fetchIndicators]);

  const indicatorList = Object.values(indicators);
  
  // Extract unique categories
  const categories = ['All', ...Array.from(new Set(indicatorList.map(ind => ind.category)))];

  const filteredIndicators = indicatorList.filter(ind => {
    const matchesSearch = 
      ind.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ind.long_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ind.description.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = selectedCategory === 'All' || ind.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="flex flex-col h-full bg-[#0b0f19] border border-slate-800 rounded-xl overflow-hidden shadow-xl text-slate-100">
      {/* Search and Categories Header */}
      <div className="p-4 border-b border-slate-800 bg-[#0f172a]/60 backdrop-blur-md space-y-3">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-blue-500 animate-pulse"></span>
              Indicator Reference Library
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Explore 100+ TA-Lib indicators & candlestick patterns</p>
          </div>
          <span className="bg-slate-800/80 text-[10px] px-2 py-0.5 rounded-full border border-slate-700 text-slate-300 font-medium">
            {indicatorList.length} Available
          </span>
        </div>

        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name, code, description..."
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
          <Search className="absolute left-3 top-2.5 text-slate-400" size={14} />
        </div>

        {/* Categories Carousel */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-full text-[10px] font-medium transition-all duration-150 border cursor-pointer whitespace-nowrap ${
                selectedCategory === cat
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Indicators Grid */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2.5 bg-slate-950/40">
        {filteredIndicators.length > 0 ? (
          filteredIndicators.map((ind) => {
            const isExpanded = expandedIndicator === ind.name;
            return (
              <div
                key={ind.name}
                className={`border rounded-lg transition-all duration-200 ${
                  isExpanded
                    ? 'bg-[#1e293b]/50 border-blue-500/50 shadow-md'
                    : 'bg-slate-900/60 border-slate-800/80 hover:bg-[#131b2e] hover:border-slate-700/80'
                }`}
              >
                {/* Header Row */}
                <div
                  onClick={() => setExpandedIndicator(isExpanded ? null : ind.name)}
                  className="p-3 flex items-center justify-between cursor-pointer"
                >
                  <div className="flex-1 min-w-0 pr-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-blue-400">{ind.name}</span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 border border-slate-700/50 text-slate-400">
                        {ind.category}
                      </span>
                    </div>
                    <div className="text-xs font-semibold text-slate-200 mt-1 truncate">{ind.long_name}</div>
                  </div>
                  <HelpCircle size={14} className="text-slate-500 hover:text-slate-300 transition-colors" />
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-3 pb-3 border-t border-slate-800/60 pt-2.5 text-xs text-slate-300 space-y-3 animate-fadeIn">
                    <p className="text-[11px] leading-relaxed text-slate-400">{ind.description}</p>
                    
                    {/* Params & Inputs */}
                    <div className="grid grid-cols-2 gap-2.5 bg-slate-950/60 p-2 rounded border border-slate-800/60 font-mono text-[10px]">
                      <div>
                        <div className="text-slate-500 uppercase font-semibold text-[8px] tracking-wider mb-0.5 flex items-center gap-1">
                          <Settings size={10} />
                          Params
                        </div>
                        <div className="text-slate-300">
                          {Object.keys(ind.params).length > 0 ? (
                            Object.entries(ind.params).map(([k, v]) => (
                              <div key={k}>{k}: {String(v)}</div>
                            ))
                          ) : (
                            <span className="text-slate-500">None</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-500 uppercase font-semibold text-[8px] tracking-wider mb-0.5 flex items-center gap-1">
                          <ArrowRight size={10} />
                          Inputs
                        </div>
                        <div className="text-slate-300 flex flex-wrap gap-1 mt-0.5">
                          {ind.inputs.map(inp => (
                            <span key={inp} className="bg-slate-800 px-1 rounded text-[9px] text-slate-400 border border-slate-700/30">
                              {inp}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Copy Buttons */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => onSelectIndicator(ind.name, ind.params, 'entry')}
                        className="flex-1 bg-blue-600/20 hover:bg-blue-600/35 border border-blue-500/40 text-blue-300 py-1.5 px-2 rounded font-semibold text-[10px] text-center transition cursor-pointer"
                      >
                        Copy to Entry
                      </button>
                      <button
                        onClick={() => onSelectIndicator(ind.name, ind.params, 'exit')}
                        className="flex-1 bg-emerald-600/20 hover:bg-emerald-600/35 border border-emerald-500/40 text-emerald-300 py-1.5 px-2 rounded font-semibold text-[10px] text-center transition cursor-pointer"
                      >
                        Copy to Exit
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="h-40 flex flex-col items-center justify-center text-slate-500 text-xs text-center p-4">
            <Search className="mb-2 opacity-30 text-slate-300" size={24} />
            <span>No indicators matched your search.</span>
            <button onClick={() => { setSearchTerm(''); setSelectedCategory('All'); }} className="text-blue-400 underline mt-1 text-[11px] cursor-pointer">
              Clear filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
