import { useMemo } from 'react';
import { Layers, Pin, Trash2, Trophy } from 'lucide-react';
import { useBacktestStore } from '../../stores/backtestStore';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export const BacktestComparison = () => {
  const { latestBacktest, pinnedRuns, pinCurrentRun, removePinnedRun, clearPinnedRuns } = useBacktestStore();

  const allRuns = useMemo(() => {
    const runs = [...pinnedRuns];
    if (latestBacktest && !runs.some((r) => r.timestamp === latestBacktest.timestamp)) {
      runs.push({ ...latestBacktest, label: `${latestBacktest.symbol} (current)` });
    }
    return runs;
  }, [pinnedRuns, latestBacktest]);

  const overlayData = useMemo(() => {
    if (allRuns.length < 2) return [];
    const maxLen = Math.max(...allRuns.map((r) => r.equity_curve?.length || 0));
    const data: Record<string, number | string>[] = [];
    for (let i = 0; i < maxLen; i++) {
      const row: Record<string, number | string> = { step: i };
      allRuns.forEach((run, idx) => {
        const pt = run.equity_curve?.[i];
        if (pt) {
          row[`run_${idx}`] = pt.value;
          if (i === 0 || !row.date) row.date = pt.date;
        }
      });
      data.push(row);
    }
    return data;
  }, [allRuns]);

  const metrics = ['total_return', 'sharpe', 'max_drawdown', 'win_rate', 'profit_factor'];

  return (
    <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <Layers className="text-[#3b82f6]" size={16} />
          <h3 className="font-black text-slate-200 text-xs uppercase tracking-widest">Strategy Comparison</h3>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => pinCurrentRun()}
            disabled={!latestBacktest}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-[10px] font-bold flex items-center gap-1 cursor-pointer disabled:opacity-40"
          >
            <Pin size={12} /> Pin Current
          </button>
          {pinnedRuns.length > 0 && (
            <button onClick={clearPinnedRuns}
              className="px-3 py-1 bg-red-950/40 hover:bg-red-950/60 text-red-400 rounded text-[10px] font-bold cursor-pointer">
              Clear All
            </button>
          )}
        </div>
      </div>

      {pinnedRuns.length === 0 && !latestBacktest ? (
        <div className="flex flex-col items-center justify-center py-10">
          <Layers size={32} className="text-slate-700 mb-4" />
          <h4 className="font-bold text-sm text-slate-400">No Runs to Compare</h4>
          <p className="text-xs text-slate-600 mt-1 max-w-sm text-center">
            Run backtests and pin them to overlay equity curves and compare metrics side-by-side.
          </p>
        </div>
      ) : (
        <>
          {/* Pinned runs list */}
          <div className="flex flex-wrap gap-2">
            {pinnedRuns.map((run, idx) => (
              <div key={idx} className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/60 border border-slate-800 rounded text-[10px]">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                <span className="font-bold text-slate-300">{run.label || run.symbol}</span>
                <span className={`font-mono ${run.total_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {run.total_return?.toFixed(1)}%
                </span>
                <button onClick={() => removePinnedRun(idx)} className="text-slate-600 hover:text-red-400 cursor-pointer">
                  <Trash2 size={10} />
                </button>
              </div>
            ))}
          </div>

          {/* Metrics table */}
          {allRuns.length >= 1 && (
            <div className="overflow-x-auto">
              <table className="w-full text-[10px]">
                <thead>
                  <tr className="text-slate-500 uppercase text-[9px]">
                    <th className="text-left py-2 px-2">Strategy</th>
                    {metrics.map((m) => (
                      <th key={m} className="text-right py-2 px-2">{m.replace('_', ' ')}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {allRuns.map((run, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/20">
                      <td className="py-2 px-2 font-bold text-slate-300 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                        {run.label || run.symbol}
                      </td>
                      <td className={`text-right py-2 px-2 font-mono ${run.total_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {run.total_return?.toFixed(2)}%
                      </td>
                      <td className="text-right py-2 px-2 font-mono text-slate-300">{run.sharpe?.toFixed(2)}</td>
                      <td className="text-right py-2 px-2 font-mono text-red-400">{run.max_drawdown?.toFixed(2)}%</td>
                      <td className="text-right py-2 px-2 font-mono text-slate-300">{run.win_rate?.toFixed(1)}%</td>
                      <td className="text-right py-2 px-2 font-mono text-slate-300">{run.profit_factor?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Equity overlay */}
          {overlayData.length > 1 ? (
            <div className="h-[280px]">
              <h4 className="text-[10px] font-black text-slate-400 mb-2 uppercase tracking-widest flex items-center gap-1">
                <Trophy size={12} /> Equity Curve Overlay
              </h4>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={overlayData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 8, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 8, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#131c31', border: '1px solid #1e293b', fontSize: 10 }} />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  {allRuns.map((run, idx) => (
                    <Line
                      key={idx}
                      type="monotone"
                      dataKey={`run_${idx}`}
                      name={run.label || run.symbol}
                      stroke={COLORS[idx % COLORS.length]}
                      dot={false}
                      strokeWidth={2}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-[10px] text-slate-500 text-center py-4">Pin at least 2 runs to see equity overlay</p>
          )}
        </>
      )}
    </div>
  );
};
