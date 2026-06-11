import { useEffect, useState } from 'react';
import { fetchStrategies } from '../../services/api';
import { useBacktestStore } from '../../stores/backtestStore';
import { Layers, Play, Loader2, Sparkles, Check } from 'lucide-react';

interface PredefinedStrategiesProps {
  onLoadStrategy: (strategySpec: any) => void;
}

export const PredefinedStrategies = ({ onLoadStrategy }: PredefinedStrategiesProps) => {
  const { runBacktest, loading, latestBacktest } = useBacktestStore();
  const [strategies, setStrategies] = useState<any[]>([]);
  const [activeStrategySlug, setActiveStrategySlug] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchStrategies();
        setStrategies(data);
      } catch (err) {
        console.error('Error loading strategies', err);
      }
    };
    load();
  }, []);

  const handleRun = async (strat: any) => {
    if (loading) return;
    setActiveStrategySlug(strat.slug);
    
    // Default symbol and period for prebuilt runs
    const symbol = 'NIFTY';
    const period = '2y';
    
    await runBacktest(symbol, strat.backtest_spec, period);
    onLoadStrategy(strat.backtest_spec);
  };

  return (
    <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-5 text-slate-100 shadow-xl">
      <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Layers className="text-blue-500" size={18} />
          <div>
            <h3 className="font-bold text-slate-100 text-sm">Pre-defined Strategies Gallery</h3>
            <p className="text-[11px] text-slate-400">Deploy institutional templates in 1-click on NIFTY index</p>
          </div>
        </div>
        <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
          <Sparkles size={10} /> Ready to Deploy
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[380px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-800">
        {strategies.length > 0 ? (
          strategies.map((strat) => {
            const isRunningThis = loading && activeStrategySlug === strat.slug;
            const isCurrentlyDisplayed = latestBacktest?.strategy_spec === strat.backtest_spec;
            
            return (
              <div
                key={strat.slug}
                className={`flex flex-col bg-slate-900/60 border rounded-lg p-4 transition-all duration-200 ${
                  isCurrentlyDisplayed 
                    ? 'border-blue-500/50 bg-[#131d35]/30' 
                    : 'border-slate-800/80 hover:bg-[#11192e] hover:border-slate-700/60'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-xs font-bold text-slate-200">{strat.name}</h4>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400 font-mono mt-1 inline-block">
                      {strat.category}
                    </span>
                  </div>
                  <button
                    onClick={() => handleRun(strat)}
                    disabled={loading}
                    className={`px-3 py-1.5 rounded-md text-[10px] font-bold flex items-center gap-1.5 transition cursor-pointer ${
                      isCurrentlyDisplayed
                        ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-500/40'
                        : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm'
                    }`}
                  >
                    {isRunningThis ? (
                      <Loader2 size={10} className="animate-spin" />
                    ) : isCurrentlyDisplayed ? (
                      <Check size={10} />
                    ) : (
                      <Play size={10} />
                    )}
                    {isRunningThis ? 'Running...' : isCurrentlyDisplayed ? 'Active' : 'Deploy'}
                  </button>
                </div>

                <p className="text-[10px] text-slate-400 leading-relaxed mt-2.5 flex-1 line-clamp-3">
                  {strat.description}
                </p>

                {/* Tags and Backtest metrics */}
                <div className="mt-3.5 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[9px] text-slate-400 font-mono">
                  <div className="flex flex-wrap gap-1">
                    {strat.tags?.slice(0, 2).map((t: string) => (
                      <span key={t} className="bg-slate-950 px-1 rounded text-slate-500 border border-slate-800/60">
                        #{t}
                      </span>
                    ))}
                  </div>
                  {strat.backtest_results && (
                    <div className="flex gap-2.5 text-slate-300">
                      <div>Sharpe: <span className="font-bold text-blue-400">{strat.backtest_results.sharpe}</span></div>
                      <div>MaxDD: <span className="font-bold text-red-400">{strat.backtest_results.max_drawdown}%</span></div>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="col-span-2 py-8 text-center text-slate-500 text-xs">
            Loading strategies from repository...
          </div>
        )}
      </div>
    </div>
  );
};
