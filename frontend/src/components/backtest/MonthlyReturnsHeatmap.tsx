import { useBacktestStore } from '../../stores/backtestStore';

export const MonthlyReturnsHeatmap = () => {
  const { latestBacktest } = useBacktestStore();

  if (!latestBacktest) {
    return <div className="text-slate-500 text-xs p-4 text-center">Run a backtest to see monthly returns.</div>;
  }

  const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  // Prefer backend-computed monthly_returns from equity curve
  const backendData = latestBacktest.monthly_returns;
  let years: string[] = [];
  const monthlyPnL: Record<string, number> = {};

  if (backendData && Object.keys(backendData).length > 0) {
    years = Object.keys(backendData).sort().reverse();
    years.forEach((year) => {
      const row = backendData[year];
      row.forEach((val, idx) => {
        if (val !== null && val !== undefined) {
          const month = String(idx + 1).padStart(2, '0');
          monthlyPnL[`${year}-${month}`] = val;
        }
      });
    });
  } else if (latestBacktest.trades?.length) {
    latestBacktest.trades.forEach((trade) => {
      if (!trade.exit_date) return;
      const monthKey = trade.exit_date.substring(0, 7);
      monthlyPnL[monthKey] = (monthlyPnL[monthKey] || 0) + trade.pnl_pct;
    });
    years = Array.from(new Set(Object.keys(monthlyPnL).map((k) => k.substring(0, 4)))).sort().reverse();
  } else {
    return <div className="text-slate-500 text-xs p-4 text-center">Insufficient data for monthly heatmap.</div>;
  }

  const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];

  const getHeatmapColor = (val: number | undefined) => {
    if (val === undefined || isNaN(val)) return 'bg-slate-900/40 text-slate-600';
    if (val > 0) return 'bg-[#3b82f6] text-[#0c1222] font-bold';
    if (val < 0) return 'bg-red-500 text-white font-bold';
    return 'bg-slate-800 text-slate-400';
  };

  return (
    <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full">
      <h3 className="text-xs font-black text-slate-200 uppercase tracking-widest mb-4">Monthly Return Heatmap</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-center border-collapse">
          <thead>
            <tr>
              <th className="p-2 text-slate-500 font-bold uppercase">Year</th>
              {monthLabels.map((m) => (
                <th key={m} className="p-2 text-slate-500 font-bold uppercase">{m}</th>
              ))}
              <th className="p-2 text-slate-300 font-black uppercase">YTD</th>
            </tr>
          </thead>
          <tbody>
            {years.map((year) => {
              let ytd = 0;
              return (
                <tr key={year} className="border-t border-slate-800/40">
                  <td className="p-2 font-mono text-slate-400 font-bold">{year}</td>
                  {months.map((month) => {
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
                  <td className={`p-2 font-mono font-black ${ytd >= 0 ? 'text-[#3b82f6]' : 'text-red-500'}`}>
                    {ytd > 0 ? '+' : ''}{ytd.toFixed(1)}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
