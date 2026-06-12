import React from 'react';
import { useBacktestStore } from '../../stores/backtestStore';

export const StrategyMetricsKPI = () => {
  const { latestBacktest } = useBacktestStore();

  if (!latestBacktest) return null;

  // We map the existing backend metrics. Assuming backend returns the extended metrics later, 
  // we fallback gracefully or calculate what we can.
  
  const cagr = latestBacktest.cagr ?? (latestBacktest.total_return / 2); // Approximation if missing
  const maxDd = latestBacktest.max_drawdown;
  const calmar = maxDd > 0 ? (cagr / maxDd) : 0;
  
  const metrics = [
    { label: 'CAGR (Ann. Return)', value: `${cagr.toFixed(2)}%`, sub: 'Compound Annual Growth Rate', bad: cagr < 0 },
    { label: 'Max Drawdown', value: `-${maxDd.toFixed(2)}%`, sub: 'Peak-to-trough decline', bad: true },
    { label: 'Calmar Ratio', value: calmar.toFixed(2), sub: 'CAGR / Max Drawdown', bad: calmar < 1 },
    { label: 'Sharpe Ratio', value: latestBacktest.sharpe.toFixed(2), sub: 'Risk-adjusted return', bad: latestBacktest.sharpe < 1 },
    { label: 'Sortino Ratio', value: latestBacktest.sortino.toFixed(2), sub: 'Downside risk filter', bad: latestBacktest.sortino < 1 },
    { label: 'Win Rate', value: `${latestBacktest.win_rate.toFixed(2)}%`, sub: 'Profitable trades / Total trades', bad: latestBacktest.win_rate < 50 },
    { label: 'Profit Factor', value: latestBacktest.profit_factor.toFixed(2), sub: 'Gross Profit / Gross Loss', bad: latestBacktest.profit_factor < 1 },
    { label: 'Expectancy', value: latestBacktest.expectancy.toFixed(2), sub: 'Average PnL per trade', bad: latestBacktest.expectancy < 0 }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {metrics.map((m) => (
        <div key={m.label} className="bg-[#0a0e17] border border-slate-800/80 rounded-lg p-4 flex flex-col shadow-xl relative overflow-hidden group">
          <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">{m.label}</span>
          <span className={`text-xl font-black font-mono mt-1 ${m.bad ? (m.label === 'Max Drawdown' ? 'text-red-400' : 'text-slate-200') : 'text-[#00d09c]'}`}>
            {m.value}
          </span>
          <span className="text-[9px] text-slate-600 mt-2 font-bold uppercase truncate">{m.sub}</span>
        </div>
      ))}
    </div>
  );
};
