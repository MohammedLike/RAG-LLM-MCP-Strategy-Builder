import type { ReactNode } from 'react';
import {
  LayoutDashboard,
  Briefcase,
  Layers,
  Bot,
  Wrench,
  User,
  Phone,
  HelpCircle,
  ChevronDown,
  Settings,
  Zap,
} from 'lucide-react';

export type AppView =
  | 'dashboard'
  | 'strategies'
  | 'my-algos'
  | 'backtest'
  | 'account'
  | 'contact'
  | 'faq';

interface SidebarProps {
  activeView: AppView;
  onNavigate: (view: AppView) => void;
  tradingMode: 'live' | 'virtual';
  onTradingModeChange: (mode: 'live' | 'virtual') => void;
}

const navItems: { id: AppView; label: string; icon: ReactNode; section?: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
  { id: 'strategies', label: 'Strategy Library', icon: <Layers size={18} />, section: 'algos' },
  { id: 'my-algos', label: 'My Algos', icon: <Bot size={18} />, section: 'algos' },
  { id: 'backtest', label: 'Strategy Builder', icon: <Wrench size={18} /> },
  { id: 'account', label: 'My Account', icon: <User size={18} /> },
  { id: 'contact', label: 'Contact Us', icon: <Phone size={18} /> },
  { id: 'faq', label: 'FAQ', icon: <HelpCircle size={18} /> },
];

export const Sidebar = ({ activeView, onNavigate, tradingMode, onTradingModeChange }: SidebarProps) => {
  return (
    <aside className="w-[220px] min-w-[220px] h-full bg-[#0a0e17] border-r border-slate-800/60 flex flex-col">
      <div className="px-5 py-5 border-b border-slate-800/60">
        <div className="flex items-center gap-1">
          <span className="text-xl font-bold text-white tracking-tight">Stryke</span>
          <span className="text-xl font-bold text-brand tracking-tight">X</span>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-brand text-[#06090f] shadow-sm'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-100'
              }`}
            >
              <span className="flex items-center gap-2.5">
                {item.icon}
                {item.label}
              </span>
              {item.section && !isActive && <ChevronDown size={14} className="opacity-50" />}
            </button>
          );
        })}
      </nav>

      <div className="p-3 space-y-3 border-t border-slate-800/60">
        <div className="rounded-xl bg-gradient-to-br from-[#00d09c]/20 to-[#00b386]/10 p-4 border border-brand/20">
          <div className="flex items-center gap-2 mb-3">
            <Zap size={16} className="text-brand" />
            <span className="text-sm font-semibold text-slate-100">Trading Mode</span>
          </div>
          <div className="flex rounded-lg bg-slate-900 p-0.5 border border-slate-800">
            {(['live', 'virtual'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => onTradingModeChange(mode)}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-md capitalize transition ${
                  tradingMode === mode ? 'bg-brand text-[#06090f]' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 px-3 py-2.5 rounded-xl flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand/10 flex items-center justify-center">
            <Zap size={14} className="text-brand" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-100">Unlimited</div>
            <div className="text-[10px] text-slate-500">Deployment & Backtests</div>
          </div>
        </div>

        <div className="flex items-center gap-2 px-2 py-1">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand to-blue-400 flex items-center justify-center text-[#06090f] text-xs font-bold">
            ML
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-semibold text-slate-100 truncate">Mohammed Like</div>
          </div>
        </div>
      </div>
    </aside>
  );
};
