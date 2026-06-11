import { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Play, BarChart3, Loader2, List, Settings2 } from 'lucide-react';
import { runBacktest } from '../../services/api';

const defaultMetrics = [
  { label: 'Total Return', value: '—', key: 'total_return', suffix: '%' },
  { label: 'Sharpe', value: '—', key: 'sharpe' },
  { label: 'Max DD', value: '—', key: 'max_drawdown', suffix: '%' },
  { label: 'Win Rate', value: '—', key: 'win_rate', suffix: '%' },
  { label: 'Profit Factor', value: '—', key: 'profit_factor' },
  { label: 'Expectancy', value: '—', key: 'expectancy' },
];

export const BacktestPanel = () => {
  const [symbol, setSymbol] = useState('NIFTY');
  const [period, setPeriod] = useState('1y');
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(defaultMetrics);
  const [chartData, setChartData] = useState<{ date: string; equity: number }[]>([]);
  const [trades, setTrades] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Strategy Builder State
  const [entryIndicator, setEntryIndicator] = useState('RSI');
  const [entryOp, setEntryOp] = useState('<');
  const [entryValue, setEntryValue] = useState(30);
  
  const [exitIndicator, setExitIndicator] = useState('RSI');
  const [exitOp, setExitOp] = useState('>');
  const [exitValue, setExitValue] = useState(70);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const strategy_spec = {
        entry: { indicator: entryIndicator, operator: entryOp, value: entryValue },
        exit: { indicator: exitIndicator, operator: exitOp, value: exitValue },
        fees: 0.001,
        slippage: 0.001
      };
      
      const result = await runBacktest(symbol, strategy_spec, period);
      
      if (result.error) throw new Error(result.error);

      setMetrics(defaultMetrics.map(m => ({
        ...m,
        value: result[m.key] ? result[m.key].toFixed(2) + (m.suffix || '') : '—'
      })));
      
      if (result.equity_curve) {
        setChartData(result.equity_curve.map((p: any) => ({
          date: p.date.split(' ')[0],
          equity: p.value,
        })));
      }
      
      if (result.trades) {
        setTrades(result.trades);
      }
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 flex flex-col h-full gap-6 overflow-y-auto bg-[#f8fafc]">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Quant Backtest Engine</h2>
          <p className="text-sm text-slate-500 mt-0.5">High-performance vectorized backtesting for NSE/BSE</p>
        </div>
        <button
          onClick={handleRun}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 disabled:opacity-60 transition-all shadow-sm"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
          Run Backtest
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">{error}</div>
      )}

      {/* Strategy Builder */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Settings2 size={18} className="text-blue-600" />
            <h3 className="font-bold text-slate-900">Strategy Rules</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <div className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">Entry Condition (Buy)</div>
              <div className="flex items-center gap-2">
                <select value={entryIndicator} onChange={e => setEntryIndicator(e.target.value)} className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm">
                  <option value="RSI">RSI</option>
                  <option value="SMA">SMA</option>
                  <option value="EMA">EMA</option>
                  <option value="MACD">MACD</option>
                  <option value="ADX">ADX</option>
                </select>
                <select value={entryOp} onChange={e => setEntryOp(e.target.value)} className="w-16 bg-slate-50 border border-slate-200 rounded-lg px-2 py-2 text-sm text-center">
                  <option value="<">{'<'}</option>
                  <option value=">">{'>'}</option>
                  <option value="==">{'='}</option>
                </select>
                <input type="number" value={entryValue} onChange={e => setEntryValue(Number(e.target.value))} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>

            <div className="space-y-4">
              <div className="text-[10px] font-bold text-red-600 uppercase tracking-wider">Exit Condition (Sell)</div>
              <div className="flex items-center gap-2">
                <select value={exitIndicator} onChange={e => setExitIndicator(e.target.value)} className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm">
                  <option value="RSI">RSI</option>
                  <option value="SMA">SMA</option>
                  <option value="EMA">EMA</option>
                  <option value="MACD">MACD</option>
                  <option value="ADX">ADX</option>
                </select>
                <select value={exitOp} onChange={e => setExitOp(e.target.value)} className="w-16 bg-slate-50 border border-slate-200 rounded-lg px-2 py-2 text-sm text-center">
                  <option value=">">{'>'}</option>
                  <option value="<">{'<'}</option>
                  <option value="==">{'='}</option>
                </select>
                <input type="number" value={exitValue} onChange={e => setExitValue(Number(e.target.value))} className="w-20 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Settings2 size={18} className="text-blue-600" />
            <h3 className="font-bold text-slate-900">Parameters</h3>
          </div>
          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-semibold text-slate-500 uppercase">Symbol</label>
              <select value={symbol} onChange={e => setSymbol(e.target.value)} className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm">
                <option value="NIFTY">NIFTY 50</option>
                <option value="BANKNIFTY">BANKNIFTY</option>
                <option value="RELIANCE">RELIANCE</option>
                <option value="TCS">TCS</option>
                <option value="HDFCBANK">HDFC BANK</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] font-semibold text-slate-500 uppercase">Lookback Period</label>
              <select value={period} onChange={e => setPeriod(e.target.value)} className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm">
                <option value="1y">Past 1 Year</option>
                <option value="2y">Past 2 Years</option>
                <option value="5y">Past 5 Years</option>
                <option value="8y">Past 8 Years</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {metrics.map((m) => (
          <div key={m.label} className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 text-center">
            <div className="text-[10px] font-semibold text-slate-500 uppercase mb-1">{m.label}</div>
            <div className="text-xl font-bold text-slate-900">{m.value}</div>
          </div>
        ))}
      </div>

      {/* Chart Section */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 min-h-[400px]">
        <div className="flex items-center gap-2 mb-6">
          <BarChart3 size={18} className="text-blue-600" />
          <h3 className="font-bold text-slate-900">Equity Curve</h3>
        </div>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#94a3b8" axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10 }} stroke="#94a3b8" axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ borderRadius: 12, border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
              <Area type="monotone" dataKey="equity" stroke="#2563eb" fill="url(#colorEquity)" strokeWidth={2.5} />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[320px] flex items-center justify-center text-slate-400 text-sm">
            Configure strategy and run backtest to visualize performance
          </div>
        )}
      </div>

      {/* Trade Log */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div className="flex items-center gap-2 mb-4">
          <List size={18} className="text-blue-600" />
          <h3 className="font-bold text-slate-900">Trade Log</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 text-slate-500 uppercase text-[10px] font-bold">
              <tr>
                <th className="px-4 py-3">Entry Date</th>
                <th className="px-4 py-3">Exit Date</th>
                <th className="px-4 py-3">Entry Price</th>
                <th className="px-4 py-3">Exit Price</th>
                <th className="px-4 py-3">P&L %</th>
                <th className="px-4 py-3">Return</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {trades.length > 0 ? trades.map((t, i) => (
                <tr key={i} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 text-slate-600">{t['Entry Timestamp']?.split(' ')[0]}</td>
                  <td className="px-4 py-3 text-slate-600">{t['Exit Timestamp']?.split(' ')[0]}</td>
                  <td className="px-4 py-3 font-medium">{t['Entry Price']?.toFixed(2)}</td>
                  <td className="px-4 py-3 font-medium">{t['Exit Price']?.toFixed(2)}</td>
                  <td className={`px-4 py-3 font-bold ${t['PnL [%]'] >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {t['PnL [%]']?.toFixed(2)}%
                  </td>
                  <td className={`px-4 py-3 font-bold ${t['Return [%]'] >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {t['Return [%]']?.toFixed(2)}%
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">No trades executed in this backtest</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
