import { useState, useEffect, useRef } from 'react';
import { useBacktestStore } from './stores/backtestStore';
import { ChatPanel } from './components/chat/ChatPanel';
import { Cpu } from 'lucide-react';
import { Sidebar, type AppView } from './components/layout/Sidebar';
import { DashboardView } from './components/dashboard/DashboardView';
import { StrategyExplorer } from './components/strategy/StrategyExplorer';
import { StrategyBuilder, type StrategyBuilderRef } from './components/backtest/StrategyBuilder';
import { BacktestDashboard } from './components/backtest/BacktestDashboard';
import { BacktestHistoryView } from './components/backtest/BacktestHistoryView';

function App() {
  const { runBacktest, fetchIndicators } = useBacktestStore();
  const builderRef = useRef<StrategyBuilderRef>(null);

  const [activeView, setActiveView] = useState<AppView>('dashboard');
  const [tradingMode, setTradingMode] = useState<'live' | 'virtual'>('virtual');
  const [period] = useState('2y');

  useEffect(() => { fetchIndicators(); }, [fetchIndicators]);

  const handleRunInstant = async (spec: any) => {
    if (!spec) return;
    const targetSymbol = (spec.symbol || 'NIFTY').toUpperCase();
    const { symbol: _ignored, ...strategySpec } = spec;
    setActiveView('backtest');
    builderRef.current?.loadStrategySpec({ ...strategySpec, symbol: targetSymbol });
    await runBacktest(targetSymbol, strategySpec, period);
  };

  return (
    <div className="h-screen w-screen bg-[#0c1222] flex overflow-hidden font-sans text-slate-200">
      <Sidebar
        activeView={activeView}
        onNavigate={setActiveView}
        tradingMode={tradingMode}
        onTradingModeChange={setTradingMode}
      />

      <div className="flex-1 flex flex-col overflow-hidden bg-[#0c1222]">
        {activeView === 'dashboard' && (
          <DashboardView onNavigate={(v) => setActiveView(v as AppView)} onRunStrategy={handleRunInstant} />
        )}
        {activeView === 'strategies' && <StrategyExplorer onRunStrategy={handleRunInstant} />}
        {activeView === 'history' && (
          <BacktestHistoryView
            onRunStrategy={() => setActiveView('backtest')}
            onLoaded={() => setActiveView('backtest')}
          />
        )}
        {activeView === 'backtest' && (
          <div className="h-full flex flex-col overflow-hidden text-slate-200 bg-[#0c1222]">
            <header className="h-12 bg-[#131c31] border-b border-slate-800/60 px-4 flex items-center justify-between shrink-0 z-10">
              <div className="flex items-center gap-3">
                <div className="h-7 w-7 rounded bg-brand flex items-center justify-center text-white">
                  <Cpu size={14} />
                </div>
                <span className="text-xs font-black text-white tracking-tighter">
                  STRYKE <span className="text-brand-light">X</span>
                </span>
                <span className="text-[8px] text-slate-600 font-mono">PRO BACKTEST ENGINE</span>
              </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
              <div className="flex-1 flex flex-col overflow-hidden min-w-0">
                <div className="flex-1 p-4 overflow-auto space-y-4">
                  <StrategyBuilder ref={builderRef} />
                  <BacktestDashboard />
                </div>
              </div>

              <div className="w-[340px] min-w-[340px] border-l border-slate-800/80 bg-[#131c31] flex flex-col">
                <ChatPanel />
              </div>
            </div>
          </div>
        )}

        {!['dashboard', 'strategies', 'backtest', 'history'].includes(activeView) && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-xl font-bold text-slate-200 mb-2">View Under Development</h2>
              <p className="text-slate-500">The {activeView} view is currently being implemented.</p>
              <button
                onClick={() => setActiveView('dashboard')}
                className="mt-4 px-4 py-2 bg-brand text-white rounded-lg text-sm font-bold cursor-pointer"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
