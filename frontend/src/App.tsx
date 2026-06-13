import { useState, useEffect, useRef } from 'react';
import { useBacktestStore } from './stores/backtestStore';
import { ChatPanel } from './components/chat/ChatPanel';
import {
  Play, Loader2, Settings2, TrendingUp, TrendingDown,
  BarChart3, List, Activity, Zap, ChevronDown, ChevronUp,
  Cpu, Search
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, ComposedChart, Line
} from 'recharts';
import { fetchCompanies } from './services/api';
import type { Condition } from './types';
import { Sidebar, type AppView } from './components/layout/Sidebar';
import { DashboardView } from './components/dashboard/DashboardView';
import { StrategyExplorer } from './components/strategy/StrategyExplorer';

const defaultCondition = (): Condition => ({
  id: crypto.randomUUID(),
  indicator: 'RSI',
  params: { timeperiod: 14 },
  operator: '<',
  valueType: 'value',
  value: 30,
  compareIndicator: 'SMA',
  compareParams: { timeperiod: 20 }
});

function App() {
  const { latestBacktest, runBacktest, loading, error, fetchIndicators, indicators } = useBacktestStore();

  const [activeView, setActiveView] = useState<AppView>('dashboard');
  const [tradingMode, setTradingMode] = useState<'live' | 'virtual'>('virtual');

  const [symbol, setSymbol] = useState('NIFTY');
  const [symbolSearch, setSymbolSearch] = useState('NIFTY');
  const [period, setPeriod] = useState('2y');
  const [instrumentType, setInstrumentType] = useState<'EQUITY' | 'OPTION'>('EQUITY');
  const [optionType, setOptionType] = useState('CE');
  const [strike, setStrike] = useState('ATM');
  const [fees, setFees] = useState(0.001);
  const [slippage, setSlippage] = useState(0.001);
  const [stopLoss, setStopLoss] = useState(0.0);
  const [takeProfit, setTakeProfit] = useState(0.0);
  const [showBuilder, setShowBuilder] = useState(true);
  const [showTradeLog, setShowTradeLog] = useState(true);
  const [companies, setCompanies] = useState<{symbol: string, name: string}[]>([]);
  const [showSymbolDropdown, setShowSymbolDropdown] = useState(false);
  const [chartView, setChartView] = useState<'equity' | 'both'>('both');

  const [entryConditions, setEntryConditions] = useState<Condition[]>([defaultCondition()]);
  const [exitConditions, setExitConditions] = useState<Condition[]>([{...defaultCondition(), operator: '>', value: 70}]);

  useEffect(() => { fetchIndicators(); }, [fetchIndicators]);
  useEffect(() => {
    fetchCompanies().then(list => {
      setCompanies(list || []);
      const match = list?.find((c: any) => c.symbol === 'NIFTY');
      if (match) setSymbolSearch(`${match.symbol} - ${match.name}`);
    }).catch(() => {});
  }, []);

  const addCondition = (type: 'entry' | 'exit') => {
    if (type === 'entry') setEntryConditions([...entryConditions, defaultCondition()]);
    else setExitConditions([...exitConditions, defaultCondition()]);
  };
  const removeCondition = (type: 'entry' | 'exit', id: string) => {
    if (type === 'entry' && entryConditions.length > 1) setEntryConditions(entryConditions.filter(c => c.id !== id));
    if (type === 'exit' && exitConditions.length > 1) setExitConditions(exitConditions.filter(c => c.id !== id));
  };
  const updateCondition = (type: 'entry' | 'exit', id: string, fields: Partial<Condition>) => {
    if (type === 'entry') setEntryConditions(entryConditions.map(c => c.id === id ? { ...c, ...fields } : c));
    else setExitConditions(exitConditions.map(c => c.id === id ? { ...c, ...fields } : c));
  };

  const handleRun = async () => {
    const formatConds = (conds: Condition[]) => conds.map(c => {
      const spec: any = { indicator: c.indicator, params: c.params, operator: c.operator };
      if (c.valueType === 'indicator') spec.value = { indicator: c.compareIndicator, params: c.compareParams };
      else spec.value = Number(c.value);
      return spec;
    });

    const strategySpec: any = {
      entry: { conditions: formatConds(entryConditions), logical_operator: 'AND' },
      exit: { conditions: formatConds(exitConditions), logical_operator: 'AND' },
      instrument_type: instrumentType,
      fees, slippage
    };
    if (stopLoss > 0) strategySpec.stop_loss = stopLoss;
    if (takeProfit > 0) strategySpec.take_profit = takeProfit;
    if (instrumentType === 'OPTION') {
      strategySpec.strike = strike;
      strategySpec.option_type = optionType;
    }

    await runBacktest(symbol, strategySpec, period);
  };

  const handleRunInstant = async (spec: any) => {
    if (!spec) return;
    const targetSymbol = (spec.symbol || 'NIFTY').toUpperCase();
    const { symbol: _ignored, ...strategySpec } = spec;
    setSymbol(targetSymbol);
    setSymbolSearch(targetSymbol);
    setActiveView('backtest');
    await runBacktest(targetSymbol, strategySpec, period);
  };

  const metrics = latestBacktest ? [
    { label: 'Total Return', value: `${latestBacktest.total_return.toFixed(2)}%`, color: latestBacktest.total_return >= 0 ? 'text-emerald-400' : 'text-red-400' },
    { label: 'CAGR', value: `${latestBacktest.cagr?.toFixed(2) || '0.00'}%`, color: 'text-emerald-400' },
    { label: 'Sharpe', value: latestBacktest.sharpe?.toFixed(2) || '0.00', color: latestBacktest.sharpe >= 1 ? 'text-emerald-400' : 'text-yellow-400' },
    { label: 'Sortino', value: latestBacktest.sortino?.toFixed(2) || '0.00', color: 'text-blue-400' },
    { label: 'Max DD', value: `${latestBacktest.max_drawdown.toFixed(2)}%`, color: 'text-red-400' },
    { label: 'Calmar', value: latestBacktest.calmar?.toFixed(2) || '0.00', color: latestBacktest.calmar >= 1 ? 'text-emerald-400' : 'text-yellow-400' },
    { label: 'Win Rate', value: `${latestBacktest.win_rate.toFixed(1)}%`, color: latestBacktest.win_rate >= 50 ? 'text-emerald-400' : 'text-red-400' },
    { label: 'Profit Factor', value: latestBacktest.profit_factor?.toFixed(2) || '0.00', color: latestBacktest.profit_factor >= 1.5 ? 'text-emerald-400' : 'text-yellow-400' },
  ] : [];

  const renderConditionRow = (cond: Condition, index: number, type: 'entry' | 'exit') => (
    <div key={cond.id} className="flex flex-wrap items-center gap-1.5 bg-slate-900/50 p-2 rounded border border-slate-700/50 text-[10px]">
      <span className="text-slate-500 font-mono w-4">{index + 1}.</span>
      <select value={cond.indicator} onChange={e => updateCondition(type, cond.id, { indicator: e.target.value, params: indicators[e.target.value]?.params || {} })}
        className="bg-slate-800 border border-slate-600 rounded px-1.5 py-0.5 text-slate-200 text-[10px]">
        {Object.keys(indicators).length > 0 ? Object.keys(indicators).map(k => <option key={k} value={k}>{k}</option>)
          : ['RSI','SMA','EMA','MACD','VWAP'].map(k => <option key={k} value={k}>{k}</option>)}
      </select>
      {Object.entries(cond.params).filter(([k]) => k !== 'output_index').map(([k, v]) => (
        <input key={k} type="text" value={String(v)} onChange={e => updateCondition(type, cond.id, { params: {...cond.params, [k]: isNaN(Number(e.target.value)) ? e.target.value : Number(e.target.value)} })}
          className="w-10 bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-slate-200 text-[10px] text-center" title={k} />
      ))}
      <select value={cond.operator} onChange={e => updateCondition(type, cond.id, { operator: e.target.value })}
        className="bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-slate-200 text-[10px]">
        <option value="<">&lt;</option><option value=">">&gt;</option>
        <option value="<=">&le;</option><option value=">=">&ge;</option>
        <option value="==">=</option>
        <option value="crosses_above">crosses above</option><option value="crosses_below">crosses below</option>
      </select>
      <select value={cond.valueType} onChange={e => updateCondition(type, cond.id, { valueType: e.target.value as 'value' | 'indicator' })}
        className="bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-slate-200 text-[10px]">
        <option value="value">Value</option><option value="indicator">Indicator</option>
      </select>
      {cond.valueType === 'value' ? (
        <input type="number" value={cond.value} onChange={e => updateCondition(type, cond.id, { value: Number(e.target.value) })}
          className="w-14 bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-slate-200 text-[10px] text-center" />
      ) : (
        <select value={cond.compareIndicator} onChange={e => updateCondition(type, cond.id, { compareIndicator: e.target.value, compareParams: indicators[e.target.value]?.params || {} })}
          className="bg-slate-800 border border-slate-600 rounded px-1 py-0.5 text-slate-200 text-[10px]">
          {Object.keys(indicators).length > 0 ? Object.keys(indicators).map(k => <option key={k} value={k}>{k}</option>)
            : ['SMA','EMA','RSI'].map(k => <option key={k} value={k}>{k}</option>)}
        </select>
      )}
      <button onClick={() => removeCondition(type, cond.id)} className="text-slate-600 hover:text-red-400 p-0.5 cursor-pointer"
        disabled={(type==='entry'?entryConditions:exitConditions).length<=1}>&times;</button>
    </div>
  );

  return (
    <div className="h-screen w-screen bg-[#0c1222] flex overflow-hidden font-sans text-slate-200">
      <Sidebar 
        activeView={activeView} 
        onNavigate={setActiveView} 
        tradingMode={tradingMode} 
        onTradingModeChange={setTradingMode} 
      />
      
      <div className="flex-1 flex flex-col overflow-hidden bg-[#0c1222]">
        {activeView === 'dashboard' && <DashboardView onNavigate={(v) => setActiveView(v as any)} onRunStrategy={handleRunInstant} />}
        {activeView === 'strategies' && <StrategyExplorer onRunStrategy={handleRunInstant} />}
        {activeView === 'backtest' && (
          <div className="h-full flex flex-col overflow-hidden text-slate-200 bg-[#0c1222]">
            {/* TOP HEADER */}
            <header className="h-12 bg-[#131c31] border-b border-slate-800/60 px-4 flex items-center justify-between shrink-0 z-10">
              <div className="flex items-center gap-3">
                <div className="h-7 w-7 rounded bg-brand flex items-center justify-center text-white"><Cpu size={14} /></div>
                <span className="text-xs font-black text-white tracking-tighter">STREAK <span className="text-brand-light">AI</span></span>
                <span className="text-[8px] text-slate-600 font-mono">PRO SIMULATOR</span>
              </div>
            </header>

            <div className="flex-1 flex overflow-hidden">
              {/* MAIN CONTENT */}
              <div className="flex-1 flex flex-col overflow-hidden min-w-0">
                {/* KPI STRIP */}
                {latestBacktest && (
                  <div className="flex gap-2 px-3 py-1.5 bg-slate-900/40 border-b border-slate-800/40 overflow-x-auto shrink-0">
                    {metrics.map(m => (
                      <div key={m.label} className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/60 rounded border border-slate-800/50 shrink-0">
                        <span className="text-[8px] font-bold text-slate-500 uppercase tracking-wider">{m.label}</span>
                        <span className={`text-[11px] font-black font-mono ${m.color}`}>{m.value}</span>
                      </div>
                    ))}
                  </div>
                )}

                {error && (
                  <div className="mx-3 mt-2 px-3 py-2 bg-red-950/30 border border-red-900/50 text-red-300 rounded text-[10px] font-medium shrink-0">{error}</div>
                )}

                {/* MAIN CHART AREA */}
                <div className="flex-1 p-3 overflow-auto">
                  {loading && (
                    <div className="h-48 flex flex-col items-center justify-center mb-3">
                      <div className="relative h-10 w-10 mb-3">
                        <div className="absolute inset-0 rounded-full border-2 border-slate-800"></div>
                        <div className="absolute inset-0 rounded-full border-2 border-brand border-t-transparent animate-spin"></div>
                      </div>
                      <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Backtesting {symbol}...</p>
                    </div>
                  )}

                  {!loading && (
                    <div className="flex flex-col gap-3">
                      {!latestBacktest && (
                        <div className="py-8 flex flex-col items-center justify-center text-center bg-[#131c31] border border-slate-800/80 rounded-lg">
                          <div className="h-12 w-12 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-center mb-3">
                            <BarChart3 className="text-slate-600" size={24} />
                          </div>
                          <h3 className="text-sm font-black text-slate-400 uppercase tracking-tight">Backtest Simulator Ready</h3>
                          <p className="text-[10px] text-slate-600 mt-1 max-w-md">Configure entry/exit conditions below, select a symbol, and hit RUN.</p>
                        </div>
                      )}

                      {latestBacktest && (
                        <div className="bg-[#131c31] border border-slate-800/80 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className="h-2 w-2 rounded-full bg-brand"></div>
                              <h3 className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Performance {chartView === 'both' ? '& Drawdown' : 'Curve'}</h3>
                            </div>
                            <div className="flex bg-slate-900 rounded p-0.5 border border-slate-800">
                              <button onClick={() => setChartView('equity')}
                                className={`px-2 py-0.5 rounded text-[8px] font-black tracking-wider cursor-pointer ${chartView==='equity'?'bg-brand text-white':'text-slate-500 hover:text-slate-300'}`}>EQUITY</button>
                            <button onClick={() => setChartView('both')}
                                className={`px-2 py-0.5 rounded text-[8px] font-black tracking-wider cursor-pointer ${chartView==='both'?'bg-brand text-white':'text-slate-500 hover:text-slate-300'}`}>BOTH</button>
                            </div>
                          </div>
                          <ResponsiveContainer width="100%" height={220}>
                            <ComposedChart data={latestBacktest.equity_curve}>
                              <defs>
                                <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/>
                                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                </linearGradient>
                                <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.1}/>
                                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} strokeOpacity={0.2} />
                              <XAxis dataKey="date" tick={{fontSize:8,fill:'#64748b'}} axisLine={false} tickLine={false} />
                              <YAxis yAxisId="equity" tick={{fontSize:8,fill:'#64748b'}} axisLine={false} tickLine={false} domain={['auto','auto']} />
                              {chartView === 'both' && (
                                <YAxis yAxisId="drawdown" orientation="right" tick={{fontSize:8,fill:'#64748b'}} axisLine={false} tickLine={false}
                                  domain={[-100, 5]} tickFormatter={(v: number) => `${v.toFixed(0)}%`} />
                              )}
                              <Tooltip contentStyle={{backgroundColor:'#131c31',border:'1px solid #1e293b',borderRadius:4,color:'#f8fafc',fontSize:10}} />
                              <Area yAxisId="equity" type="monotone" dataKey="value" stroke="#3b82f6" fill="url(#eqGrad)" strokeWidth={2} name="Equity" />
                              {chartView === 'both' && latestBacktest.drawdown && (
                                <Area yAxisId="drawdown" type="monotone" data={latestBacktest.drawdown} dataKey="value" stroke="#ef4444" fill="url(#ddGrad)" strokeWidth={1.5} name="Drawdown %" />
                              )}
                            </ComposedChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {/* STRATEGY BUILDER - always visible */}
                      <div className="bg-[#131c31] border border-slate-800/80 rounded-lg">
                        <button onClick={() => setShowBuilder(!showBuilder)}
                          className="w-full flex items-center justify-between px-4 py-2.5 text-[10px] font-black text-slate-400 uppercase tracking-widest cursor-pointer hover:text-slate-200 transition">
                          <span className="flex items-center gap-2"><Settings2 size={12} /> Strategy Builder</span>
                          {showBuilder ? <ChevronUp size={12}/> : <ChevronDown size={12}/>}
                        </button>
                        {showBuilder && (
                          <div className="px-4 pb-4 space-y-3 border-t border-slate-800/50 pt-3">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-[9px] font-bold text-blue-400 uppercase tracking-wider">Entry (Buy)</span>
                                  <button onClick={() => addCondition('entry')} className="text-[9px] text-blue-400 hover:text-blue-300 cursor-pointer">+ Add</button>
                                </div>
                                <div className="space-y-1">{entryConditions.map((c, i) => renderConditionRow(c, i, 'entry'))}</div>
                              </div>
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-[9px] font-bold text-emerald-400 uppercase tracking-wider">Exit (Sell)</span>
                                  <button onClick={() => addCondition('exit')} className="text-[9px] text-emerald-400 hover:text-emerald-300 cursor-pointer">+ Add</button>
                                </div>
                                <div className="space-y-1">{exitConditions.map((c, i) => renderConditionRow(c, i, 'exit'))}</div>
                              </div>
                            </div>
                            <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/40 text-[9px] mt-2">
                              <div className="flex flex-wrap items-center gap-3">
                                {/* Symbol Search */}
                                <div className="relative">
                                  <input type="text" value={symbolSearch} onFocus={() => setShowSymbolDropdown(true)}
                                    onChange={e => { setSymbolSearch(e.target.value); setShowSymbolDropdown(true); const s = e.target.value.split(' - ')[0].trim().toUpperCase(); if (s) setSymbol(s); }}
                                    className="w-32 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[9px]" placeholder="Symbol..." />
                                  {showSymbolDropdown && companies.length > 0 && (
                                    <><div className="fixed inset-0 z-10" onClick={() => setShowSymbolDropdown(false)} />
                                      <div className="absolute bottom-full left-0 mb-1 bg-slate-900 border border-slate-800 rounded max-h-40 overflow-y-auto z-20 w-48">
                                        {companies.filter(c => c.symbol.toLowerCase().includes(symbolSearch.split(' - ')[0].toLowerCase())).slice(0, 30).map(c => (
                                          <div key={c.symbol} onClick={() => { setSymbol(c.symbol); setSymbolSearch(`${c.symbol} - ${c.name}`); setShowSymbolDropdown(false); }}
                                            className="px-2 py-1 text-[9px] hover:bg-blue-600/30 cursor-pointer text-slate-300">{c.symbol} <span className="text-slate-600">{c.name}</span></div>
                                        ))}
                                      </div>
                                    </>
                                  )}
                                </div>
                                
                                {/* Period */}
                                <select value={period} onChange={e => setPeriod(e.target.value)}
                                  className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[9px]">
                                  <option value="1y">1Y</option><option value="2y">2Y</option><option value="5y">5Y</option><option value="8y">8Y</option>
                                </select>

                                {/* Instrument Type */}
                                <select value={instrumentType} onChange={e => setInstrumentType(e.target.value as 'EQUITY'|'OPTION')}
                                  className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[9px]">
                                  <option value="EQUITY">Equity</option><option value="OPTION">Option</option>
                                </select>

                                {/* Options Strike / Option Type */}
                                {instrumentType === 'OPTION' && (
                                  <>
                                    <select value={optionType} onChange={e => setOptionType(e.target.value)}
                                      className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[9px]">
                                      <option value="CE">CE</option><option value="PE">PE</option><option value="STRADDLE">Straddle</option>
                                    </select>
                                    <select value={strike} onChange={e => setStrike(e.target.value)}
                                      className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-[9px]">
                                      <option value="ITM-2">ITM-2</option><option value="ITM-1">ITM-1</option>
                                      <option value="ATM">ATM</option><option value="OTM+1">OTM+1</option><option value="OTM+2">OTM+2</option>
                                    </select>
                                  </>
                                )}

                                {/* Stop Loss */}
                                <label className="flex items-center gap-1 text-slate-500 font-bold uppercase"><span>SL%</span>
                                  <input type="number" step="0.01" value={stopLoss} onChange={e => setStopLoss(Number(e.target.value))}
                                    className="w-12 bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-slate-200 text-center" placeholder="SL%" />
                                </label>
                                
                                {/* Fees */}
                                <label className="flex items-center gap-1 text-slate-500 font-bold uppercase"><span>Fees</span>
                                  <input type="number" step="0.0001" value={fees} onChange={e => setFees(Number(e.target.value))}
                                    className="w-12 bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-slate-200 text-center" />
                                </label>

                                {/* Slippage */}
                                <label className="flex items-center gap-1 text-slate-500 font-bold uppercase"><span>Slippage</span>
                                  <input type="number" step="0.0001" value={slippage} onChange={e => setSlippage(Number(e.target.value))}
                                    className="w-12 bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-slate-200 text-center" />
                                </label>
                              </div>

                              <button onClick={handleRun} disabled={loading}
                                className="bg-brand hover:bg-brand-light disabled:bg-slate-700 text-white px-4 py-1.5 rounded text-[9px] font-black flex items-center gap-1.5 transition cursor-pointer disabled:cursor-not-allowed">
                                {loading ? <Loader2 size={10} className="animate-spin" /> : <Play size={10} />}
                                {loading ? 'RUNNING...' : 'RUN BACKTEST'}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* TRADE LOG */}
                      {latestBacktest && (
                      <div className="bg-[#131c31] border border-slate-800/80 rounded-lg">
                        <button onClick={() => setShowTradeLog(!showTradeLog)}
                          className="w-full flex items-center justify-between px-4 py-2.5 text-[10px] font-black text-slate-400 uppercase tracking-widest cursor-pointer hover:text-slate-200 transition">
                          <span className="flex items-center gap-2"><List size={12} /> Trade Log ({latestBacktest.trades?.length || 0} trades)</span>
                          {showTradeLog ? <ChevronUp size={12}/> : <ChevronDown size={12}/>}
                        </button>
                        {showTradeLog && (
                          <div className="px-4 pb-4 border-t border-slate-800/50 pt-2 overflow-x-auto max-h-64 overflow-y-auto">
                            {latestBacktest.trades && latestBacktest.trades.length > 0 ? (
                              <table className="w-full text-[10px] text-left">
                                <thead className="text-slate-500 uppercase text-[8px] font-black sticky top-0 bg-[#131c31]">
                                  <tr><th className="px-2 py-1.5">ID</th><th className="px-2 py-1.5">Entry</th><th className="px-2 py-1.5">Exit</th>
                                    <th className="px-2 py-1.5">Entry</th><th className="px-2 py-1.5">Exit</th><th className="px-2 py-1.5">P&L</th>
                                    <th className="px-2 py-1.5">Return</th><th className="px-2 py-1.5">Reason</th></tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800/40">
                                  {latestBacktest.trades.map((t: any) => (
                                    <tr key={t.id} className="hover:bg-slate-800/30">
                                      <td className="px-2 py-1.5 font-mono text-slate-600">#{t.id}</td>
                                      <td className="px-2 py-1.5 font-bold text-slate-400">{t.entry_date}</td>
                                      <td className="px-2 py-1.5 font-bold text-slate-400">{t.exit_date}</td>
                                      <td className="px-2 py-1.5 font-mono">{t.entry_price?.toFixed(2)}</td>
                                      <td className="px-2 py-1.5 font-mono">{t.exit_price?.toFixed(2)}</td>
                                      <td className={`px-2 py-1.5 font-black ${t.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {t.pnl >= 0 ? '+' : ''}{t.pnl?.toFixed(2) || '0.00'}
                                      </td>
                                      <td className="px-2 py-1.5"><span className={`px-1 py-0.5 rounded font-black text-[9px] ${t.pnl_pct >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                        {t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct?.toFixed(2) || '0.00'}%</span></td>
                                      <td className="px-2 py-1.5 text-slate-500">{t.exit_reason || 'Signal'}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            ) : (
                              <div className="py-6 text-center text-slate-600 text-[10px] font-bold uppercase tracking-widest">No trades executed</div>
                            )}
                          </div>
                        )}
                      </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* RIGHT SIDEBAR - AI CHAT */}
              <div className="w-[340px] min-w-[340px] border-l border-slate-800/80 bg-[#131c31] flex flex-col">
                <ChatPanel />
              </div>
            </div>
          </div>
        )}
        {/* Placeholder for other views */}
        {!['dashboard', 'strategies', 'backtest'].includes(activeView) && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-xl font-bold text-slate-900 mb-2">View Under Development</h2>
              <p className="text-slate-500">The {activeView} view is currently being implemented.</p>
              <button onClick={() => setActiveView('dashboard')} className="btn-primary mt-4 px-4 py-2">Go to Dashboard</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
