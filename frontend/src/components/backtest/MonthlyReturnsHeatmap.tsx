import React from 'react';
import { useBacktestStore } from '../../stores/backtestStore';

export const MonthlyReturnsHeatmap = () => {
  const { latestBacktest } = useBacktestStore();

  if (!latestBacktest || !latestBacktest.trades || latestBacktest.trades.length === 0) {
    return <div className="text-slate-500 text-xs p-4 text-center">Insufficient trade data for monthly heatmap.</div>;
  }

  // Aggregate trades by YYYY-MM
  const monthlyPnL: Record<string, number> = {};
  
  latestBacktest.trades.forEach(trade => {
    // Assuming entry_date or exit_date is format YYYY-MM-DD
    if (!trade.exit_date) return;
    const monthKey = trade.exit_date.substring(0, 7); // YYYY-MM
    monthlyPnL[monthKey] = (monthlyPnL[monthKey] || 0) + trade.pnl_pct;
  });

  const years = Array.from(new Set(Object.keys(monthlyPnL).map(k => k.substring(0, 4)))).sort().reverse();
  const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
  const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  const getHeatmapColor = (val: number) => {
    if (val === undefined || isNaN(val)) return 'bg-slate-900/40 text-slate-600';
    if (val > 0) {
      const intensity = Math.min(val / 10, 1); // Cap at 10% for color
      return `bg-[#00d09c] text-[#06090f] font-bold`} 
    else if (val < 0) {
      const intensity = Math.min(Math.abs(val) / 10, 1);
      return `bg-red-500 text-white font-bold`;
    }
    return 'bg-slate-800 text-slate-400';
  };

  return (
    <div className="bg-[#0a0e17] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full">
      <h3 className="text-xs font-black text-slate-200 uppercase tracking-widest mb-4">Monthly Return Distribution</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-center border-collapse">
          <thead>
            <tr>
              <th className="p-2 text-slate-500 font-bold uppercase">Year</th>
              {monthLabels.map(m => (
                <th key={m} className="p-2 text-slate-500 font-bold uppercase">{m}</th>
              ))}
              <th className="p-2 text-slate-300 font-black uppercase">YTD</th>
            </tr>
          </thead>
          <tbody>
            {years.map(year => {
              let ytd = 0;
              return (
                <tr key={year} className="border-t border-slate-800/40">
                  <td className="p-2 font-mono text-slate-400 font-bold">{year}</td>
                  {months.map(month => {
                    const key = `${year}-${month}`;
                    const val = monthlyPnL[key];
                    if (val !== undefined) ytd += val;
                    return (
                      <td key={key} className="p-1">
                        <div className={`h-8 w-12 flex items-center justify-center rounded text-[10px] mx-auto transition-all ${getHeatmapColor(val)}`}>
                          {val !== undefined ? `${val.toFixed(1)}%` : '-'}
                        </div>
                      </td>
                    );
                  })}
                  <td className={`p-2 font-mono font-black ${ytd >= 0 ? 'text-[#00d09c]' : 'text-red-500'}`}>
                    {ytd > 0 ? '+' : ''}{ytd.toFixed(1)}%
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
