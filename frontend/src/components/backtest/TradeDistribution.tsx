import React from 'react';
import { useBacktestStore } from '../../stores/backtestStore';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';

export const TradeDistribution = () => {
  const { latestBacktest } = useBacktestStore();

  if (!latestBacktest || !latestBacktest.trades || latestBacktest.trades.length === 0) {
    return <div className="text-slate-500 text-xs p-4 text-center">No trades available for distribution analysis.</div>;
  }

  // Bucket trades by PnL %
  const buckets: Record<string, number> = {};
  const bucketSize = 1.0; // 1% buckets

  latestBacktest.trades.forEach(t => {
    const pnl = t.pnl_pct;
    // Round to nearest bucket
    const bucket = Math.floor(pnl / bucketSize) * bucketSize;
    const key = `${bucket.toFixed(1)}% to ${(bucket + bucketSize).toFixed(1)}%`;
    buckets[key] = (buckets[key] || 0) + 1;
  });

  const data = Object.keys(buckets)
    .sort((a, b) => parseFloat(a) - parseFloat(b))
    .map(k => ({
      range: k,
      count: buckets[k],
      isProfit: parseFloat(k) >= 0
    }));

  return (
    <div className="bg-[#0a0e17] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full h-[300px] flex flex-col">
      <h3 className="text-xs font-black text-slate-200 uppercase tracking-widest mb-4">Trade P&L Distribution</h3>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <XAxis dataKey="range" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0a0e17', border: '1px solid #1e293b', borderRadius: 4, color: '#f8fafc', fontSize: 11 }}
              labelStyle={{ fontWeight: 'black', color: '#94a3b8', marginBottom: 4 }}
              cursor={{fill: '#1e293b', opacity: 0.4}}
            />
            <ReferenceLine x="0.0% to 1.0%" stroke="#475569" strokeDasharray="3 3" />
            <Bar dataKey="count" radius={[2, 2, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.isProfit ? '#00d09c' : '#ef4444'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
