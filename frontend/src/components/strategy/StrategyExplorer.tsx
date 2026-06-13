import { useEffect, useState } from 'react';
import { Zap, Trophy, Users, TrendingUp, Loader2 } from 'lucide-react';
import { fetchStrategies } from '../../services/api';

export const StrategyExplorer = ({ onRunStrategy }: { onRunStrategy?: (spec: any) => void }) => {
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [categories, setCategories] = useState<string[]>(['All']);
  const [selectedCategory, setSelectedCategory] = useState('All');

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchStrategies();
        setStrategies(data);
        const dynamicCategories = Array.from(
          new Set(['All', ...data.map((s: any) => s.category || 'Uncategorized')])
        );
        setCategories(dynamicCategories);
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
    <div className="p-6 space-y-8 overflow-y-auto h-full bg-[#0c1222]">
      <div className="flex items-center gap-2">
        <span className="text-lg">👍</span>
        <h2 className="text-xl font-black text-white uppercase tracking-tight">Strategy Library</h2>
        <div className="ml-auto flex gap-2 text-[10px]">
          <span className="bg-brand/10 text-brand px-3 py-1.5 rounded font-black border border-brand/20 uppercase tracking-widest">
            {strategies.length} Strategies Found
          </span>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 mt-3 overflow-x-auto">
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-1.5 rounded text-[10px] font-black uppercase tracking-widest transition shrink-0 ${
              selectedCategory === category
                ? 'bg-brand text-[#0c1222]'
                : 'bg-slate-900 text-slate-500 hover:text-slate-300 border border-slate-800'
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="animate-spin text-brand mb-4" size={32} />
          <p className="text-slate-500 font-black uppercase tracking-widest text-[10px]">Syncing Strategy Library...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {strategies
            .filter((s) => selectedCategory === 'All' || (s.category || 'Uncategorized') === selectedCategory)
            .map((s) => (
              <div key={s.slug} className="bg-[#131c31] border border-slate-800/60 p-5 flex flex-col hover:border-slate-700 transition-colors rounded-xl">
              <div className="flex justify-between mb-3">
                <div>
                  <h3 className="font-black text-white text-xs uppercase tracking-tight">{s.name}</h3>
                  <div className="flex items-center gap-1 text-[8px] text-slate-600 mt-0.5 font-black uppercase tracking-widest">
                    Quant AI <span className="text-brand">✓</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[8px] text-slate-600 uppercase font-black tracking-widest">Category</div>
                  <div className="text-[10px] font-black text-brand uppercase">{s.category}</div>
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {s.tags?.map((t: string) => (
                  <span key={t} className="px-2 py-0.5 rounded text-[8px] font-black uppercase bg-slate-900 text-slate-500 border border-slate-800">{t}</span>
                ))}
              </div>
              <p className="text-[10px] text-slate-500 mb-4 flex-1 line-clamp-3 leading-relaxed">{s.hypothesis || s.description}</p>
              <div className="grid grid-cols-2 gap-2 mb-4 text-center">
                <div className="bg-slate-900/50 rounded py-2 border border-slate-800/40">
                  <div className="text-[8px] text-slate-600 uppercase font-black tracking-widest">Total Return</div>
                  <div className="text-xs font-black text-emerald-400">{s.backtest_results?.total_return?.toFixed(2)}%</div>
                </div>
                <div className="bg-slate-900/50 rounded py-2 border border-slate-800/40">
                  <div className="text-[8px] text-slate-600 uppercase font-black tracking-widest">Win Rate</div>
                  <div className="text-xs font-black text-white">{s.backtest_results?.win_rate}%</div>
                </div>
              </div>
              <div className="flex gap-2">
                <button 
                  onClick={() => onRunStrategy?.(s.backtest_spec)}
                  className="bg-brand hover:bg-brand-dark text-[#0c1222] flex-1 py-2 text-[10px] flex items-center justify-center gap-1 font-black uppercase tracking-widest rounded transition cursor-pointer"
                >
                  <Zap size={12} /> Instant Deploy
                </button>
                <button className="bg-slate-800 hover:bg-slate-700 text-white flex-1 py-2 text-[10px] font-black uppercase tracking-widest rounded transition cursor-pointer">Details</button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div>
        <h2 className="text-xl font-black text-white uppercase tracking-tight mb-4">Featured Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {featured.map((f) => (
            <div key={f.title} className="bg-[#131c31] border border-slate-800/60 rounded-xl overflow-hidden flex flex-col">
              <div className={`bg-gradient-to-r ${f.color} px-4 py-3 flex items-center gap-2 text-white`}>
                {f.icon}
                <span className="font-black text-xs uppercase tracking-tight">{f.title}</span>
              </div>
              <div className="p-5 text-center flex-1 flex flex-col">
                <div className="text-3xl font-black text-white">{f.stat}</div>
                <div className="text-[10px] text-slate-500 mt-1 font-black uppercase tracking-widest">{f.label}</div>
                <div className="flex gap-2 mt-auto pt-6">
                  <button className="bg-brand hover:bg-brand-dark text-[#0c1222] flex-1 py-2.5 text-[10px] font-black uppercase tracking-widest rounded transition cursor-pointer">Instant Deploy</button>
                  <button className="bg-slate-800 hover:bg-slate-700 text-white flex-1 py-2.5 text-[10px] font-black uppercase tracking-widest rounded transition cursor-pointer">Details</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
