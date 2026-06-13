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
    
    // Default symbol and period for prebuilt runs (Indian context)
    const symbol = 'NIFTY';
    const period = '2y';
    try {
      await runBacktest(symbol, strat.backtest_spec, period);
      onLoadStrategy(strat.backtest_spec);
    } catch (err) {
      console.error('Predefined strategy run failed', err);
    } finally {
      setActiveStrategySlug(null);
    }
  };

  return (
    <div className="bg-[#0a0e17] border border-slate-800/80 rounded-xl p-6 text-slate-100 shadow-2xl">
      <div className="flex justify-between items-center mb-6 border-b border-slate-800/50 pb-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-[#00d09c]/10 flex items-center justify-center border border-[#00d09c]/20">
            <Layers className="text-[#00d09c]" size={20} />
          </div>
          <div>
            <h3 className="font-black text-slate-200 text-sm uppercase tracking-tighter">Discover Alpha</h3>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Pre-built NSE/BSE Strategy Templates</p>
          </div>
        </div>
        <span className="text-[10px] bg-[#00d09c]/10 text-[#00d09c] border border-[#00d09c]/30 px-3 py-1 rounded-full font-black uppercase tracking-widest flex items-center gap-1.5">
          <Sparkles size={10} /> Verified
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[420px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-800">
        {strategies.length > 0 ? (
          strategies.map((strat) => {
            const isRunningThis = loading && activeStrategySlug === strat.slug;
            // Compare strategy specs deeply since they can be different object instances
            const isCurrentlyDisplayed = latestBacktest?.strategy_spec && strat.backtest_spec
              ? JSON.stringify(latestBacktest.strategy_spec) === JSON.stringify(strat.backtest_spec)
              : false;
            
            return (
              <div
                key={strat.slug}
                className={`flex flex-col bg-slate-900/30 border rounded-lg p-5 transition-all duration-300 group ${
                  isCurrentlyDisplayed 
                    ? 'border-[#00d09c]/50 bg-[#00d09c]/5' 
                    : 'border-slate-800/60 hover:bg-slate-800/40 hover:border-slate-700'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-xs font-black text-slate-100 uppercase tracking-tight">{strat.name}</h4>
                    <span className="text-[9px] px-2 py-0.5 rounded-sm bg-slate-950 border border-slate-800 text-slate-500 font-bold mt-1.5 inline-block uppercase tracking-widest">
                      {strat.category}
                    </span>
                  </div>
                  <button
                    onClick={() => handleRun(strat)}
                    disabled={loading}
                    className={`px-4 py-2 rounded text-[10px] font-black uppercase tracking-widest flex items-center gap-2 transition cursor-pointer shadow-lg ${
                      isCurrentlyDisplayed
                        ? 'bg-green-500/20 text-green-400 border border-green-500/40'
                        : 'bg-[#00d09c] hover:bg-[#00b386] text-[#06090f]'
                    }`}
                  >
                    {isRunningThis ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : isCurrentlyDisplayed ? (
                      <Check size={12} />
                    ) : (
                      <Play size={12} />
                    )}
                    {isRunningThis ? 'RUNNING' : isCurrentlyDisplayed ? 'ACTIVE' : 'DEPLOY'}
                  </button>
                </div>

                <p className="text-[11px] text-slate-500 leading-relaxed mt-4 flex-1 line-clamp-3 font-medium">
                  {strat.description}
                </p>

                {/* Tags and Backtest metrics */}
                <div className="mt-4 pt-4 border-t border-slate-800/50 flex items-center justify-between">
                  <div className="flex flex-wrap gap-1.5">
                    {strat.tags?.slice(0, 2).map((t: string) => (
                      <span key={t} className="text-[9px] font-black text-slate-600 uppercase">
                        #{t}
                      </span>
                    ))}
                  </div>
                  {strat.backtest_results && (
                    <div className="flex gap-4">
                      <div className="flex flex-col items-end">
                        <span className="text-[8px] font-black text-slate-600 uppercase">Sharpe</span>
                        <span className="text-[10px] font-black text-[#00d09c]">{strat.backtest_results.sharpe}</span>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-[8px] font-black text-slate-600 uppercase">MaxDD</span>
                        <span className="text-[10px] font-black text-red-500">{strat.backtest_results.max_drawdown}%</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="col-span-2 py-12 text-center">
            <div className="flex flex-col items-center gap-3">
              <Loader2 size={24} className="animate-spin text-slate-700" />
              <span className="text-slate-600 font-black uppercase tracking-widest text-[10px]">Synchronizing Strategy Repository</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
