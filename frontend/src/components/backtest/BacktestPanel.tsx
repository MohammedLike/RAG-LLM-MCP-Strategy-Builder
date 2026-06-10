import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const mockData = Array.from({length: 30}, (_, i) => ({
  date: `Day ${i+1}`,
  equity: 100000 + Math.random() * 20000 + i * 500
}));

export const BacktestPanel = () => {
  return (
    <div className="p-6 flex flex-col h-full gap-6">
      <div className="grid grid-cols-4 gap-4">
        {['Sharpe', 'Sortino', 'Max DD', 'Win Rate'].map((metric, i) => (
          <div key={i} className="bg-slate-800 p-4 rounded-xl border border-slate-700 text-center">
            <div className="text-slate-400 text-sm mb-1">{metric}</div>
            <div className="text-xl font-bold">---</div>
          </div>
        ))}
      </div>
      <div className="flex-1 bg-slate-800 rounded-xl p-4 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4 text-slate-300">Equity Curve</h3>
        <ResponsiveContainer width="100%" height="90%">
          <AreaChart data={mockData}>
            <XAxis dataKey="date" hide />
            <YAxis domain={['auto', 'auto']} hide />
            <Tooltip />
            <Area type="monotone" dataKey="equity" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
