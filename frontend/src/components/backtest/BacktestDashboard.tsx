import { useState } from 'react';
import { useBacktestStore } from '../../stores/backtestStore';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { BarChart3, List, Activity, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export const BacktestDashboard = () => {
  const { latestBacktest, loading, error } = useBacktestStore();
  const [chartType, setChartType] = useState<'equity' | 'drawdown'>('equity');

  if (error) {
    return (
      <div className="bg-red-950/40 border border-red-900 text-red-300 p-5 rounded-xl shadow-xl flex flex-col justify-center items-center text-center">
        <Activity className="text-red-500 mb-2" size={32} />
        <h4 className="font-bold text-sm">Backtest Execution Failure</h4>
        <p className="text-xs text-red-400 mt-1 max-w-md">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-8 text-slate-100 shadow-xl min-h-[400px] flex flex-col items-center justify-center text-center">
        <div className="relative h-12 w-12 mb-4">
          <div className="absolute inset-0 rounded-full border-4 border-blue-500/20"></div>
          <div className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
        </div>
        <h4 className="font-bold text-sm text-slate-200">Processing Vectorized Backtest...</h4>
        <p className="text-xs text-slate-500 mt-1">Downloading daily ticker data and computing signals</p>
      </div>
    );
  }

  if (!latestBacktest) {
    return (
      <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-8 text-slate-100 shadow-xl min-h-[400px] flex flex-col items-center justify-center text-center border-dashed">
        <BarChart3 className="text-slate-700 mb-3 animate-pulse" size={40} />
        <h4 className="font-bold text-sm text-slate-300">No Backtest Session Loaded</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-md">
          Create rules in the strategy console, click run, or ask the AI assistant directly to visualize performance.
        </p>
      </div>
    );
  }

  const metrics = [
    { label: 'Total Return', value: `${latestBacktest.total_return.toFixed(2)}%`, key: 'total_return', sub: `Benchmark: ${latestBacktest.benchmark_return.toFixed(2)}%` },
    { label: 'Sharpe Ratio', value: latestBacktest.sharpe.toFixed(2), key: 'sharpe', sub: 'Risk-adjusted return' },
    { label: 'Sortino Ratio', value: latestBacktest.sortino.toFixed(2), key: 'sortino', sub: 'Downside risk filter' },
    { label: 'Max Drawdown', value: `-${latestBacktest.max_drawdown.toFixed(2)}%`, key: 'max_drawdown', sub: 'Peak-to-trough drop', bad: true },
    { label: 'Win Rate', value: `${latestBacktest.win_rate.toFixed(2)}%`, key: 'win_rate', sub: 'Percentage of winning trades' },
    { label: 'Expectancy', value: latestBacktest.expectancy.toFixed(2), key: 'expectancy', sub: 'Expected profit per trade' },
  ];

  return (
    <div className="flex flex-col gap-6 text-slate-100">
      
      {/* Run Metadata Header */}
      <div className="flex justify-between items-end bg-slate-900/40 p-4 border border-slate-800/80 rounded-xl">
        <div>
          <span className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">Latest Run Configuration</span>
          <div className="flex items-center gap-3 mt-1">
            <h4 className="font-mono text-base font-bold text-blue-400">{latestBacktest.symbol}</h4>
            <span className="h-3 w-px bg-slate-800"></span>
            <span className="text-xs text-slate-300">Period: {latestBacktest.period}</span>
            <span className="h-3 w-px bg-slate-800"></span>
            <span className="text-[10px] text-slate-400">Run: {latestBacktest.timestamp ? new Date(latestBacktest.timestamp).toLocaleTimeString() : 'N/A'}</span>
          </div>
        </div>
        <div className="flex bg-slate-950 p-0.5 rounded border border-slate-800/80 text-[10px]">
          <button
            onClick={() => setChartType('equity')}
            className={`px-3 py-1 rounded font-semibold transition cursor-pointer ${
              chartType === 'equity' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Equity Curve
          </button>
          <button
            onClick={() => setChartType('drawdown')}
            className={`px-3 py-1 rounded font-semibold transition cursor-pointer ${
              chartType === 'drawdown' ? 'bg-red-950 text-red-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Drawdown
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {metrics.map((m) => (
          <div key={m.label} className="bg-[#0b0f19] border border-slate-800 rounded-xl p-4 flex flex-col shadow-md relative overflow-hidden group hover:border-slate-700 transition">
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">{m.label}</span>
            <span className={`text-xl font-bold font-mono mt-1 ${m.bad ? 'text-red-400' : 'text-slate-100'}`}>
              {m.value}
            </span>
            <span className="text-[9px] text-slate-500 mt-2 font-medium truncate">{m.sub}</span>
          </div>
        ))}
      </div>

      {/* Chart Section */}
      <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-5 shadow-xl min-h-[380px]">
        <div className="flex items-center gap-2 mb-4 border-b border-slate-800/80 pb-3">
          <BarChart3 className="text-blue-500" size={16} />
          <h3 className="font-bold text-slate-100 text-sm">
            {chartType === 'equity' ? 'Equity Performance Curve' : 'Peak Drawdown Timeline'}
          </h3>
        </div>
        
        {chartType === 'equity' ? (
          <ResponsiveContainer width="100%" height={290}>
            <AreaChart data={latestBacktest.equity_curve}>
              <defs>
                <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1d4ed8" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="#1d4ed8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: '#f8fafc', fontSize: 11 }}
                labelStyle={{ fontWeight: 'bold' }}
              />
              <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#colorEquity)" strokeWidth={2} name="Equity ($)" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={290}>
            <AreaChart data={latestBacktest.drawdown}>
              <defs>
                <linearGradient id="colorDD" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: 8, color: '#f8fafc', fontSize: 11 }}
                labelStyle={{ fontWeight: 'bold' }}
              />
              <Area type="monotone" dataKey="value" stroke="#ef4444" fill="url(#colorDD)" strokeWidth={2} name="Drawdown (%)" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Trade Log Section */}
      <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-5 shadow-xl">
        <div className="flex items-center gap-2 mb-4 border-b border-slate-800/80 pb-3">
          <List className="text-blue-500" size={16} />
          <h3 className="font-bold text-slate-100 text-sm">Strategy Transactions Log ({latestBacktest.trades.length} Executed)</h3>
        </div>
        <div className="overflow-x-auto max-h-[250px] scrollbar-thin scrollbar-thumb-slate-800 pr-1">
          <table className="w-full text-xs text-left text-slate-300">
            <thead className="bg-slate-950 text-slate-500 uppercase text-[9px] font-bold sticky top-0">
              <tr>
                <th className="px-4 py-2">ID</th>
                <th className="px-4 py-2">Entry Date</th>
                <th className="px-4 py-2">Exit Date</th>
                <th className="px-4 py-2">Entry Price</th>
                <th className="px-4 py-2">Exit Price</th>
                <th className="px-4 py-2">PnL %</th>
                <th className="px-4 py-2">Return</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {latestBacktest.trades.length > 0 ? (
                latestBacktest.trades.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-900/40 transition">
                    <td className="px-4 py-2.5 font-mono text-[10px] text-slate-500">#{t.id}</td>
                    <td className="px-4 py-2.5 font-medium">{t.entry_date}</td>
                    <td className="px-4 py-2.5 font-medium">{t.exit_date}</td>
                    <td className="px-4 py-2.5 font-mono font-medium">{t.entry_price.toFixed(2)}</td>
                    <td className="px-4 py-2.5 font-mono font-medium">{t.exit_price.toFixed(2)}</td>
                    <td className={`px-4 py-2.5 font-bold flex items-center gap-1 ${t.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {t.pnl >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                      {t.pnl >= 0 ? '+' : ''}{t.pnl.toFixed(2)}
                    </td>
                    <td className={`px-4 py-2.5 font-bold font-mono ${t.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct.toFixed(2)}%
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                    No trades executed. Adjust your conditions or try a different asset/lookback.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
