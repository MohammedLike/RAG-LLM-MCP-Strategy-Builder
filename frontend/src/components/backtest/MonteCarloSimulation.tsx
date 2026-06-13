import React, { useMemo } from 'react';
import { useBacktestStore } from '../../stores/backtestStore';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export const MonteCarloSimulation = () => {
  const { latestBacktest } = useBacktestStore();

  const simulationData = useMemo(() => {
    if (!latestBacktest || !latestBacktest.trades || latestBacktest.trades.length < 10) return null;

    const trades = latestBacktest.trades.map(t => t.pnl_pct / 100);
    const numSimulations = 100; // reduced for browser performance
    const numTrades = trades.length;
    
    // Generate simulated paths
    const paths = Array.from({ length: numSimulations }, () => {
      let equity = 100;
      const path = [equity];
      for (let i = 0; i < numTrades; i++) {
        // Random sample with replacement
        const randomTrade = trades[Math.floor(Math.random() * trades.length)];
        equity = equity * (1 + randomTrade);
        path.push(equity);
      }
      return path;
    });

    // Calculate percentiles
    const resultData = [];
    let medianEnd = 0, p5End = 0, p95End = 0;

    for (let step = 0; step <= numTrades; step++) {
      const stepValues = paths.map(p => p[step]).sort((a, b) => a - b);
      
      const p5 = stepValues[Math.floor(numSimulations * 0.05)];
      const median = stepValues[Math.floor(numSimulations * 0.50)];
      const p95 = stepValues[Math.floor(numSimulations * 0.95)];

      if (step === numTrades) {
        medianEnd = median;
        p5End = p5;
        p95End = p95;
      }

      resultData.push({
        step,
        median: median.toFixed(2),
        p5: p5.toFixed(2),
        p95: p95.toFixed(2)
      });
    }

    const probProfit = paths.filter(p => p[numTrades] > 100).length / numSimulations * 100;

    return { data: resultData, probProfit, medianEnd, p5End, p95End };
  }, [latestBacktest]);

  if (!simulationData) {
    return <div className="text-slate-500 text-xs p-4 text-center">Need at least 10 trades for Monte Carlo Simulation.</div>;
  }

  return (
    <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-5 shadow-xl w-full h-[300px] flex flex-col">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-xs font-black text-slate-200 uppercase tracking-widest">Monte Carlo Simulation</h3>
        <div className="text-right">
          <div className="text-[10px] text-slate-500 font-bold uppercase">Prob. of Profit</div>
          <div className="text-sm font-black text-[#3b82f6]">{simulationData.probProfit.toFixed(1)}%</div>
        </div>
      </div>
      <div className="flex gap-4 mb-4 border-b border-slate-800 pb-2">
         <span className="text-[10px] text-slate-400 font-bold">5th %ile: <span className="text-red-400">{simulationData.p5End.toFixed(2)}</span></span>
         <span className="text-[10px] text-slate-400 font-bold">Median: <span className="text-[#3b82f6]">{simulationData.medianEnd.toFixed(2)}</span></span>
         <span className="text-[10px] text-slate-400 font-bold">95th %ile: <span className="text-blue-400">{simulationData.p95End.toFixed(2)}</span></span>
      </div>

      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={simulationData.data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} strokeOpacity={0.4} />
            <XAxis dataKey="step" tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 9, fill: '#64748b' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ backgroundColor: '#131c31', border: '1px solid #1e293b', borderRadius: 4, color: '#f8fafc', fontSize: 11 }}
              labelStyle={{ fontWeight: 'black', color: '#94a3b8', marginBottom: 4 }}
            />
            <Line type="monotone" dataKey="p95" stroke="#3b82f6" strokeWidth={1} dot={false} strokeDasharray="3 3" name="95th Percentile" />
            <Line type="monotone" dataKey="median" stroke="#3b82f6" strokeWidth={2} dot={false} name="Median Path" />
            <Line type="monotone" dataKey="p5" stroke="#ef4444" strokeWidth={1} dot={false} strokeDasharray="3 3" name="5th Percentile" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
