import React, { useState, useMemo } from 'react';
import { useBacktestStore } from '../../stores/backtestStore';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export const RollingMetricsChart = () => {
  const { latestBacktest } = useBacktestStore();
  const [metric, setMetric] = useState<'sharpe' | 'drawdown' | 'volatility'>('sharpe');
  const windowSize = 126; // Approx 6 months of trading days

  const data = useMemo(() => {
    if (!latestBacktest || !latestBacktest.equity_curve || latestBacktest.equity_curve.length < windowSize) {
      return [];
    }

    const eq = latestBacktest.equity_curve;
    const rollingData = [];

    for (let i = windowSize; i < eq.length; i++) {
      const window = eq.slice(i - windowSize, i + 1);
      
      // Calculate daily returns for the window
      const returns = [];
      for (let j = 1; j < window.length; j++) {
        returns.push((window[j].value - window[j-1].value) / window[j-1].value);
      }

      const meanReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
      const stdDev = Math.sqrt(returns.reduce((a, b) => a + Math.pow(b - meanReturn, 2), 0) / (returns.length - 1));
      
      const annualizedReturn = meanReturn * 252;
      const annualizedVol = stdDev * Math.sqrt(252);
      
      const sharpe = annualizedVol > 0 ? (annualizedReturn - 0.05) / annualizedVol : 0; // Assuming 5% risk free

      // Max DD in window
      let peak = window[0].value;
      let maxDd = 0;
      for (let j = 0; j < window.length; j++) {
        if (window[j].value > peak) peak = window[j].value;
        const dd = (peak - window[j].value) / peak;
        if (dd > maxDd) maxDd = dd;
      }

      rollingData.push({
        date: eq[i].date,
        sharpe: sharpe,
        volatility: annualizedVol * 100,
        drawdown: maxDd * 100
      });
    }

    return rollingData;
  }, [latestBacktest]);

  if (data.length === 0) {
    return <div className="text-slate-500 text-xs p-4 text-center">Need at least 6 months of data for rolling metrics.</div>;
  }

  const colorMap = {
    sharpe: '#3b82f6',
    drawdown: '#ef4444',
    volatility: '#3b82f6'
  };

  return (
    <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full h-[300px] flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xs font-black text-slate-200 uppercase tracking-widest">6-Month Rolling Metrics</h3>
        <select 
          value={metric} 
          onChange={(e) => setMetric(e.target.value as any)}
          className="bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded p-1 outline-none font-bold uppercase tracking-widest"
        >
          <option value="sharpe">Sharpe Ratio</option>
          <option value="drawdown">Max Drawdown (%)</option>
          <option value="volatility">Volatility (%)</option>
        </select>
      </div>
      
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} strokeOpacity={0.4} />
            <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} minTickGap={30} />
            <YAxis tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ backgroundColor: '#131c31', border: '1px solid #1e293b', borderRadius: 4, color: '#f8fafc', fontSize: 11 }}
              labelStyle={{ fontWeight: 'black', color: '#94a3b8', marginBottom: 4 }}
              itemStyle={{ fontWeight: 'black', color: colorMap[metric] }}
            />
            <Line type="monotone" dataKey={metric} stroke={colorMap[metric]} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
