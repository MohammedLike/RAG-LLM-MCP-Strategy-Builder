import { Bell, LayoutGrid } from 'lucide-react';
import type { AppView } from './Sidebar';

const titles: Record<AppView, string> = {
  dashboard: 'Dashboard',
  strategies: 'Pre-Built Algos',
  'my-algos': 'My Algos',
  backtest: 'Strategy Builder',
  account: 'My Account',
  contact: 'Contact Us',
  faq: 'FAQ',
};

interface TopHeaderProps {
  activeView: AppView;
}

export const TopHeader = ({ activeView }: TopHeaderProps) => {
  return (
    <header className="h-14 min-h-[56px] bg-white border-b border-[#e5e9f0] flex items-center justify-between px-6">
      <div className="flex items-center gap-2 text-slate-800">
        <LayoutGrid size={18} className="text-muted" />
        <h1 className="text-base font-semibold">{titles[activeView]}</h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden md:flex items-center gap-6 px-4 py-1.5 rounded-lg border border-[#e5e9f0] bg-slate-50/50">
          <div>
            <div className="text-[10px] text-muted uppercase tracking-wide">Margin Available</div>
            <div className="text-sm font-bold text-slate-900">₹0.00</div>
          </div>
          <div className="w-px h-8 bg-[#e5e9f0]" />
          <div>
            <div className="text-[10px] text-muted uppercase tracking-wide">Token Expiry</div>
            <div className="text-sm font-semibold text-slate-700">Jun 12, 2026 09:00</div>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-success" />
            <span className="text-xs font-semibold text-success">Connected</span>
          </div>
        </div>

        <button className="relative p-2 rounded-lg hover:bg-slate-50 text-muted">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger rounded-full" />
        </button>

        <div className="flex items-center gap-2 pl-2 border-l border-[#e5e9f0]">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-brand flex items-center justify-center text-white text-xs font-bold">
            ML
          </div>
          <div className="hidden sm:block">
            <div className="text-sm font-semibold text-slate-900 leading-tight">Mohammed Like</div>
            <div className="text-[11px] text-muted">@mohammedlike</div>
          </div>
        </div>
      </div>
    </header>
  );
};
