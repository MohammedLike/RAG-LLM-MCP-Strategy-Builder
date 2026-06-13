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
    <aside className="w-[220px] min-w-[220px] h-full bg-white border-r border-[#e5e9f0] flex flex-col">
      <div className="px-5 py-5 border-b border-[#e5e9f0]">
        <div className="flex items-center gap-1">
          <span className="text-xl font-bold text-slate-900 tracking-tight">Stryke</span>
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
                  ? 'bg-brand text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
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

      <div className="p-3 space-y-3 border-t border-[#e5e9f0]">
        <div className="rounded-xl bg-gradient-to-br from-[#1a56db] to-[#0f3d99] p-4 text-white">
          <div className="flex items-center gap-2 mb-3">
            <Zap size={16} />
            <span className="text-sm font-semibold">Trading Mode</span>
          </div>
          <div className="flex rounded-lg bg-white/15 p-0.5">
            {(['live', 'virtual'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => onTradingModeChange(mode)}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-md capitalize transition ${
                  tradingMode === mode ? 'bg-white text-brand' : 'text-white/80'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>

        <div className="card px-3 py-2.5 flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand-light flex items-center justify-center">
            <Zap size={14} className="text-brand" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-900">Unlimited</div>
            <div className="text-[10px] text-muted">Deployment & Backtests</div>
          </div>
        </div>

        <div className="flex items-center gap-2 px-2 py-1">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand to-blue-400 flex items-center justify-center text-white text-xs font-bold">
            ML
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-semibold text-slate-900 truncate">Mohammed Like</div>
          </div>
        </div>
      </div>
    </aside>
  );
};
