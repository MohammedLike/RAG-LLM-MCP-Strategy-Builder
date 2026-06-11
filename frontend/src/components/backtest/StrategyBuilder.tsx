import { useState, forwardRef, useImperativeHandle, useEffect } from 'react';
import { useBacktestStore } from '../../stores/backtestStore';
import { Settings2, Plus, Trash2, Play, Loader2 } from 'lucide-react';
import { fetchCompanies } from '../../services/api';

interface Condition {
  id: string;
  indicator: string;
  params: Record<string, any>;
  operator: string;
  valueType: 'value' | 'indicator';
  value: number;
  compareIndicator: string;
  compareParams: Record<string, any>;
}

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

interface StrategyBuilderProps {
  onBacktestCompleted?: () => void;
}

export interface StrategyBuilderRef {
  loadStrategySpec: (spec: any) => void;
  loadIndicatorToRule: (indicatorName: string, defaults: any, ruleType: 'entry' | 'exit') => void;
}

export const StrategyBuilder = forwardRef<StrategyBuilderRef, StrategyBuilderProps>(
  ({ onBacktestCompleted }, ref) => {
    const { runBacktest, loading, indicators } = useBacktestStore();
    
    // Strategy configuration state
    const [symbol, setSymbol] = useState('NIFTY');
    const [period, setPeriod] = useState('2y');
    const [fees, setFees] = useState(0.001);
    const [slippage, setSlippage] = useState(0.001);

    const [companies, setCompanies] = useState<{symbol: string, name: string, sector: string}[]>([]);
    const [symbolSearch, setSymbolSearch] = useState('');
    const [showSymbolDropdown, setShowSymbolDropdown] = useState(false);

    useEffect(() => {
      const load = async () => {
        try {
          const list = await fetchCompanies();
          setCompanies(list);
          const active = list.find((c: any) => c.symbol.toUpperCase() === symbol.toUpperCase());
          if (active) {
            setSymbolSearch(`${active.symbol} - ${active.name}`);
          } else {
            setSymbolSearch(symbol);
          }
        } catch (err) {
          console.error(err);
        }
      };
      load();
    }, []);

    useEffect(() => {
      if (companies.length > 0) {
        const active = companies.find(c => c.symbol.toUpperCase() === symbol.toUpperCase());
        if (active) {
          setSymbolSearch(`${active.symbol} - ${active.name}`);
        } else {
          setSymbolSearch(symbol);
        }
      } else {
        setSymbolSearch(symbol);
      }
    }, [symbol, companies]);

    const [entryConditions, setEntryConditions] = useState<Condition[]>([
      {
        id: crypto.randomUUID(),
        indicator: 'RSI',
        params: { timeperiod: 14 },
        operator: '<',
        valueType: 'value',
        value: 30,
        compareIndicator: 'SMA',
        compareParams: { timeperiod: 20 }
      }
    ]);

    const [exitConditions, setExitConditions] = useState<Condition[]>([
      {
        id: crypto.randomUUID(),
        indicator: 'RSI',
        params: { timeperiod: 14 },
        operator: '>',
        valueType: 'value',
        value: 70,
        compareIndicator: 'SMA',
        compareParams: { timeperiod: 20 }
      }
    ]);

    // Handle loading a strategy spec from Predefined Gallery
    useImperativeHandle(ref, () => ({
      loadStrategySpec: (spec: any) => {
        if (!spec) return;
        
        // Helper to import conditions from spec
        const parseRules = (ruleGroup: any) => {
          if (!ruleGroup) return [defaultCondition()];
          
          const condList: any[] = [];
          const rawConds = ruleGroup.conditions || (ruleGroup.indicator ? [ruleGroup] : []);
          
          rawConds.forEach((c: any) => {
            const isCompIndicator = typeof c.value === 'object' && c.value !== null && 'indicator' in c.value;
            condList.push({
              id: crypto.randomUUID(),
              indicator: c.indicator || 'SMA',
              params: c.params || {},
              operator: c.operator || '==',
              valueType: isCompIndicator ? 'indicator' : 'value',
              value: isCompIndicator ? 0 : (c.value || 0),
              compareIndicator: isCompIndicator ? c.value.indicator : 'SMA',
              compareParams: isCompIndicator ? (c.value.params || {}) : { timeperiod: 20 }
            });
          });
          
          return condList.length > 0 ? condList : [defaultCondition()];
        };

        if (spec.entry) setEntryConditions(parseRules(spec.entry));
        if (spec.exit) setExitConditions(parseRules(spec.exit));
        if (spec.fees !== undefined) setFees(spec.fees);
        if (spec.slippage !== undefined) setSlippage(spec.slippage);
      },

      loadIndicatorToRule: (indicatorName: string, defaults: any, ruleType: 'entry' | 'exit') => {
        const newCond: Condition = {
          id: crypto.randomUUID(),
          indicator: indicatorName,
          params: { ...defaults },
          operator: indicatorName.startsWith('CDL') ? '>' : '==',
          valueType: 'value',
          value: indicatorName.startsWith('CDL') ? 0 : 50,
          compareIndicator: 'SMA',
          compareParams: { timeperiod: 20 }
        };

        if (ruleType === 'entry') {
          setEntryConditions(prev => [...prev.filter(c => c.indicator !== 'RSI' || prev.length > 1), newCond]);
        } else {
          setExitConditions(prev => [...prev.filter(c => c.indicator !== 'RSI' || prev.length > 1), newCond]);
        }
      }
    }));

    const addCondition = (type: 'entry' | 'exit') => {
      const list = type === 'entry' ? entryConditions : exitConditions;
      const setter = type === 'entry' ? setEntryConditions : setExitConditions;
      setter([...list, defaultCondition()]);
    };

    const removeCondition = (type: 'entry' | 'exit', id: string) => {
      const list = type === 'entry' ? entryConditions : exitConditions;
      const setter = type === 'entry' ? setEntryConditions : setExitConditions;
      if (list.length > 1) {
        setter(list.filter(c => c.id !== id));
      }
    };

    const updateCondition = (type: 'entry' | 'exit', id: string, fields: Partial<Condition>) => {
      const list = type === 'entry' ? entryConditions : exitConditions;
      const setter = type === 'entry' ? setEntryConditions : setExitConditions;
      setter(list.map(c => c.id === id ? { ...c, ...fields } : c));
    };

    const handleRunBacktest = async () => {
      // Formulate strategy spec
      const formatConditions = (conds: Condition[]) => {
        return conds.map(c => {
          const specCond: any = {
            indicator: c.indicator,
            params: c.params,
            operator: c.operator
          };
          if (c.valueType === 'indicator') {
            specCond.value = {
              indicator: c.compareIndicator,
              params: c.compareParams
            };
          } else {
            specCond.value = Number(c.value);
          }
          return specCond;
        });
      };

      const strategySpec = {
        entry: {
          conditions: formatConditions(entryConditions),
          logical_operator: 'AND'
        },
        exit: {
          conditions: formatConditions(exitConditions),
          logical_operator: 'AND'
        },
        fees,
        slippage
      };

      await runBacktest(symbol, strategySpec, period);
      if (onBacktestCompleted) {
        onBacktestCompleted();
      }
    };

    // Helper to render condition rows
    const renderConditionRow = (cond: Condition, index: number, type: 'entry' | 'exit') => {
      const indicatorKeys = Object.keys(indicators);
      const activeIndicatorInfo = indicators[cond.indicator];
      const activeCompareIndicatorInfo = indicators[cond.compareIndicator];

      return (
        <div key={cond.id} className="flex flex-wrap items-center gap-2 bg-[#0e1628] p-3 rounded-lg border border-slate-800/80 mb-2">
          <span className="text-[10px] font-mono text-slate-500 font-bold w-6">{index + 1}.</span>
          
          {/* LHS Indicator Selector */}
          <div className="flex flex-col">
            <span className="text-[8px] uppercase text-slate-500 font-bold mb-0.5">Indicator</span>
            <select
              value={cond.indicator}
              onChange={(e) => {
                const defaults = indicators[e.target.value]?.params || {};
                updateCondition(type, cond.id, { indicator: e.target.value, params: { ...defaults } });
              }}
              className="bg-slate-900 border border-slate-700/85 text-xs text-slate-200 rounded px-2.5 py-1 focus:outline-none"
            >
              {indicatorKeys.length > 0 ? (
                indicatorKeys.map(k => <option key={k} value={k}>{k}</option>)
              ) : (
                <>
                  <option value="RSI">RSI</option>
                  <option value="SMA">SMA</option>
                  <option value="EMA">EMA</option>
                  <option value="MACD">MACD</option>
                  <option value="VWAP">VWAP</option>
                  <option value="close">Close Price</option>
                </>
              )}
            </select>
          </div>

          {/* LHS Parameter Input (e.g. timeperiod) */}
          {activeIndicatorInfo && Object.keys(activeIndicatorInfo.params).length > 0 && (
            <div className="flex flex-col">
              <span className="text-[8px] uppercase text-slate-500 font-bold mb-0.5">Params</span>
              <div className="flex gap-1">
                {Object.entries(cond.params).map(([paramName, paramVal]) => (
                  <input
                    key={paramName}
                    type="text"
                    value={String(paramVal)}
                    placeholder={paramName}
                    title={paramName}
                    onChange={(e) => {
                      const val = isNaN(Number(e.target.value)) ? e.target.value : Number(e.target.value);
                      updateCondition(type, cond.id, {
                        params: { ...cond.params, [paramName]: val }
                      });
                    }}
                    className="w-12 bg-slate-900 border border-slate-700 text-[10px] text-center text-slate-300 rounded py-1"
                  />
                ))}
              </div>
            </div>
          )}

          {/* Comparison Operator */}
          <div className="flex flex-col">
            <span className="text-[8px] uppercase text-slate-500 font-bold mb-0.5">Operator</span>
            <select
              value={cond.operator}
              onChange={(e) => updateCondition(type, cond.id, { operator: e.target.value })}
              className="bg-slate-900 border border-slate-700/85 text-xs text-slate-200 rounded px-2 py-1 focus:outline-none font-medium"
            >
              <option value="<">&lt;</option>
              <option value=">">&gt;</option>
              <option value="<=">&le;</option>
              <option value=">=">&ge;</option>
              <option value="==">=</option>
              <option value="crosses_above">crosses above</option>
              <option value="crosses_below">crosses below</option>
            </select>
          </div>

          {/* RHS Mode (Value vs Indicator) */}
          <div className="flex flex-col">
            <span className="text-[8px] uppercase text-slate-500 font-bold mb-0.5">Compare To</span>
            <select
              value={cond.valueType}
              onChange={(e) => updateCondition(type, cond.id, { valueType: e.target.value as 'value' | 'indicator' })}
              className="bg-slate-900 border border-slate-700/85 text-xs text-slate-200 rounded px-2 py-1 focus:outline-none"
            >
              <option value="value">Static Value</option>
              <option value="indicator">Another Indicator</option>
            </select>
          </div>

          {/* RHS Input */}
          {cond.valueType === 'value' ? (
            <div className="flex flex-col">
              <span className="text-[8px] uppercase text-slate-500 font-bold mb-0.5">Value</span>
              <input
                type="number"
                value={cond.value}
                onChange={(e) => updateCondition(type, cond.id, { value: Number(e.target.value) })}
                className="w-16 bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded px-2 py-1 text-center focus:outline-none"
              />
            </div>
          ) : (
            <>
              {/* Compare Indicator */}
              <div className="flex flex-col">
                <span className="text-[8px] uppercase text-slate-500 font-bold mb-0.5">Indicator</span>
                <select
                  value={cond.compareIndicator}
                  onChange={(e) => {
                    const defaults = indicators[e.target.value]?.params || {};
                    updateCondition(type, cond.id, { compareIndicator: e.target.value, compareParams: { ...defaults } });
                  }}
                  className="bg-slate-900 border border-slate-700/85 text-xs text-slate-200 rounded px-2.5 py-1 focus:outline-none"
                >
                  {indicatorKeys.length > 0 ? (
                    indicatorKeys.map(k => <option key={k} value={k}>{k}</option>)
                  ) : (
                    <>
                      <option value="SMA">SMA</option>
                      <option value="EMA">EMA</option>
                      <option value="RSI">RSI</option>
                      <option value="close">Close Price</option>
                    </>
                  )}
                </select>
              </div>

              {/* Compare Params */}
              {activeCompareIndicatorInfo && Object.keys(activeCompareIndicatorInfo.params).length > 0 && (
                <div className="flex flex-col">
                  <span className="text-[8px] uppercase text-slate-500 font-bold mb-0.5">Params</span>
                  <div className="flex gap-1">
                    {Object.entries(cond.compareParams).map(([paramName, paramVal]) => (
                      <input
                        key={paramName}
                        type="text"
                        value={String(paramVal)}
                        placeholder={paramName}
                        onChange={(e) => {
                          const val = isNaN(Number(e.target.value)) ? e.target.value : Number(e.target.value);
                          updateCondition(type, cond.id, {
                            compareParams: { ...cond.compareParams, [paramName]: val }
                          });
                        }}
                        className="w-12 bg-slate-900 border border-slate-700 text-[10px] text-center text-slate-300 rounded py-1"
                      />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Delete Row button */}
          <button
            onClick={() => removeCondition(type, cond.id)}
            disabled={(type === 'entry' ? entryConditions : exitConditions).length <= 1}
            className="p-1.5 text-slate-500 hover:text-red-400 disabled:opacity-30 disabled:hover:text-slate-500 mt-3 transition cursor-pointer"
          >
            <Trash2 size={13} />
          </button>
        </div>
      );
    };

    return (
      <div className="bg-[#0b0f19] border border-slate-800 rounded-xl p-5 text-slate-100 shadow-xl flex flex-col gap-5">
        <div className="flex justify-between items-center border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Settings2 className="text-blue-500" size={18} />
            <div>
              <h3 className="font-bold text-slate-100 text-sm">Custom Strategy Builder Console</h3>
              <p className="text-[11px] text-slate-400">Assemble multi-condition logic manually or load from library</p>
            </div>
          </div>
          <button
            onClick={handleRunBacktest}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 disabled:opacity-60 transition shadow-sm cursor-pointer"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Run Backtest
          </button>
        </div>

        {/* Entry (Buy) Rules */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
              Entry Conditions (Buy)
            </span>
            <button
              onClick={() => addCondition('entry')}
              className="text-[10px] text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 cursor-pointer"
            >
              <Plus size={12} /> Add Rule
            </button>
          </div>
          <div className="space-y-1.5 max-h-[170px] overflow-y-auto pr-1">
            {entryConditions.map((c, i) => renderConditionRow(c, i, 'entry'))}
          </div>
        </div>

        {/* Exit (Sell) Rules */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
              Exit Conditions (Sell)
            </span>
            <button
              onClick={() => addCondition('exit')}
              className="text-[10px] text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 cursor-pointer"
            >
              <Plus size={12} /> Add Rule
            </button>
          </div>
          <div className="space-y-1.5 max-h-[170px] overflow-y-auto pr-1">
            {exitConditions.map((c, i) => renderConditionRow(c, i, 'exit'))}
          </div>
        </div>

        {/* Parameters Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-950/40 p-4 border border-slate-800/80 rounded-lg">
          <div className="relative">
            <label className="text-[9px] font-semibold text-slate-500 uppercase">Symbol</label>
            <input
              type="text"
              value={symbolSearch}
              onFocus={() => setShowSymbolDropdown(true)}
              onChange={(e) => {
                setSymbolSearch(e.target.value);
                setShowSymbolDropdown(true);
                const cleanInput = e.target.value.split(' - ')[0].trim().toUpperCase();
                if (cleanInput) {
                  setSymbol(cleanInput);
                }
              }}
              placeholder="Search Indian stocks..."
              className="w-full mt-1 bg-slate-900 border border-slate-700/80 rounded px-2.5 py-1 text-xs text-slate-200 focus:outline-none"
            />
            {showSymbolDropdown && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowSymbolDropdown(false)} />
                <div className="absolute left-0 right-0 mt-1 bg-slate-900 border border-slate-800 rounded-md max-h-48 overflow-y-auto z-20 shadow-2xl divide-y divide-slate-800/60 scrollbar-thin scrollbar-thumb-slate-800">
                  {companies
                    .filter(c => 
                      c.symbol.toLowerCase().includes(symbolSearch.split(' - ')[0].toLowerCase()) ||
                      c.name.toLowerCase().includes(symbolSearch.toLowerCase())
                    )
                    .slice(0, 55)
                    .map(c => (
                      <div
                        key={c.symbol}
                        onClick={() => {
                          setSymbol(c.symbol);
                          setSymbolSearch(`${c.symbol} - ${c.name}`);
                          setShowSymbolDropdown(false);
                        }}
                        className="p-2 text-[10px] hover:bg-blue-600/30 hover:text-white cursor-pointer transition text-slate-300 flex justify-between"
                      >
                        <div>
                          <span className="font-bold font-mono text-blue-400">{c.symbol}</span>
                          <span className="ml-2 text-slate-400 font-sans">{c.name}</span>
                        </div>
                        <span className="text-[8px] text-slate-500 font-mono mt-0.5">{c.sector}</span>
                      </div>
                    ))}
                  {companies.length > 0 && companies.filter(c => 
                    c.symbol.toLowerCase().includes(symbolSearch.split(' - ')[0].toLowerCase()) ||
                    c.name.toLowerCase().includes(symbolSearch.toLowerCase())
                  ).length === 0 && (
                    <div className="p-3 text-[10px] text-slate-500 text-center">
                      No matching tickers found
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
          
          <div>
            <label className="text-[9px] font-semibold text-slate-500 uppercase">Lookback</label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="w-full mt-1 bg-slate-900 border border-slate-700/80 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none"
            >
              <option value="1y">1 Year</option>
              <option value="2y">2 Years</option>
              <option value="5y">5 Years</option>
              <option value="8y">8 Years</option>
            </select>
          </div>

          <div>
            <label className="text-[9px] font-semibold text-slate-500 uppercase">Fees %</label>
            <input
              type="number"
              step="0.0001"
              value={fees}
              onChange={(e) => setFees(Number(e.target.value))}
              className="w-full mt-1 bg-slate-900 border border-slate-700/80 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none"
            />
          </div>

          <div>
            <label className="text-[9px] font-semibold text-slate-500 uppercase">Slippage %</label>
            <input
              type="number"
              step="0.0001"
              value={slippage}
              onChange={(e) => setSlippage(Number(e.target.value))}
              className="w-full mt-1 bg-slate-900 border border-slate-700/80 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none"
            />
          </div>
        </div>
      </div>
    );
  }
);

StrategyBuilder.displayName = 'StrategyBuilder';
