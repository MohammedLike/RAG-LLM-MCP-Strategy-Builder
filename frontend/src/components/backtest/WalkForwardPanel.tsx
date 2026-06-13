import { useState, useEffect } from 'react';
import { useBacktestStore } from '../../stores/backtestStore';
import { runWalkForward } from '../../services/api';
import { Activity, Loader2, Shield } from 'lucide-react';

export const WalkForwardPanel = () => {
  const { latestBacktest } = useBacktestStore();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    if (!latestBacktest) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runWalkForward(
        latestBacktest.symbol,
        latestBacktest.strategy_spec,
        latestBacktest.period,
        5
      );
      if (res.error) setError(res.error);
      else setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setResult(null);
    setError(null);
  }, [latestBacktest?.timestamp]);

  if (!latestBacktest) {
    return <div className="text-slate-500 text-xs p-4 text-center">Run a backtest to enable walk-forward validation.</div>;
  }

  return (
    <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Shield className="text-[#3b82f6]" size={16} />
          <h3 className="font-black text-slate-200 text-xs uppercase tracking-widest">Walk-Forward Validation</h3>
        </div>
        <button
          onClick={handleRun}
          disabled={loading}
          className="px-4 py-1.5 bg-[#3b82f6] text-white rounded text-[10px] font-black uppercase cursor-pointer disabled:opacity-50 flex items-center gap-2"
        >
          {loading ? <Loader2 size={12} className="animate-spin" /> : <Activity size={12} />}
          {loading ? 'Running...' : 'Validate'}
        </button>
      </div>

      {error && <p className="text-red-400 text-xs text-center py-4">{error}</p>}

      {result?.summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="bg-slate-900/50 p-3 rounded border border-slate-800">
            <div className="text-[9px] text-slate-500 uppercase font-bold">OOS Avg Return</div>
            <div className="text-lg font-black text-emerald-400">{result.summary.avg_oos_return}%</div>
          </div>
          <div className="bg-slate-900/50 p-3 rounded border border-slate-800">
            <div className="text-[9px] text-slate-500 uppercase font-bold">OOS Avg Sharpe</div>
            <div className="text-lg font-black text-blue-400">{result.summary.avg_oos_sharpe}</div>
          </div>
          <div className="bg-slate-900/50 p-3 rounded border border-slate-800">
            <div className="text-[9px] text-slate-500 uppercase font-bold">Positive Folds</div>
            <div className="text-lg font-black text-slate-200">{result.summary.positive_oos_folds}/{result.summary.total_folds}</div>
          </div>
          <div className="bg-slate-900/50 p-3 rounded border border-slate-800">
            <div className="text-[9px] text-slate-500 uppercase font-bold">Consistency</div>
            <div className="text-lg font-black text-brand">{result.summary.consistency_pct}%</div>
          </div>
        </div>
      )}

      {result?.folds && (
        <div className="overflow-x-auto max-h-48">
          <table className="w-full text-[10px]">
            <thead className="text-slate-500 uppercase text-[9px]">
              <tr>
                <th className="text-left py-1 px-2">Fold</th>
                <th className="text-right py-1 px-2">In-Sample Ret</th>
                <th className="text-right py-1 px-2">Out-Sample Ret</th>
                <th className="text-right py-1 px-2">OOS Sharpe</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {result.folds.filter((f: any) => f.out_sample).map((f: any) => (
                <tr key={f.fold}>
                  <td className="py-1.5 px-2 font-bold text-slate-400">#{f.fold}</td>
                  <td className="py-1.5 px-2 text-right font-mono text-slate-300">{f.in_sample?.total_return?.toFixed(1)}%</td>
                  <td className={`py-1.5 px-2 text-right font-mono font-bold ${f.out_sample.total_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {f.out_sample.total_return?.toFixed(1)}%
                  </td>
                  <td className="py-1.5 px-2 text-right font-mono text-slate-300">{f.out_sample.sharpe?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!result && !error && !loading && (
        <p className="text-[10px] text-slate-500 text-center py-6">
          3-layer validation: train on 70% of each window, test on remaining 30% — Tradomate-style robustness check.
        </p>
      )}
    </div>
  );
};
