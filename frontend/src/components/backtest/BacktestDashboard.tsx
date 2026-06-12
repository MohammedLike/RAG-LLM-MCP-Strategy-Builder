import { useState } from 'react';
import { useBacktestStore } from '../../stores/backtestStore';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { BarChart3, List, Activity, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export const BacktestDashboard = () => {
  const { latestBacktest, loading, error } = useBacktestStore();
  const [chartType, setChartType] = useState<'equity' | 'drawdown'>('equity');

  if (error) {
    return (
      <div className="bg-red-950/20 border border-red-900/50 text-red-300 p-6 rounded-lg shadow-xl flex flex-col justify-center items-center text-center">
        <Activity className="text-red-500 mb-3" size={36} />
        <h4 className="font-bold text-sm uppercase tracking-tight">Execution Error</h4>
        <p className="text-xs text-red-400/80 mt-1 max-w-md font-medium">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-[#0a0e17] border border-slate-800/80 rounded-xl p-10 text-slate-100 shadow-2xl min-h-[400px] flex flex-col items-center justify-center text-center">
        <div className="relative h-14 w-14 mb-5">
          <div className="absolute inset-0 rounded-full border-[3px] border-[#00d09c]/10"></div>
          <div className="absolute inset-0 rounded-full border-[3px] border-[#00d09c] border-t-transparent animate-spin"></div>
        </div>
        <h4 className="font-black text-sm text-slate-100 tracking-tight uppercase">Running Quantitative Simulation</h4>
        <p className="text-[10px] text-slate-500 mt-1.5 font-bold uppercase tracking-widest">Processing NSE Ticker Data & Signals</p>
      </div>
    );
  }

  if (!latestBacktest) {
    return (
      <div className="bg-[#0a0e17] border border-slate-800/50 rounded-xl p-10 text-slate-100 shadow-2xl min-h-[400px] flex flex-col items-center justify-center text-center border-dashed">
        <div className="h-16 w-16 rounded-2xl bg-slate-900/50 flex items-center justify-center border border-slate-800 mb-4">
          <BarChart3 className="text-slate-600" size={32} />
        </div>
        <h4 className="font-black text-sm text-slate-200 uppercase tracking-tight">System Ready for Analysis</h4>
        <p className="text-xs text-slate-500 mt-2 max-w-sm leading-relaxed">
          Design your strategy in the builder or use natural language in the AI panel to generate performance visualizations.
        </p>
      </div>
    );
  }

  const metrics = [
    { label: 'Total Return', value: `${latestBacktest.total_return.toFixed(2)}%`, key: 'total_return', sub: `Benchmark: ${latestBacktest.benchmark_return.toFixed(2)}%` },
    { label: 'Sharpe Ratio', value: latestBacktest.sharpe.toFixed(2), key: 'sharpe', sub: 'Risk-adjusted return' },
    { label: 'Sortino Ratio', value: latestBacktest.sortino.toFixed(2), key: 'sortino', sub: 'Downside risk filter' },
    { label: 'Max Drawdown', value: `-${latestBacktest.max_drawdown.toFixed(2)}%`, key: 'max_drawdown', sub: 'Peak-to-trough drop', bad: true },
    { label: 'Win Rate', value: `${latestBacktest.win_rate.toFixed(2)}%`, key: 'win_rate', sub: 'Hit accuracy' },
    { label: 'Expectancy', value: latestBacktest.expectancy.toFixed(2), key: 'expectancy', sub: 'Return per trade' },
  ];

  return (
    <div className="flex flex-col gap-6 text-slate-100 pb-10">
      
      {/* Run Metadata Header */}
      <div className="flex justify-between items-center bg-[#0a0e17] p-4 border border-slate-800/80 rounded-lg">
        <div className="flex items-center gap-4">
          <div className="bg-[#00d09c]/10 px-3 py-1.5 rounded border border-[#00d09c]/20">
            <h4 className="font-mono text-sm font-black text-[#00d09c]">{latestBacktest.symbol}</h4>
          </div>
          <div className="flex flex-col">
            <span className="text-[9px] uppercase tracking-widest text-slate-500 font-black">Time Period</span>
            <span className="text-[10px] text-slate-200 font-bold uppercase">{latestBacktest.period} (Daily)</span>
          </div>
          <div className="h-6 w-px bg-slate-800/80"></div>
          <div className="flex flex-col">
            <span className="text-[9px] uppercase tracking-widest text-slate-500 font-black">Execution Time</span>
            <span className="text-[10px] text-slate-400 font-bold">{latestBacktest.timestamp ? new Date(latestBacktest.timestamp).toLocaleTimeString() : 'N/A'}</span>
          </div>
        </div>
        <div className="flex bg-slate-900/50 p-1 rounded border border-slate-800/80">
          <button
            onClick={() => setChartType('equity')}
            className={`px-4 py-1.5 rounded text-[10px] font-black tracking-widest transition cursor-pointer ${
              chartType === 'equity' ? 'bg-[#00d09c] text-[#06090f]' : 'text-slate-500 hover:text-slate-200'
            }`}
          >
            EQUITY
          </button>
          <button
            onClick={() => setChartType('drawdown')}
            className={`px-4 py-1.5 rounded text-[10px] font-black tracking-widest transition cursor-pointer ${
              chartType === 'drawdown' ? 'bg-red-500 text-white' : 'text-slate-500 hover:text-slate-200'
            }`}
          >
            DRAWDOWN
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {metrics.map((m) => (
          <div key={m.label} className="bg-[#0a0e17] border border-slate-800/80 rounded-lg p-4 flex flex-col shadow-xl relative overflow-hidden hover:border-[#00d09c]/30 transition group">
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{m.label}</span>
            <span className={`text-xl font-black font-mono mt-1 ${m.bad ? 'text-red-400' : 'text-[#00d09c]'}`}>
              {m.value}
            </span>
            <span className="text-[9px] text-slate-600 mt-2 font-bold uppercase truncate">{m.sub}</span>
            <div className={`absolute bottom-0 left-0 h-0.5 bg-current transition-all duration-300 w-0 group-hover:w-full ${m.bad ? 'text-red-500' : 'text-[#00d09c]'}`}></div>
          </div>
        ))}
      </div>

      {/* Chart Section */}
      <div className="bg-[#0a0e17] border border-slate-800/80 rounded-lg p-6 shadow-2xl min-h-[400px]">
        <div className="flex items-center gap-2 mb-6 border-b border-slate-800/50 pb-4">
          <div className={`h-2 w-2 rounded-full ${chartType === 'equity' ? 'bg-[#00d09c]' : 'bg-red-500'}`}></div>
          <h3 className="font-black text-slate-200 text-xs uppercase tracking-widest">
            {chartType === 'equity' ? 'Growth Performance Analysis' : 'Risk Exposure & Drawdowns'}
          </h3>
        </div>
        
        {chartType === 'equity' ? (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={latestBacktest.equity_curve}>
              <defs>
                <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d09c" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#00d09c" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} strokeOpacity={0.2} />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 9, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0a0e17', border: '1px solid #1e293b', borderRadius: 4, color: '#f8fafc', fontSize: 11 }}
                labelStyle={{ fontWeight: 'black', color: '#94a3b8', marginBottom: 4 }}
                itemStyle={{ fontWeight: 'black', color: '#00d09c' }}
              />
              <Area type="monotone" dataKey="value" stroke="#00d09c" fill="url(#colorEquity)" strokeWidth={2} name="NAV" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={latestBacktest.drawdown}>
              <defs>
                <linearGradient id="colorDD" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} strokeOpacity={0.2} />
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 9, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0a0e17', border: '1px solid #1e293b', borderRadius: 4, color: '#f8fafc', fontSize: 11 }}
                labelStyle={{ fontWeight: 'black', color: '#94a3b8', marginBottom: 4 }}
                itemStyle={{ fontWeight: 'black', color: '#ef4444' }}
              />
              <Area type="monotone" dataKey="value" stroke="#ef4444" fill="url(#colorDD)" strokeWidth={2} name="Drawdown %" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Trade Log Section */}
      <div className="bg-[#0a0e17] border border-slate-800/80 rounded-lg p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-6 border-b border-slate-800/50 pb-4">
          <div className="flex items-center gap-2">
            <List className="text-[#00d09c]" size={14} />
            <h3 className="font-black text-slate-200 text-xs uppercase tracking-widest">Order Log ({latestBacktest.trades.length} Positions)</h3>
          </div>
          <span className="text-[9px] font-black bg-[#00d09c]/10 text-[#00d09c] px-2 py-0.5 rounded border border-[#00d09c]/20 uppercase tracking-tighter">NSE Delivery/Intraday</span>
        </div>
        <div className="overflow-x-auto max-h-[350px] scrollbar-thin scrollbar-thumb-slate-800 pr-1">
          <table className="w-full text-xs text-left text-slate-300">
            <thead className="bg-slate-900/50 text-slate-500 uppercase text-[9px] font-black sticky top-0">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Entry</th>
                <th className="px-4 py-3">Exit</th>
                <th className="px-4 py-3">Entry Price</th>
                <th className="px-4 py-3">Exit Price</th>
                <th className="px-4 py-3">PnL</th>
                <th className="px-4 py-3">Return %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {latestBacktest.trades.length > 0 ? (
                latestBacktest.trades.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/30 transition group">
                    <td className="px-4 py-3 font-mono text-[10px] text-slate-600 group-hover:text-slate-400">#{t.id}</td>
                    <td className="px-4 py-3 font-bold text-slate-400">{t.entry_date}</td>
                    <td className="px-4 py-3 font-bold text-slate-400">{t.exit_date}</td>
                    <td className="px-4 py-3 font-mono font-bold">{t.entry_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
                    <td className="px-4 py-3 font-mono font-bold">{t.exit_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
                    <td className={`px-4 py-3 font-black ${t.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {t.pnl >= 0 ? '+' : ''}{t.pnl.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                    <td className={`px-4 py-3`}>
                      <span className={`px-2 py-0.5 rounded-sm font-black font-mono text-[10px] ${t.pnl_pct >= 0 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                        {t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct.toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Activity size={24} className="text-slate-700" />
                      <span className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">No executable signals found in period</span>
                    </div>
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
