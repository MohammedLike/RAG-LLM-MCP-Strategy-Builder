import { useState } from 'react';
import { Sidebar, type AppView } from './components/layout/Sidebar';
import { TopHeader } from './components/layout/TopHeader';
import { PlaceholderView } from './components/layout/PlaceholderView';
import { DashboardView } from './components/dashboard/DashboardView';
import { StrategyExplorer } from './components/strategy/StrategyExplorer';
import { BacktestPanel } from './components/backtest/BacktestPanel';
import { ChatDrawer } from './components/chat/ChatDrawer';
import { ChatFab } from './components/chat/ChatFab';
import { Briefcase, Bot, User, Phone, HelpCircle } from 'lucide-react';

function App() {
  const [view, setView] = useState<AppView>('dashboard');
  const [chatOpen, setChatOpen] = useState(false);
  const [tradingMode, setTradingMode] = useState<'live' | 'virtual'>('live');

  const renderContent = () => {
    switch (view) {
      case 'dashboard':
        return <DashboardView onNavigate={(v) => setView(v)} />;
      case 'strategies':
        return <StrategyExplorer />;
      case 'backtest':
        return <BacktestPanel />;
      case 'portfolio':
        return (
          <PlaceholderView
            title="Portfolio"
            description="Track your deployed algos, P&L, and capital allocation across strategies."
            icon={<Briefcase size={28} />}
          />
        );
      case 'my-algos':
        return (
          <PlaceholderView
            title="My Algos"
            description="Manage your custom and deployed algorithmic strategies."
            icon={<Bot size={28} />}
          />
        );
      case 'account':
        return (
          <PlaceholderView
            title="My Account"
            description="Broker connection, API tokens, subscription, and profile settings."
            icon={<User size={28} />}
          />
        );
      case 'contact':
        return (
          <PlaceholderView
            title="Contact Us"
            description="Reach out to the StrykeX support team for help with your account."
            icon={<Phone size={28} />}
          />
        );
      case 'faq':
        return (
          <PlaceholderView
            title="FAQ"
            description="Frequently asked questions about algo trading, deployment, and backtesting."
            icon={<HelpCircle size={28} />}
          />
        );
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="h-screen w-screen flex bg-[#f4f6f9] overflow-hidden">
      <Sidebar
        activeView={view}
        onNavigate={setView}
        tradingMode={tradingMode}
        onTradingModeChange={setTradingMode}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <TopHeader activeView={view} />
        <main className="flex-1 overflow-hidden relative">{renderContent()}</main>
      </div>
      <ChatFab onClick={() => setChatOpen(true)} />
      <ChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}

export default App;
