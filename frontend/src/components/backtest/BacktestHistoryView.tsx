import { useEffect } from 'react';
import { History, Play, Loader2 } from 'lucide-react';
import { useBacktestStore } from '../../stores/backtestStore';

interface BacktestHistoryViewProps {
  onRunStrategy?: () => void;
  onLoaded?: () => void;
}

export const BacktestHistoryView = ({ onRunStrategy, onLoaded }: BacktestHistoryViewProps) => {
  const { history, fetchHistory, loadBacktestById, loading } = useBacktestStore();

  useEffect(() => {
    fetchHistory(50);
  }, [fetchHistory]);

  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <History className="text-brand" size={22} />
          <div>
            <h2 className="text-lg font-bold text-white">Backtest History</h2>
            <p className="text-xs text-slate-500">All persisted runs from Postgres</p>
          </div>
        </div>
        <button
          onClick={() => fetchHistory(50)}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-bold cursor-pointer"
        >
          Refresh
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-brand" size={32} />
        </div>
      )}

      {!loading && history.length === 0 && (
        <div className="text-center py-20 bg-slate-900/40 border border-slate-800 rounded-xl">
          <History size={40} className="mx-auto text-slate-700 mb-4" />
          <h3 className="text-slate-400 font-bold">No backtest history yet</h3>
          <p className="text-slate-600 text-sm mt-2">Run your first backtest to see results here.</p>
          {onRunStrategy && (
            <button onClick={onRunStrategy} className="mt-4 px-4 py-2 bg-brand text-white rounded-lg text-xs font-bold cursor-pointer">
              Go to Strategy Builder
            </button>
          )}
        </div>
      )}

      {history.length > 0 && (
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/80 text-slate-500 text-[10px] uppercase font-black">
              <tr>
                <th className="text-left px-4 py-3">Symbol</th>
                <th className="text-left px-4 py-3">Period</th>
                <th className="text-left px-4 py-3">Label</th>
                <th className="text-right px-4 py-3">Return</th>
                <th className="text-right px-4 py-3">Sharpe</th>
                <th className="text-right px-4 py-3">Max DD</th>
                <th className="text-right px-4 py-3">Trades</th>
                <th className="text-right px-4 py-3">Date</th>
                <th className="text-right px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {history.map((row: any) => (
                <tr key={row.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-4 py-3 font-mono font-bold text-brand">{row.symbol}</td>
                  <td className="px-4 py-3 text-slate-400">{row.period}</td>
                  <td className="px-4 py-3 text-slate-300 text-xs">{row.strategy_label || '—'}</td>
                  <td className={`px-4 py-3 text-right font-mono font-bold ${(row.total_return ?? 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {(row.total_return ?? 0).toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-slate-300">{(row.sharpe ?? 0).toFixed(2)}</td>
                  <td className="px-4 py-3 text-right font-mono text-red-400">{(row.max_drawdown ?? 0).toFixed(2)}%</td>
                  <td className="px-4 py-3 text-right text-slate-400">{row.trade_count ?? '—'}</td>
                  <td className="px-4 py-3 text-right text-slate-500 text-xs">
                    {row.created_at ? new Date(row.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={async () => {
                        await loadBacktestById(row.id);
                        onLoaded?.();
                      }}
                      className="px-2 py-1 bg-brand/20 hover:bg-brand/30 text-brand rounded text-[10px] font-bold flex items-center gap-1 ml-auto cursor-pointer"
                    >
                      <Play size={10} /> Load
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
