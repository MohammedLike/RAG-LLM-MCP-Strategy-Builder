import { useEffect, useState } from 'react';
import { TrendingDown, TrendingUp, Zap, Rocket } from 'lucide-react';
import { useMarketStore } from '../../stores/marketStore';
import { fetchQuote, fetchStrategies } from '../../services/api';
import './Dashboard.css';

const extraIndices = [
  { name: 'NIFTY MIDCAP SELECT', value: '13,201.05', change: '-0.40%', up: false },
  { name: 'FIN NIFTY', value: '27,201.05', change: '-0.40%', up: false },
  { name: 'INDIA VIX', value: '17.05', change: '-0.40%', up: false },
];

interface DashboardViewProps {
  onNavigate?: (view: 'strategies' | 'backtest') => void;
  onRunStrategy?: (spec: any) => void;
}

export const DashboardView = ({ onNavigate, onRunStrategy }: DashboardViewProps) => {
  const { niftyQuote, bankNiftyQuote, setQuote } = useMarketStore();
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loadingStrategies, setLoadingStrategies] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [categories, setCategories] = useState<string[]>(['All']);

  useEffect(() => {
    fetchQuote('NIFTY').then(setQuote).catch(() => {});
    fetchQuote('BANKNIFTY').then(setQuote).catch(() => {});
  }, [setQuote]);

  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const data = await fetchStrategies();
        const rows = data || [];
        // Prefer categories with fully-defined entry/exit rules on the dashboard
        const filtered = rows.filter((s: any) => 
          s.category === 'Equity' || 
          s.category === 'Options' || 
          s.category === 'Trend Following' ||
          s.category === 'Momentum' ||
          s.category === 'Mean Reversion'
        );
        setStrategies(filtered);
        setCategories(['All', 'Equity', 'Options', 'Trend Following', 'Momentum', 'Mean Reversion']);
      } catch (err) {
        console.error('Error loading dashboard strategies', err);
      } finally {
        setLoadingStrategies(false);
      }
    };
    loadStrategies();
  }, []);

  const formatPrice = (v?: number) => (v ? v.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : '—');

  return (
    <div className="dashboard-shell p-6 space-y-6 overflow-y-auto h-full">
      <div className="flex items-center justify-between dashboard-hero px-6 py-4">
        <h2 className="text-2xl font-bold text-white">
          👋 Good Afternoon, <span className="text-brand-light">Mohammed Like</span>
        </h2>
        <span className="dashboard-badge text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded">Market Open</span>
      </div>

      {/* Market indices bar */}
      <div className="flex gap-3 overflow-x-auto pb-1">
        {[
          { name: 'NIFTY 50', value: formatPrice(niftyQuote?.ltp), change: niftyQuote?.change ?? -0.4, up: (niftyQuote?.change ?? -0.4) >= 0 },
          { name: 'BANK NIFTY', value: formatPrice(bankNiftyQuote?.ltp), change: bankNiftyQuote?.change ?? -0.4, up: (bankNiftyQuote?.change ?? -0.4) >= 0 },
          ...extraIndices.map((i) => ({ ...i, change: parseFloat(i.change), up: i.up })),
        ].map((idx) => (
          <div key={idx.name} className="bg-[#131c31] border border-slate-800/60 p-4 min-w-[160px] shrink-0 rounded-xl">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wide mb-1">{idx.name}</div>
            <div className="text-lg font-black text-white">{idx.value}</div>
            <div className={`flex items-center gap-1 text-xs font-bold mt-0.5 ${idx.up ? 'text-emerald-400' : 'text-rose-400'}`}>
              {idx.up ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {typeof idx.change === 'number' ? `${idx.change >= 0 ? '+' : ''}${idx.change.toFixed(2)}%` : idx.change}
            </div>
          </div>
        ))}
        <div className="bg-[#131c31] border border-slate-800/60 p-4 min-w-[140px] shrink-0 flex flex-col justify-center items-center rounded-xl">
          <div className="text-[10px] font-bold text-slate-500 uppercase mb-1">Market Sentiment</div>
          <div className="text-sm font-black text-rose-400">Bearish</div>
          <div className="text-2xl mt-1">🐻</div>
        </div>
      </div>

      {/* Middle row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-[#131c31] border border-slate-800/60 p-5 rounded-xl">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-bold text-slate-400">Overall Profit/Loss</span>
              <div className="flex bg-slate-900 rounded-lg p-0.5 border border-slate-800 text-[10px]">
                <button className="px-3 py-1 rounded-md bg-brand text-[#0c1222] font-black uppercase">Live</button>
                <button className="px-3 py-1 rounded-md text-slate-500 font-bold uppercase">Virtual</button>
              </div>
            </div>
            <div className="text-4xl font-black text-white mb-1">₹ 0</div>
            <div className="text-[10px] text-slate-500 mb-6 font-mono">Last Updated 11 Jun 2026, 02:30 PM</div>
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-800/40">
              {[
                { label: 'Booked P&L', value: '₹0' },
                { label: 'Capital Deployed', value: '₹0' },
                { label: 'Active Algos', value: '0' },
              ].map((s) => (
                <div key={s.label}>
                  <div className="text-[9px] text-slate-500 uppercase font-black tracking-widest">{s.label}</div>
                  <div className="text-lg font-black text-white mt-0.5">{s.value}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-[#131c31] border border-slate-800/60 p-8 flex flex-col items-center text-center rounded-xl">
            <div className="w-12 h-12 rounded-xl bg-brand/10 flex items-center justify-center mb-3 border border-brand/20">
              <Zap size={24} className="text-brand" />
            </div>
            <h3 className="font-black text-white mb-1 uppercase tracking-tight">No Deployed Strategies</h3>
            <p className="text-xs text-slate-500 mb-4">Deploy your first algo strategy to get started</p>
            <button onClick={() => onNavigate?.('strategies')} className="bg-brand hover:bg-brand-dark text-[#0c1222] px-6 py-2.5 rounded-lg text-xs font-black uppercase tracking-wider transition cursor-pointer">Deploy Algo Strategy</button>
          </div>
        </div>

        <div className="bg-[#131c31] border border-slate-800/60 p-5 flex flex-col rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-black text-white uppercase tracking-tight text-sm">Deployed Algos</h3>
            <div className="flex gap-2 text-[10px]">
              <button className="px-2 py-1 rounded-md bg-brand/10 text-brand font-black uppercase">All</button>
              <button className="px-2 py-1 rounded-md text-slate-500 font-bold uppercase">Type</button>
            </div>
          </div>
          <div className="flex-1 flex flex-col items-center justify-center text-center py-8">
            <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-3">
              <Zap size={24} className="text-slate-700" />
            </div>
            <h3 className="font-black text-slate-400 mb-1 uppercase text-xs tracking-widest">No Active Algos</h3>
            <p className="text-[10px] text-slate-600 mb-4">Browse strategies to deploy</p>
            <button onClick={() => onNavigate?.('strategies')} className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-wider transition cursor-pointer">Browse Algos</button>
          </div>
        </div>
      </div>

      {/* Recommended + Algos of the week */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        <div className="xl:col-span-3">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-lg">👍</span>
            <h3 className="font-black text-white uppercase tracking-tight text-sm">Recommended Strategies</h3>
          </div>
          <div className="flex gap-2 mb-4 overflow-x-auto">
            {categories.map((tab) => (
              <button
                key={tab}
                onClick={() => setSelectedCategory(tab)}
                className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition shrink-0 ${
                  selectedCategory === tab ? 'bg-brand text-[#0c1222]' : 'bg-slate-900 text-slate-500 hover:text-slate-300 border border-slate-800'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {loadingStrategies ? (
              <div className="col-span-3 py-12 text-center text-slate-500 text-[10px] font-black uppercase tracking-widest">Syncing Strategies...</div>
            ) : (
              strategies
                .filter((s) => selectedCategory === 'All' || s.category === selectedCategory)
                .slice(0, 30)
                .map((s) => (
                  <div key={s.slug} className="bg-[#131c31] border border-slate-800/60 p-5 rounded-xl flex flex-col">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[8px] uppercase font-black tracking-widest text-slate-600">{s.category || 'General'}</span>
                      <span className="text-[10px] font-black text-brand">{s.backtest_results?.win_rate ? `${s.backtest_results.win_rate}% WR` : ''}</span>
                    </div>
                    <h4 className="font-black text-white text-xs mb-2 uppercase tracking-tight">{s.name}</h4>
                    <p className="text-[10px] text-slate-500 leading-relaxed mb-4 min-h-[45px] line-clamp-3">{s.description || s.hypothesis || 'Quantitative strategy from the library.'}</p>
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {(s.tags || []).slice(0, 2).map((tag: string) => (
                        <span key={tag} className="rounded px-2 py-0.5 text-[8px] font-black uppercase bg-slate-900 text-slate-500 border border-slate-800">{tag}</span>
                      ))}
                    </div>
                    <div className="flex items-center gap-2 mt-auto">
                      <button
                        onClick={() => onRunStrategy?.({ ...s.backtest_spec, symbol: s.backtest_spec?.symbol || 'NIFTY' })}
                        className="bg-brand hover:bg-brand-dark text-[#0c1222] flex-1 py-2 text-[10px] font-black uppercase tracking-widest rounded transition cursor-pointer"
                      >
                        Run
                      </button>
                      <button className="bg-slate-800 hover:bg-slate-700 text-white flex-1 py-2 text-[10px] font-black uppercase tracking-widest rounded transition cursor-pointer">Details</button>
                    </div>
                  </div>
                ))
            )}
          </div>
        </div>

        <div className="bg-[#131c31] border border-slate-800/60 rounded-xl overflow-hidden flex flex-col">
          <div className="bg-gradient-to-r from-brand to-brand-light px-4 py-3 flex items-center gap-2 text-[#0c1222]">
            <Rocket size={16} />
            <span className="font-black text-xs uppercase tracking-tight">Algos of the Week</span>
          </div>
          <div className="p-4 flex-1 flex flex-col">
            <h4 className="font-black text-white text-xs mb-3 uppercase tracking-tight">Nifty Monthly B1</h4>
            <div className="space-y-3 text-[10px]">
              {[
                ['Overall P&L', '₹1,25,000'],
                ['Win Rate', '72%'],
                ['Monthly Return', '4.2%'],
                ['Avg. Duration', '5 days'],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between items-center">
                  <span className="text-slate-500 font-bold uppercase">{k}</span>
                  <span className="font-black text-slate-200">{v}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-center gap-1.5 mt-auto pt-4">
              {[0, 1, 2].map((i) => (
                <span key={i} className={`w-1 h-1 rounded-full ${i === 0 ? 'bg-brand' : 'bg-slate-800'}`} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

