import React, { useState } from 'react';
import { Settings2, Loader2, Play, Activity } from 'lucide-react';
import { runBacktestAsync, pollBacktestResult } from '../../services/api';
import { useBacktestStore } from '../../stores/backtestStore';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export const ParameterOptimizer = () => {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const { latestBacktest } = useBacktestStore();

  const handleOptimize = async () => {
    if (!latestBacktest) return;
    
    setIsOptimizing(true);
    setError(null);
    setResults([]);

    // We take the latest backtest spec and generate a grid
    const baseSpec = latestBacktest.strategy_spec;
    const symbol = latestBacktest.symbol;
    const period = latestBacktest.period;
    
    // For demonstration, let's assume it's a moving average or RSI strategy and we tweak stop loss
    // A robust implementation would parse the spec and find numeric parameters to vary.
    // Here we will vary stop loss to demonstrate the parallel capability.
    
    const requests = [];
    const stopLosses = [0.01, 0.02, 0.03, 0.04, 0.05];
    
    for (const sl of stopLosses) {
      requests.push({
        symbol,
        period,
        strategy_spec: { ...baseSpec, stop_loss: sl }
      });
    }

    try {
      const initRes = await runBacktestAsync(requests);
      const taskId = initRes.task_id;
      
      if (!taskId) throw new Error("Failed to initialize optimization task");

      // Polling
      const poll = async () => {
        const statusRes = await pollBacktestResult(taskId);
        if (statusRes.status === "completed") {
          setIsOptimizing(false);
          const formattedResults = Object.keys(statusRes.results).map((k, i) => {
             const res = statusRes.results[k];
             if (res.error) return { name: `SL ${stopLosses[i]*100}%`, sharpe: 0, error: res.error };
             return {
                name: `SL ${stopLosses[i]*100}%`,
                sharpe: res.sharpe,
                return: res.total_return,
                winRate: res.win_rate
             };
          });
          setResults(formattedResults);
        } else if (statusRes.status === "failed") {
          setIsOptimizing(false);
          setError(statusRes.error || "Optimization failed");
        } else {
          setTimeout(poll, 1500);
        }
      };
      
      setTimeout(poll, 1500);

    } catch (e: any) {
      setError(e.message || "Optimization error");
      setIsOptimizing(false);
    }
  };

  return (
    <div className="bg-[#0a0e17] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full h-[400px] flex flex-col">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Settings2 className="text-[#00d09c]" size={16} />
          <h3 className="font-black text-slate-200 text-xs uppercase tracking-widest">Parameter Optimizer (Grid Search)</h3>
        </div>
        <button 
          onClick={handleOptimize}
          disabled={isOptimizing || !latestBacktest} 
          className="px-4 py-1.5 bg-[#00d09c] text-[#06090f] rounded text-[10px] font-black uppercase tracking-widest cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isOptimizing ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
          {isOptimizing ? 'Optimizing...' : 'Run Grid Search'}
        </button>
      </div>
      
      <div className="flex-1 min-h-0 overflow-y-auto">
        {!latestBacktest ? (
          <div className="h-full flex flex-col items-center justify-center">
            <Activity size={32} className="text-slate-700 mb-4" />
            <span className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Run a backtest first to optimize parameters</span>
          </div>
        ) : isOptimizing ? (
          <div className="h-full flex flex-col items-center justify-center">
            <Loader2 size={32} className="animate-spin text-[#00d09c] mb-4" />
            <span className="text-slate-400 font-bold uppercase tracking-widest text-xs">Running Parallel Backtests...</span>
            <span className="text-slate-600 font-bold uppercase tracking-widest text-[10px] mt-2">Iterating Stop Loss variations</span>
          </div>
        ) : error ? (
           <div className="h-full flex flex-col items-center justify-center text-red-400 font-bold text-xs uppercase tracking-widest text-center px-6">
             <Activity size={24} className="mb-2" />
             {error}
           </div>
        ) : results.length > 0 ? (
           <div className="h-full flex flex-col">
             <h4 className="text-[10px] font-black text-slate-400 mb-4 uppercase tracking-widest text-center">Sharpe Ratio by Stop Loss</h4>
             <ResponsiveContainer width="100%" height="100%">
               <BarChart data={results} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
                 <XAxis type="number" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
                 <YAxis dataKey="name" type="category" tick={{ fontSize: 9, fill: '#94a3b8', fontWeight: 'bold' }} axisLine={false} tickLine={false} width={60} />
                 <Tooltip
                   cursor={{fill: '#1e293b', opacity: 0.4}}
                   contentStyle={{ backgroundColor: '#0a0e17', border: '1px solid #1e293b', borderRadius: 4, color: '#f8fafc', fontSize: 11 }}
                   labelStyle={{ fontWeight: 'black', color: '#94a3b8', marginBottom: 4 }}
                 />
                 <Bar dataKey="sharpe" radius={[0, 4, 4, 0]}>
                   {results.map((entry, index) => (
                     <Cell key={`cell-${index}`} fill={entry.sharpe > 1 ? '#00d09c' : (entry.sharpe > 0 ? '#3b82f6' : '#ef4444')} />
                   ))}
                 </Bar>
               </BarChart>
             </ResponsiveContainer>
           </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center">
            <div className="h-12 w-12 rounded bg-slate-900 flex items-center justify-center border border-slate-800 mb-4">
              <Settings2 size={24} className="text-slate-600" />
            </div>
            <h4 className="font-bold text-sm text-slate-300">Ready to Optimize</h4>
            <p className="text-xs text-slate-500 mt-2 max-w-sm text-center">
              Click Run to distribute modified strategy parameters across multiple cores for concurrent execution.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
