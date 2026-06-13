import { useState } from 'react';
import { Settings2, Loader2, Play, Activity } from 'lucide-react';
import { optimizeBacktest } from '../../services/api';
import { useBacktestStore } from '../../stores/backtestStore';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export const ParameterOptimizer = () => {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [bestParams, setBestParams] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { latestBacktest } = useBacktestStore();

  const handleOptimize = async () => {
    if (!latestBacktest) return;

    setIsOptimizing(true);
    setError(null);
    setResults([]);
    setBestParams(null);

    const baseSpec = latestBacktest.strategy_spec;
    const symbol = latestBacktest.symbol;
    const period = latestBacktest.period;

    const paramGrid = {
      stop_loss: [1, 2, 3, 4, 5],
      take_profit: [3, 5, 8, 10],
    };

    try {
      const res = await optimizeBacktest(symbol, baseSpec, period, paramGrid);
      if (res.error) throw new Error(res.error);

      const grid = res.optimization_grid || [];
      const formatted = grid
        .filter((r: any) => !r.error)
        .map((r: any) => {
          const sl = r.params?.stop_loss ?? '?';
          const tp = r.params?.take_profit ?? '?';
          return {
            name: `SL${sl}/TP${tp}`,
            sharpe: r.sharpe ?? 0,
            return: r.total_return ?? 0,
            winRate: r.win_rate ?? 0,
            maxDrawdown: r.max_drawdown ?? 0,
            params: r.params,
          };
        });

      setResults(formatted);
      setBestParams(res.best_params || null);
    } catch (e: any) {
      setError(e.message || 'Optimization error');
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full min-h-[400px] flex flex-col">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Settings2 className="text-[#3b82f6]" size={16} />
          <h3 className="font-black text-slate-200 text-xs uppercase tracking-widest">Parameter Optimizer (Grid Search)</h3>
        </div>
        <button
          onClick={handleOptimize}
          disabled={isOptimizing || !latestBacktest}
          className="px-4 py-1.5 bg-[#3b82f6] text-white rounded text-[10px] font-black uppercase tracking-widest cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isOptimizing ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
          {isOptimizing ? 'Optimizing...' : 'Run Grid Search'}
        </button>
      </div>

      {bestParams && (
        <div className="mb-4 p-3 bg-emerald-950/20 border border-emerald-900/40 rounded text-[10px]">
          <span className="font-black text-emerald-400 uppercase">Best Params: </span>
          <span className="text-slate-300 font-mono">{JSON.stringify(bestParams)}</span>
        </div>
      )}

      <div className="flex-1 min-h-0 overflow-y-auto">
        {!latestBacktest ? (
          <div className="h-full flex flex-col items-center justify-center">
            <Activity size={32} className="text-slate-700 mb-4" />
            <span className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Run a backtest first to optimize parameters</span>
          </div>
        ) : isOptimizing ? (
          <div className="h-full flex flex-col items-center justify-center">
            <Loader2 size={32} className="animate-spin text-[#3b82f6] mb-4" />
            <span className="text-slate-400 font-bold uppercase tracking-widest text-xs">Running grid search...</span>
            <span className="text-slate-600 font-bold uppercase tracking-widest text-[10px] mt-2">Testing SL × TP combinations</span>
          </div>
        ) : error ? (
          <div className="h-full flex flex-col items-center justify-center text-red-400 font-bold text-xs uppercase tracking-widest text-center px-6">
            <Activity size={24} className="mb-2" />
            {error}
          </div>
        ) : results.length > 0 ? (
          <div className="h-[320px] flex flex-col">
            <h4 className="text-[10px] font-black text-slate-400 mb-4 uppercase tracking-widest text-center">Sharpe Ratio by Parameter Set</h4>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={results} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
                <XAxis type="number" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 8, fill: '#94a3b8', fontWeight: 'bold' }} axisLine={false} tickLine={false} width={70} />
                <Tooltip
                  cursor={{ fill: '#1e293b', opacity: 0.4 }}
                  contentStyle={{ backgroundColor: '#131c31', border: '1px solid #1e293b', borderRadius: 4, color: '#f8fafc', fontSize: 11 }}
                />
                <Bar dataKey="sharpe" radius={[0, 4, 4, 0]}>
                  {results.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.sharpe > 1 ? '#3b82f6' : entry.sharpe > 0 ? '#6366f1' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center">
            <Settings2 size={24} className="text-slate-600 mb-4" />
            <h4 className="font-bold text-sm text-slate-300">Ready to Optimize</h4>
            <p className="text-xs text-slate-500 mt-2 max-w-sm text-center">
              Grid search across stop-loss and take-profit combinations — like AlgoTest and QuantMan optimizers.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
