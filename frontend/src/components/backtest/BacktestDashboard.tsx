import { useState } from 'react';
import { useBacktestStore } from '../../stores/backtestStore';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { BarChart3, List, Activity, Settings2, LineChart, Layers, PieChart } from 'lucide-react';
import { StrategyMetricsKPI } from './StrategyMetricsKPI';
import { MonthlyReturnsHeatmap } from './MonthlyReturnsHeatmap';
import { RollingMetricsChart } from './RollingMetricsChart';
import { MonteCarloSimulation } from './MonteCarloSimulation';
import { TradeDistribution } from './TradeDistribution';
import { ParameterOptimizer } from './ParameterOptimizer';
import { BacktestComparison } from './BacktestComparison';

export const BacktestDashboard = () => {
  const { latestBacktest, loading, error } = useBacktestStore();
  const [chartType, setChartType] = useState<'equity' | 'drawdown'>('equity');
  const [activeSubTab, setActiveSubTab] = useState<'summary' | 'performance' | 'trades' | 'optimize' | 'compare'>('summary');

  if (error) {
    return (
      <div className="bg-red-950/20 border border-red-900/50 text-red-300 p-6 rounded-lg shadow-xl flex flex-col justify-center items-center text-center h-full">
        <Activity className="text-red-500 mb-3" size={36} />
        <h4 className="font-bold text-sm uppercase tracking-tight">Execution Error</h4>
        <p className="text-xs text-red-400/80 mt-1 max-w-md font-medium">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-[#131c31] border border-slate-800/80 rounded-xl p-10 text-slate-100 shadow-2xl h-full flex flex-col items-center justify-center text-center">
        <div className="relative h-14 w-14 mb-5">
          <div className="absolute inset-0 rounded-full border-[3px] border-[#3b82f6]/10"></div>
          <div className="absolute inset-0 rounded-full border-[3px] border-[#3b82f6] border-t-transparent animate-spin"></div>
        </div>
        <h4 className="font-black text-sm text-slate-100 tracking-tight uppercase">Running Quantitative Simulation</h4>
        <p className="text-[10px] text-slate-500 mt-1.5 font-bold uppercase tracking-widest">Processing NSE Ticker Data & Signals</p>
      </div>
    );
  }

  if (!latestBacktest) {
    return (
      <div className="bg-[#131c31] border border-slate-800/50 rounded-xl p-10 text-slate-100 shadow-2xl h-full flex flex-col items-center justify-center text-center border-dashed">
        <div className="h-16 w-16 rounded-2xl bg-slate-900/50 flex items-center justify-center border border-slate-800 mb-4">
          <BarChart3 className="text-slate-600" size={32} />
        </div>
        <h4 className="font-black text-sm text-slate-200 uppercase tracking-tight">System Ready for Analysis</h4>
        <p className="text-xs text-slate-500 mt-2 max-w-sm leading-relaxed font-medium">
          Design your strategy in the builder or use natural language in the AI panel to generate performance visualizations.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 text-slate-100 pb-10">
      
      {/* Run Metadata Header */}
      <div className="flex justify-between items-center bg-[#131c31] p-4 border border-slate-800/80 rounded-lg shadow-lg">
        <div className="flex items-center gap-4">
          <div className="bg-[#3b82f6]/10 px-3 py-1.5 rounded border border-[#3b82f6]/20">
            <h4 className="font-mono text-sm font-black text-[#3b82f6]">{latestBacktest.symbol}</h4>
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
      </div>

      {/* Internal Tabs */}
      <div className="flex bg-[#131c31] p-1 border border-slate-800/80 rounded-lg max-w-fit shadow-lg">
        <button
          onClick={() => setActiveSubTab('summary')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded text-[10px] font-black uppercase tracking-widest transition cursor-pointer ${
            activeSubTab === 'summary' ? 'bg-slate-800 text-slate-100' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <BarChart3 size={14} /> Summary
        </button>
        <button
          onClick={() => setActiveSubTab('performance')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded text-[10px] font-black uppercase tracking-widest transition cursor-pointer ${
            activeSubTab === 'performance' ? 'bg-slate-800 text-slate-100' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <LineChart size={14} /> Advanced Perf
        </button>
        <button
          onClick={() => setActiveSubTab('trades')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded text-[10px] font-black uppercase tracking-widest transition cursor-pointer ${
            activeSubTab === 'trades' ? 'bg-slate-800 text-slate-100' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <List size={14} /> Trade Log
        </button>
        <button
          onClick={() => setActiveSubTab('optimize')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded text-[10px] font-black uppercase tracking-widest transition cursor-pointer ${
            activeSubTab === 'optimize' ? 'bg-slate-800 text-slate-100' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <Settings2 size={14} /> Optimize
        </button>
        <button
          onClick={() => setActiveSubTab('compare')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded text-[10px] font-black uppercase tracking-widest transition cursor-pointer ${
            activeSubTab === 'compare' ? 'bg-slate-800 text-slate-100' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <Layers size={14} /> Compare
        </button>
      </div>

      {/* Tab Content */}
      
      {/* 1. Summary Tab */}
      {activeSubTab === 'summary' && (
        <div className="flex flex-col gap-4">
          <StrategyMetricsKPI />

          {/* Chart Section */}
          <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-6 shadow-2xl min-h-[350px]">
            <div className="flex items-center justify-between mb-6 border-b border-slate-800/50 pb-4">
              <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${chartType === 'equity' ? 'bg-[#3b82f6]' : 'bg-red-500'}`}></div>
                <h3 className="font-black text-slate-200 text-xs uppercase tracking-widest">
                  {chartType === 'equity' ? 'Growth Performance Analysis' : 'Risk Exposure & Drawdowns'}
                </h3>
              </div>
              <div className="flex bg-slate-900/50 p-1 rounded border border-slate-800/80">
                <button
                  onClick={() => setChartType('equity')}
                  className={`px-4 py-1.5 rounded text-[10px] font-black tracking-widest transition cursor-pointer ${
                    chartType === 'equity' ? 'bg-[#3b82f6] text-[#0c1222]' : 'text-slate-500 hover:text-slate-200'
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
            
            {chartType === 'equity' ? (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={latestBacktest.equity_curve}>
                  <defs>
                    <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} strokeOpacity={0.2} />
                  <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} minTickGap={30} />
                  <YAxis tick={{ fontSize: 9, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#131c31', border: '1px solid #1e293b', borderRadius: 4, color: '#f8fafc', fontSize: 11 }}
                    labelStyle={{ fontWeight: 'black', color: '#94a3b8', marginBottom: 4 }}
                    itemStyle={{ fontWeight: 'black', color: '#3b82f6' }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#colorEquity)" strokeWidth={2} name="NAV" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={latestBacktest.drawdown}>
                  <defs>
                    <linearGradient id="colorDD" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} strokeOpacity={0.2} />
                  <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} minTickGap={30} />
                  <YAxis tick={{ fontSize: 9, fill: '#64748b', fontWeight: 'bold' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#131c31', border: '1px solid #1e293b', borderRadius: 4, color: '#f8fafc', fontSize: 11 }}
                    labelStyle={{ fontWeight: 'black', color: '#94a3b8', marginBottom: 4 }}
                    itemStyle={{ fontWeight: 'black', color: '#ef4444' }}
                  />
                  <Area type="monotone" dataKey="value" stroke="#ef4444" fill="url(#colorDD)" strokeWidth={2} name="Drawdown %" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}

      {/* 2. Advanced Performance Tab */}
      {activeSubTab === 'performance' && (
        <div className="flex flex-col gap-4">
          <MonthlyReturnsHeatmap />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <RollingMetricsChart />
            <MonteCarloSimulation />
          </div>
        </div>
      )}

      {/* 3. Trades Tab */}
      {activeSubTab === 'trades' && (
        <div className="flex flex-col gap-4">
          <TradeDistribution />
          <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6 border-b border-slate-800/50 pb-4">
              <div className="flex items-center gap-2">
                <List className="text-[#3b82f6]" size={14} />
                <h3 className="font-black text-slate-200 text-xs uppercase tracking-widest">Order Log ({latestBacktest.trades.length} Positions)</h3>
              </div>
            </div>
            <div className="overflow-x-auto max-h-[350px] scrollbar-thin scrollbar-thumb-slate-800 pr-1">
              <table className="w-full text-xs text-left text-slate-300">
                <thead className="bg-slate-900/50 text-slate-500 uppercase text-[9px] font-black sticky top-0">
                  <tr>
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Entry</th>
                    <th className="px-4 py-3">Exit</th>
                    <th className="px-4 py-3">Dir</th>
                    <th className="px-4 py-3 text-right">Entry Price</th>
                    <th className="px-4 py-3 text-right">Exit Price</th>
                    <th className="px-4 py-3 text-right">PnL</th>
                    <th className="px-4 py-3 text-right">Return %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40">
                  {latestBacktest.trades.length > 0 ? (
                    latestBacktest.trades.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-800/30 transition group">
                        <td className="px-4 py-3 font-mono text-[10px] text-slate-600 group-hover:text-slate-400">#{t.id}</td>
                        <td className="px-4 py-3 font-bold text-slate-400">{t.entry_date}</td>
                        <td className="px-4 py-3 font-bold text-slate-400">{t.exit_date}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${t.direction === 'Short' ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'}`}>
                            {t.direction}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono font-bold text-right">{t.entry_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
                        <td className="px-4 py-3 font-mono font-bold text-right">{t.exit_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
                        <td className={`px-4 py-3 font-black text-right ${t.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {t.pnl >= 0 ? '+' : ''}{t.pnl.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className={`px-2 py-0.5 rounded-sm font-black font-mono text-[10px] ${t.pnl_pct >= 0 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                            {t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct.toFixed(2)}%
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="px-4 py-12 text-center">
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
      )}

      {/* 4. Optimize Tab */}
      {activeSubTab === 'optimize' && <ParameterOptimizer />}

      {/* 5. Compare Tab */}
      {activeSubTab === 'compare' && <BacktestComparison />}

    </div>
  );
};

