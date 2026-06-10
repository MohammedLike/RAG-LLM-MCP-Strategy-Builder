import React, { useState } from 'react'
import { ChatPanel } from './components/chat/ChatPanel'
import { MarketDashboard } from './components/market/MarketDashboard'
import { StrategyExplorer } from './components/strategy/StrategyExplorer'
import { BacktestPanel } from './components/backtest/BacktestPanel'

type View = 'chat' | 'market' | 'strategies' | 'backtest'

function App() {
  const [view, setView] = useState<View>('market')

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      <header className="h-16 border-b border-slate-800 flex items-center px-6 shadow-sm">
        <div className="w-8 h-8 rounded bg-accent-blue flex items-center justify-center mr-3 text-white font-bold">Q</div>
        <h1 className="text-xl font-bold tracking-tight">Quant AI Agent</h1>
      </header>
      <div className="flex-1 flex overflow-hidden">
        <aside className="w-64 border-r border-slate-800 bg-slate-900/50 p-4">
          <nav className="space-y-2">
            {[
              { id: 'chat', label: 'Chat Assistant' },
              { id: 'market', label: 'Live Market' },
              { id: 'strategies', label: 'Strategies' },
              { id: 'backtest', label: 'Backtesting Engine' }
            ].map(item => (
              <button
                key={item.id}
                onClick={() => setView(item.id as View)}
                className={`w-full text-left p-3 rounded-lg font-medium transition ${view === item.id ? 'bg-accent-blue text-white shadow-lg shadow-blue-500/20' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </aside>
        
        {/* Main Content Area */}
        <main className="flex-1 flex overflow-hidden">
          {/* Always show Chat Panel on the left as a sidebar if not explicitly viewing it? 
              Let's make chat always visible as a split pane, or conditionally.
              We'll make it a 2-pane view. Chat on left, context on right. */}
          <div className="w-[400px] h-full shadow-2xl z-10">
            <ChatPanel />
          </div>
          <div className="flex-1 h-full overflow-y-auto bg-slate-950 relative">
            {view === 'market' && <MarketDashboard />}
            {view === 'strategies' && <StrategyExplorer />}
            {view === 'backtest' && <BacktestPanel />}
            {view === 'chat' && (
              <div className="flex items-center justify-center h-full text-slate-500 flex-col gap-4">
                <div className="text-6xl">🤖</div>
                <h2 className="text-xl font-semibold">How can I help you analyze the market today?</h2>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
