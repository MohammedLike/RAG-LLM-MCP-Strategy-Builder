import { Zap, Trophy, Users, TrendingUp } from 'lucide-react';

const strategies = [
  {
    name: 'Nifty Options Bundle',
    provider: 'Stockwiz Tech. LLP',
    minInvestment: '₹3,00,000',
    tags: ['Multi Directional', 'High Risk'],
    instruments: 'Nifty',
    description: 'A diversified options bundle for Nifty with defined risk parameters and weekly rebalancing.',
    winRate: '68%',
    rr: '1:2',
    return1y: '15.2%',
    maxDd: '8.5%',
  },
  {
    name: 'Short Strangle',
    provider: 'Quant AI',
    minInvestment: '₹2,50,000',
    tags: ['Non-Directional', 'Medium Risk'],
    instruments: 'BankNifty',
    description: 'Weekly short strangle on BankNifty with IV percentile filter and theta decay capture.',
    winRate: '72%',
    rr: '1:1.5',
    return1y: '12.5%',
    maxDd: '6.2%',
  },
  {
    name: 'Iron Condor',
    provider: 'Quant AI',
    minInvestment: '₹2,00,000',
    tags: ['Defined Risk', 'Low Risk'],
    instruments: 'Nifty',
    description: 'Monthly iron condor on Nifty with wing protection and 50% profit target.',
    winRate: '75%',
    rr: '1:3',
    return1y: '11.8%',
    maxDd: '5.1%',
  },
  {
    name: 'Bull Put Spread',
    provider: 'Quant AI',
    minInvestment: '₹1,50,000',
    tags: ['Directional', 'Medium Risk'],
    instruments: 'Nifty, BankNifty',
    description: 'Credit spread on support levels with DMA confluence and RSI filter.',
    winRate: '64%',
    rr: '1:2',
    return1y: '10.2%',
    maxDd: '7.0%',
  },
];

const featured = [
  { title: 'Highest Win Rate', icon: <Trophy size={20} />, color: 'from-blue-500 to-blue-600', stat: '75%', label: 'Iron Condor' },
  { title: 'Most Deployed', icon: <Users size={20} />, color: 'from-violet-500 to-purple-600', stat: '1,240', label: 'users' },
  { title: 'Most Profitable', icon: <TrendingUp size={20} />, color: 'from-emerald-500 to-green-600', stat: '₹2.4L', label: 'avg. annual' },
];

export const StrategyExplorer = () => {
  return (
    <div className="p-6 space-y-8 overflow-y-auto h-full">
      <div className="flex items-center gap-2">
        <span className="text-lg">👍</span>
        <h2 className="text-xl font-bold text-slate-900">Recommended Algo Strategies</h2>
        <div className="ml-auto flex gap-2 text-xs">
          {['Individual', 'Bundled', 'Algofolio'].map((tab, i) => (
            <button
              key={tab}
              className={`px-3 py-1.5 rounded-lg font-semibold ${
                i === 1 ? 'bg-brand text-white' : 'bg-white border border-[#e5e9f0] text-muted'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {strategies.map((s) => (
          <div key={s.name} className="card p-5 flex flex-col hover:shadow-md transition-shadow">
            <div className="flex justify-between mb-2">
              <div>
                <h3 className="font-bold text-slate-900">{s.name}</h3>
                <div className="flex items-center gap-1 text-xs text-muted mt-0.5">
                  {s.provider} <span className="text-brand">✓</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-muted">Min Investment</div>
                <div className="text-xs font-bold">{s.minInvestment}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {s.tags.map((t) => (
                <span key={t} className="tag bg-slate-100 text-slate-600">{t}</span>
              ))}
            </div>
            <div className="text-[10px] text-muted uppercase font-semibold">Instruments</div>
            <div className="text-xs font-semibold mb-2">{s.instruments}</div>
            <p className="text-xs text-muted mb-4 flex-1">{s.description}</p>
            <div className="grid grid-cols-2 gap-2 mb-4 text-center">
              {[['Win Rate', s.winRate], ['R/R Ratio', s.rr], ['1Y Return', s.return1y], ['Max DD', s.maxDd]].map(([k, v]) => (
                <div key={k} className="bg-slate-50 rounded-lg py-2">
                  <div className="text-[10px] text-muted">{k}</div>
                  <div className="text-xs font-bold text-slate-900">{v}</div>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <button className="btn-primary flex-1 py-2 text-xs flex items-center justify-center gap-1">
                <Zap size={12} /> Instant Deploy
              </button>
              <button className="btn-outline flex-1 py-2 text-xs">View Details</button>
            </div>
          </div>
        ))}
      </div>

      <div>
        <h2 className="text-xl font-bold text-slate-900 mb-4">Featured Algos</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {featured.map((f) => (
            <div key={f.title} className="card overflow-hidden">
              <div className={`bg-gradient-to-r ${f.color} px-4 py-3 flex items-center gap-2 text-white`}>
                {f.icon}
                <span className="font-bold text-sm">{f.title}</span>
              </div>
              <div className="p-5 text-center">
                <div className="text-3xl font-bold text-slate-900">{f.stat}</div>
                <div className="text-sm text-muted mt-1">{f.label}</div>
                <div className="flex gap-2 mt-4">
                  <button className="btn-primary flex-1 py-2 text-xs">Instant Deploy</button>
                  <button className="btn-outline flex-1 py-2 text-xs">Details</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
          <span>🎓</span> Learnings & Guides
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {['Token Validation', 'Strategy Builder', 'Algo Categories'].map((title) => (
            <div
              key={title}
              className="relative rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 p-6 text-white overflow-hidden cursor-pointer hover:scale-[1.02] transition-transform"
            >
              <div className="text-5xl font-black text-white/5 absolute -right-2 -bottom-2">X</div>
              <h3 className="font-bold text-lg relative z-10">{title}</h3>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
