import { useState, useRef, useEffect } from 'react';
import { ChatPanel } from './components/chat/ChatPanel';
import { StrategyBuilder, type StrategyBuilderRef } from './components/backtest/StrategyBuilder';
import { PredefinedStrategies } from './components/backtest/PredefinedStrategies';
import { IndicatorsLibrary } from './components/backtest/IndicatorsLibrary';
import { BacktestDashboard } from './components/backtest/BacktestDashboard';
import { useBacktestStore } from './stores/backtestStore';
import { Settings2, Layers, BookOpen, LineChart, Cpu } from 'lucide-react';

type WorkstationTab = 'dashboard' | 'builder' | 'gallery' | 'indicators';

function App() {
  const [activeTab, setActiveTab] = useState<WorkstationTab>('dashboard');
  const builderRef = useRef<StrategyBuilderRef>(null);
  const { latestBacktest } = useBacktestStore();

  // If a backtest finishes executing (either via builder or AI), focus the dashboard to show results
  useEffect(() => {
    if (latestBacktest) {
      setActiveTab('dashboard');
    }
  }, [latestBacktest]);

  const handleLoadStrategy = (spec: any) => {
    builderRef.current?.loadStrategySpec(spec);
    setActiveTab('builder');
  };

  const handleSelectIndicator = (indicatorName: string, defaults: any, type: 'entry' | 'exit') => {
    builderRef.current?.loadIndicatorToRule(indicatorName, defaults, type);
    setActiveTab('builder');
  };

  return (
    <div className="h-screen w-screen bg-[#06090f] flex flex-col font-sans overflow-hidden select-none text-slate-200">
      {/* Top Glassmorphic Navigation Header */}
      <header className="h-14 bg-[#0a0e17] border-b border-slate-800/60 px-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded bg-[#00d09c] flex items-center justify-center text-[#06090f] shadow-lg shadow-[#00d09c]/20">
            <Cpu size={18} />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-black text-white tracking-tighter">STREAK <span className="text-[#00d09c]">AI</span></span>
              <span className="bg-[#00d09c]/10 text-[#00d09c] text-[9px] font-bold font-mono px-1.5 py-0.5 rounded border border-[#00d09c]/30">
                PRO v3.0
              </span>
            </div>
            <p className="text-[10px] text-slate-500 font-medium">Next-Gen Indian Market Backtesting Engine</p>
          </div>
        </div>
        
        {/* Connection status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-slate-800/40 rounded-full border border-slate-700/50">
            <span className="h-1.5 w-1.5 rounded-full bg-[#00d09c] shadow-[0_0_8px_rgba(0,208,156,0.6)]"></span>
            <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">NSE LIVE</span>
          </div>
          <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 hover:bg-slate-700 transition cursor-pointer">
            <Settings2 size={14} className="text-slate-400" />
          </div>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <div className="flex-1 flex overflow-hidden p-4 gap-4">
        
        {/* Left Side: Backtesting Panel Console */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          
          {/* Workstation Tabs */}
          <div className="flex bg-[#0a0e17] p-1 border border-slate-800/80 rounded-lg max-w-fit">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded text-xs font-bold transition cursor-pointer ${
                activeTab === 'dashboard'
                  ? 'bg-[#00d09c] text-[#06090f]'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <LineChart size={14} />
              DASHBOARD
            </button>
            <button
              onClick={() => setActiveTab('builder')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded text-xs font-bold transition cursor-pointer ${
                activeTab === 'builder'
                  ? 'bg-[#00d09c] text-[#06090f]'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Settings2 size={14} />
              STRATEGY BUILDER
            </button>
            <button
              onClick={() => setActiveTab('gallery')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded text-xs font-bold transition cursor-pointer ${
                activeTab === 'gallery'
                  ? 'bg-[#00d09c] text-[#06090f]'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers size={14} />
              DISCOVER
            </button>
            <button
              onClick={() => setActiveTab('indicators')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded text-xs font-bold transition cursor-pointer ${
                activeTab === 'indicators'
                  ? 'bg-[#00d09c] text-[#06090f]'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BookOpen size={14} />
              INDICATORS
            </button>
          </div>

          {/* Tab Content Display */}
          <div className="flex-1 overflow-y-auto pr-1">
            {activeTab === 'dashboard' && <BacktestDashboard />}
            <div className={activeTab === 'builder' ? 'block' : 'hidden'}>
              <StrategyBuilder ref={builderRef} onBacktestCompleted={() => setActiveTab('dashboard')} />
            </div>
            {activeTab === 'gallery' && (
              <PredefinedStrategies onLoadStrategy={handleLoadStrategy} />
            )}
            {activeTab === 'indicators' && (
              <div className="h-[520px]">
                <IndicatorsLibrary onSelectIndicator={handleSelectIndicator} />
              </div>
            )}
          </div>
        </div>

        {/* Right Side: AI Assistant Panel */}
        <div className="w-[400px] min-w-[400px] h-full flex flex-col bg-[#0a0e17] border border-slate-800/80 rounded-xl overflow-hidden shadow-2xl">
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}

export default App;
