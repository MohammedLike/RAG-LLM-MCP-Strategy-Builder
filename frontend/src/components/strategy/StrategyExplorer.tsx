export const StrategyExplorer = () => {
  const strategies = [
    { name: 'Short Strangle', category: 'Options Selling', performance: '+15.2%' },
    { name: 'Iron Condor', category: 'Non-Directional', performance: '+12.5%' }
  ];

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Strategy Knowledge Base</h2>
      <div className="grid grid-cols-2 gap-4">
        {strategies.map((s, i) => (
          <div key={i} className="bg-slate-800 p-4 rounded-xl border border-slate-700 hover:border-accent-blue cursor-pointer transition">
            <h3 className="text-lg font-semibold text-white">{s.name}</h3>
            <span className="inline-block px-2 py-1 mt-2 text-xs rounded bg-slate-700 text-slate-300">{s.category}</span>
            <div className="mt-4 text-accent-green font-bold">{s.performance} APY</div>
          </div>
        ))}
      </div>
    </div>
  );
};
