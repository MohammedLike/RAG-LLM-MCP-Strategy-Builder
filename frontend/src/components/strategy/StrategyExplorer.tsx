import { useEffect, useState } from 'react';
import { Zap, Trophy, Users, TrendingUp, Loader2 } from 'lucide-react';
import { fetchStrategies } from '../../services/api';

export const StrategyExplorer = () => {
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        // Fetch only indicator based strategies as requested
        const data = await fetchStrategies();
        // Filter locally if backend parameter not used, or just use all since backend returns DB strategies
        const filtered = data.filter((s: any) => s.category === 'Indicator Based');
        setStrategies(filtered);
      } catch (err) {
        console.error('Error loading strategies', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const featured = [
    { title: 'Highest Win Rate', icon: <Trophy size={20} />, color: 'from-blue-500 to-blue-600', stat: '82%', label: 'Supertrend Rider' },
    { title: 'Most Deployed', icon: <Users size={20} />, color: 'from-violet-500 to-purple-600', stat: '10,240', label: 'users' },
    { title: 'Most Profitable', icon: <TrendingUp size={20} />, color: 'from-emerald-500 to-green-600', stat: '₹5.4L', label: 'avg. annual' },
  ];

  return (
    <div className="p-6 space-y-8 overflow-y-auto h-full">
      <div className="flex items-center gap-2">
        <span className="text-lg">👍</span>
        <h2 className="text-xl font-bold text-slate-900">Indicator Based Strategies</h2>
        <div className="ml-auto flex gap-2 text-xs">
          <span className="bg-brand/10 text-brand px-3 py-1.5 rounded-lg font-bold border border-brand/20">
            {strategies.length} Strategies Found
          </span>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="animate-spin text-brand mb-4" size={32} />
          <p className="text-slate-500 font-bold uppercase tracking-widest text-xs">Syncing Strategy Library...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {strategies.map((s) => (
            <div key={s.slug} className="card p-5 flex flex-col hover:shadow-md transition-shadow bg-white border-[#e5e9f0]">
              <div className="flex justify-between mb-2">
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">{s.name}</h3>
                  <div className="flex items-center gap-1 text-[10px] text-muted mt-0.5">
                    Quant AI <span className="text-brand">✓</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[9px] text-muted uppercase font-bold">Category</div>
                  <div className="text-[10px] font-black text-brand uppercase">{s.category}</div>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {s.tags?.map((t: string) => (
                  <span key={t} className="tag bg-slate-50 text-slate-500 border border-slate-100">{t}</span>
                ))}
              </div>
              <p className="text-xs text-muted mb-4 flex-1 line-clamp-3">{s.hypothesis || s.description}</p>
              <div className="grid grid-cols-2 gap-2 mb-4 text-center">
                <div className="bg-slate-50 rounded-lg py-2">
                  <div className="text-[9px] text-muted uppercase font-bold">Total Return</div>
                  <div className="text-xs font-black text-emerald-600">{s.backtest_results?.total_return?.toFixed(2)}%</div>
                </div>
                <div className="bg-slate-50 rounded-lg py-2">
                  <div className="text-[9px] text-muted uppercase font-bold">Win Rate</div>
                  <div className="text-xs font-black text-slate-900">{s.backtest_results?.win_rate}%</div>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="btn-primary flex-1 py-2 text-[10px] flex items-center justify-center gap-1 font-black uppercase tracking-wider">
                  <Zap size={12} /> Instant Deploy
                </button>
                <button className="btn-outline flex-1 py-2 text-[10px] font-black uppercase tracking-wider">Details</button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div>
        <h2 className="text-xl font-bold text-slate-900 mb-4">Featured Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {featured.map((f) => (
            <div key={f.title} className="card overflow-hidden">
              <div className={`bg-gradient-to-r ${f.color} px-4 py-3 flex items-center gap-2 text-white`}>
                {f.icon}
                <span className="font-bold text-sm">{f.title}</span>
              </div>
              <div className="p-5 text-center">
                <div className="text-3xl font-bold text-slate-900">{f.stat}</div>
                <div className="text-sm text-muted mt-1 font-medium">{f.label}</div>
                <div className="flex gap-2 mt-4">
                  <button className="btn-primary flex-1 py-2 text-xs font-bold">Instant Deploy</button>
                  <button className="btn-outline flex-1 py-2 text-xs font-bold">Details</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
