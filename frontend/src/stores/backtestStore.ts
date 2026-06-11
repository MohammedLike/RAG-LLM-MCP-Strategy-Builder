import { create } from 'zustand';
import { runBacktest as apiRunBacktest, api } from '../services/api';

interface Indicator {
  name: string;
  long_name: string;
  category: string;
  params: Record<string, any>;
  description: string;
  inputs: string[];
}

interface Trade {
  id: number;
  entry_date: string;
  exit_date: string;
  direction: string;
  entry_price: number;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
  size: number;
  duration_days: number;
}

interface EquityPoint {
  date: string;
  value: number;
}

interface BacktestResult {
  symbol: string;
  period: string;
  strategy_spec: any;
  timestamp?: string;
  total_return: number;
  benchmark_return: number;
  sharpe: number;
  sortino: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  expectancy: number;
  equity_curve: EquityPoint[];
  drawdown: EquityPoint[];
  trades: Trade[];
}

interface BacktestState {
  latestBacktest: BacktestResult | null;
  indicators: Record<string, Indicator>;
  loading: boolean;
  error: string | null;
  runBacktest: (symbol: string, strategySpec: any, period: string) => Promise<void>;
  fetchLatestBacktest: () => Promise<void>;
  fetchIndicators: () => Promise<void>;
  clearLatestBacktest: () => void;
}

export const useBacktestStore = create<BacktestState>((set) => ({
  latestBacktest: null,
  indicators: {},
  loading: false,
  error: null,

  runBacktest: async (symbol, strategySpec, period) => {
    set({ loading: true, error: null });
    try {
      const result = await apiRunBacktest(symbol, strategySpec, period);
      if (result.error) {
        set({ error: result.error, loading: false });
      } else {
        set({ latestBacktest: result, loading: false });
      }
    } catch (err: any) {
      set({ error: err.message || 'Failed to run backtest', loading: false });
    }
  },

  fetchLatestBacktest: async () => {
    try {
      const res = await api.get('/backtest/latest');
      if (res.data && res.data.symbol) {
        set({ latestBacktest: res.data });
      }
    } catch (err) {
      console.error('Error fetching latest backtest', err);
    }
  },

  fetchIndicators: async () => {
    try {
      const res = await api.get('/indicators');
      if (res.data) {
        set({ indicators: res.data });
      }
    } catch (err) {
      console.error('Error fetching indicators list', err);
    }
  },

  clearLatestBacktest: () => set({ latestBacktest: null })
}));
