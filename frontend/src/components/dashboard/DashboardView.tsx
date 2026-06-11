import { useEffect } from 'react';
import { TrendingDown, TrendingUp, Zap, Rocket } from 'lucide-react';
import { useMarketStore } from '../../stores/marketStore';
import { fetchQuote } from '../../services/api';

const extraIndices = [
  { name: 'NIFTY MIDCAP SELECT', value: '13,201.05', change: '-0.40%', up: false },
  { name: 'FIN NIFTY', value: '27,201.05', change: '-0.40%', up: false },
  { name: 'INDIA VIX', value: '17.05', change: '-0.40%', up: false },
];

const recommendedStrategies = [
  {
    name: 'Nifty Options Bundle',
    provider: 'Stockwiz Tech. LLP',
    minInvestment: '₹3,00,000',
    tags: [{ label: 'Multi Directional', color: 'bg-orange-100 text-orange-700' }],
    risk: 'High Risk',
    instruments: 'Nifty',
    description: 'A diversified options bundle for Nifty with defined risk parameters.',
    winRate: '68%',
    rr: '1:2',
    return1y: '15.2%',
    maxDd: '8.5%',
  },
  {
    name: 'Short Strangle Pro',
    provider: 'Quant AI',
    minInvestment: '₹2,50,000',
    tags: [{ label: 'Non-Directional', color: 'bg-blue-100 text-blue-700' }],
    risk: 'Medium Risk',
    instruments: 'BankNifty',
    description: 'Weekly short strangle on BankNifty with IV filter and theta capture.',
    winRate: '72%',
    rr: '1:1.5',
    return1y: '12.5%',
    maxDd: '6.2%',
  },
];

interface DashboardViewProps {
  onNavigate?: (view: 'strategies' | 'backtest') => void;
}

export const DashboardView = ({ onNavigate }: DashboardViewProps) => {
  const { niftyQuote, bankNiftyQuote, setQuote } = useMarketStore();

  useEffect(() => {
    fetchQuote('NIFTY').then(setQuote).catch(() => {});
    fetchQuote('BANKNIFTY').then(setQuote).catch(() => {});
  }, [setQuote]);

  const formatPrice = (v?: number) => (v ? v.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : '—');

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900">
          👋 Good Afternoon, <span className="text-brand">Mohammed Like</span>
        </h2>
        <span className="tag bg-green-100 text-success text-xs px-3 py-1">Market Open</span>
      </div>

      {/* Market indices bar */}
      <div className="flex gap-3 overflow-x-auto pb-1">
        {[
          { name: 'NIFTY 50', value: formatPrice(niftyQuote?.ltp), change: niftyQuote?.change ?? -0.4, up: (niftyQuote?.change ?? -0.4) >= 0 },
          { name: 'BANK NIFTY', value: formatPrice(bankNiftyQuote?.ltp), change: bankNiftyQuote?.change ?? -0.4, up: (bankNiftyQuote?.change ?? -0.4) >= 0 },
          ...extraIndices.map((i) => ({ ...i, change: parseFloat(i.change), up: i.up })),
        ].map((idx) => (
          <div key={idx.name} className="card px-4 py-3 min-w-[160px] shrink-0">
            <div className="text-[10px] font-semibold text-muted uppercase tracking-wide mb-1">{idx.name}</div>
            <div className="text-lg font-bold text-slate-900">{idx.value}</div>
            <div className={`flex items-center gap-1 text-xs font-semibold mt-0.5 ${idx.up ? 'text-success' : 'text-danger'}`}>
              {idx.up ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {typeof idx.change === 'number' ? `${idx.change >= 0 ? '+' : ''}${idx.change.toFixed(2)}%` : idx.change}
            </div>
          </div>
        ))}
        <div className="card px-4 py-3 min-w-[140px] shrink-0 flex flex-col justify-center items-center">
          <div className="text-[10px] font-semibold text-muted uppercase mb-1">Market Sentiment</div>
          <div className="text-sm font-bold text-danger">Bearish</div>
          <div className="text-2xl mt-1">🐻</div>
        </div>
      </div>

      {/* Middle row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-semibold text-muted">Overall Profit/Loss</span>
              <div className="flex rounded-lg border border-[#e5e9f0] p-0.5 text-xs">
                <button className="px-3 py-1 rounded-md bg-brand text-white font-semibold">Live</button>
                <button className="px-3 py-1 rounded-md text-muted font-medium">Virtual</button>
              </div>
            </div>
            <div className="text-4xl font-bold text-slate-900 mb-1">₹ 0</div>
            <div className="text-xs text-muted mb-6">Last Updated 11 Jun 2026, 02:30 PM</div>
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-[#e5e9f0]">
              {[
                { label: 'Booked P&L', value: '₹0' },
                { label: 'Capital Deployed', value: '₹0' },
                { label: 'Active Algos', value: '0' },
              ].map((s) => (
                <div key={s.label}>
                  <div className="text-[10px] text-muted uppercase font-semibold">{s.label}</div>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">{s.value}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-8 flex flex-col items-center text-center">
            <div className="w-12 h-12 rounded-xl bg-brand-light flex items-center justify-center mb-3">
              <Zap size={24} className="text-brand" />
            </div>
            <h3 className="font-bold text-slate-900 mb-1">No Deployed Strategies</h3>
            <p className="text-sm text-muted mb-4">Deploy your first algo strategy to get started</p>
            <button onClick={() => onNavigate?.('strategies')} className="btn-primary px-5 py-2.5 text-sm">Deploy Algo Strategy</button>
          </div>
        </div>

        <div className="card p-5 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-slate-900">Deployed Algos</h3>
            <div className="flex gap-2 text-xs">
              <button className="px-2 py-1 rounded-md bg-brand-light text-brand font-semibold">All</button>
              <button className="px-2 py-1 rounded-md text-muted">Strategy Type</button>
            </div>
          </div>
          <div className="flex-1 flex flex-col items-center justify-center text-center py-8">
            <div className="w-12 h-12 rounded-xl bg-brand-light flex items-center justify-center mb-3">
              <Zap size={24} className="text-brand" />
            </div>
            <h3 className="font-bold text-slate-900 mb-1">No Deployed Algos !</h3>
            <p className="text-sm text-muted mb-4">Browse pre-built strategies to deploy</p>
            <button onClick={() => onNavigate?.('strategies')} className="btn-primary px-5 py-2.5 text-sm">Browse Pre-Built Algos</button>
          </div>
        </div>
      </div>

      {/* Recommended + Algos of the week */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        <div className="xl:col-span-3">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">👍</span>
            <h3 className="font-bold text-slate-900">Recommended Algo Strategies</h3>
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
          <div className="flex gap-4 overflow-x-auto pb-2">
            {recommendedStrategies.map((s) => (
              <StrategyCard key={s.name} {...s} />
            ))}
          </div>
        </div>

        <div className="card overflow-hidden">
          <div className="bg-gradient-to-r from-brand to-blue-400 px-4 py-3 flex items-center gap-2 text-white">
            <Rocket size={18} />
            <span className="font-bold text-sm">Algos of the Week</span>
          </div>
          <div className="p-4">
            <h4 className="font-bold text-slate-900 text-sm mb-3">Nifty Monthly B1</h4>
            <div className="space-y-2 text-sm">
              {[
                ['Overall P&L', '₹1,25,000'],
                ['Win Rate', '72%'],
                ['Monthly Return', '4.2%'],
                ['Avg. Trade Duration', '5 days'],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-muted">{k}</span>
                  <span className="font-semibold text-slate-900">{v}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-center gap-1.5 mt-4">
              {[0, 1, 2, 3, 4].map((i) => (
                <span key={i} className={`w-1.5 h-1.5 rounded-full ${i === 0 ? 'bg-brand' : 'bg-slate-300'}`} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

function StrategyCard({
  name,
  provider,
  minInvestment,
  tags,
  risk,
  instruments,
  description,
  winRate,
  rr,
  return1y,
  maxDd,
}: (typeof recommendedStrategies)[0]) {
  return (
    <div className="card p-4 min-w-[300px] max-w-[320px] shrink-0 flex flex-col">
      <div className="flex items-start justify-between mb-2">
        <div>
          <h4 className="font-bold text-slate-900 text-sm">{name}</h4>
          <div className="flex items-center gap-1 mt-0.5">
            <span className="text-xs text-muted">{provider}</span>
            <span className="text-brand text-xs">✓</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-muted">Min Investment</div>
          <div className="text-xs font-bold text-slate-900">{minInvestment}</div>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5 mb-3">
        {tags.map((t) => (
          <span key={t.label} className={`tag ${t.color}`}>{t.label}</span>
        ))}
        <span className="tag bg-red-100 text-danger">{risk}</span>
      </div>
      <div className="text-[10px] text-muted uppercase font-semibold mb-1">Instruments</div>
      <div className="text-xs font-semibold text-slate-800 mb-2">{instruments}</div>
      <p className="text-xs text-muted mb-3 line-clamp-2">{description}</p>
      <div className="grid grid-cols-2 gap-2 mb-4 text-center">
        {[
          ['Win Rate', winRate],
          ['R/R Ratio', rr],
          ['1 Year Return', return1y],
          ['Max Drawdown', maxDd],
        ].map(([k, v]) => (
          <div key={k} className="bg-slate-50 rounded-lg py-2">
            <div className="text-[10px] text-muted">{k}</div>
            <div className="text-xs font-bold text-slate-900">{v}</div>
          </div>
        ))}
      </div>
      <div className="flex gap-2 mt-auto">
        <button className="btn-primary flex-1 py-2 text-xs flex items-center justify-center gap-1">
          <Zap size={12} /> Instant Deploy
        </button>
        <button className="btn-outline flex-1 py-2 text-xs">View Details</button>
      </div>
    </div>
  );
}
