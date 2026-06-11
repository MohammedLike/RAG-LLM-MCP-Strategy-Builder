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
    <div className="h-screen w-screen bg-[#070b13] flex flex-col font-sans overflow-hidden select-none">
      {/* Top Glassmorphic Navigation Header */}
      <header className="h-14 bg-[#0a0f1d]/75 border-b border-slate-800/80 px-6 flex items-center justify-between backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <Cpu size={18} className="animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold text-slate-100 tracking-wide">ANTIGRAVITY</span>
              <span className="bg-blue-600/20 text-blue-400 text-[8px] font-bold font-mono px-1.5 py-0.5 rounded border border-blue-500/35">
                LABS v2.0
              </span>
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">AI-Integrated Quantitative Backtesting Engine</p>
          </div>
        </div>
        
        {/* Connection status */}
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)] animate-pulse"></span>
          <span className="text-[10px] font-mono text-slate-400">NSE Provider: Online</span>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <div className="flex-1 flex overflow-hidden p-4 gap-4">
        
        {/* Left Side: Backtesting Panel Console */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          
          {/* Workstation Tabs */}
          <div className="flex bg-[#0b0f19] p-1 border border-slate-800 rounded-xl max-w-fit shadow-md">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${
                activeTab === 'dashboard'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <LineChart size={14} />
              Performance Visualizer
            </button>
            <button
              onClick={() => setActiveTab('builder')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${
                activeTab === 'builder'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Settings2 size={14} />
              Strategy Builder
            </button>
            <button
              onClick={() => setActiveTab('gallery')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${
                activeTab === 'gallery'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers size={14} />
              Prebuilt Gallery
            </button>
            <button
              onClick={() => setActiveTab('indicators')}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition cursor-pointer ${
                activeTab === 'indicators'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <BookOpen size={14} />
              Indicators Catalog
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
        <div className="w-[380px] min-w-[380px] h-full flex flex-col">
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}

export default App;
