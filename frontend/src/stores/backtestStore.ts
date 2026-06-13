import { create } from 'zustand';
import {
  runBacktest as apiRunBacktest,
  fetchBacktestHistory,
  fetchBacktestById,
  api,
} from '../services/api';
import type { BacktestResult, Indicator } from '../types';

interface BacktestState {
  latestBacktest: BacktestResult | null;
  pinnedRuns: BacktestResult[];
  history: any[];
  indicators: Record<string, Indicator>;
  loading: boolean;
  error: string | null;
  runBacktest: (symbol: string, strategySpec: any, period: string) => Promise<void>;
  fetchLatestBacktest: () => Promise<void>;
  fetchIndicators: () => Promise<void>;
  fetchHistory: (limit?: number, symbol?: string) => Promise<void>;
  loadBacktestById: (id: string) => Promise<void>;
  pinCurrentRun: (label?: string) => void;
  removePinnedRun: (index: number) => void;
  clearPinnedRuns: () => void;
  clearLatestBacktest: () => void;
}

export const useBacktestStore = create<BacktestState>((set, get) => ({
  latestBacktest: null,
  pinnedRuns: [],
  history: [],
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
      const message = err.response?.data?.error
        || err.response?.data?.detail
        || (err.code === 'ERR_NETWORK' ? 'Cannot reach backend API. Make sure the backend is running on port 8001.' : null)
        || err.message
        || 'Failed to run backtest';
      set({ error: message, loading: false });
    }
  },

  fetchLatestBacktest: async () => {
    try {
      const res = await api.get('/backtest/latest');
      if (res.data) {
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

  fetchHistory: async (limit = 50, symbol?: string) => {
    try {
      const data = await fetchBacktestHistory(limit, symbol);
      set({ history: data.history || [] });
    } catch (err) {
      console.error('Error fetching backtest history', err);
    }
  },

  loadBacktestById: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const result = await fetchBacktestById(id);
      if (result.error) {
        set({ error: result.error, loading: false });
      } else {
        set({ latestBacktest: result, loading: false });
      }
    } catch (err: any) {
      set({ error: err.message || 'Failed to load backtest', loading: false });
    }
  },

  pinCurrentRun: (label?: string) => {
    const current = get().latestBacktest;
    if (!current) return;
    const pinned = [...get().pinnedRuns];
    if (pinned.length >= 5) pinned.shift();
    pinned.push({ ...current, label: label || `${current.symbol} ${current.period}` });
    set({ pinnedRuns: pinned });
  },

  removePinnedRun: (index: number) => {
    const pinned = [...get().pinnedRuns];
    pinned.splice(index, 1);
    set({ pinnedRuns: pinned });
  },

  clearPinnedRuns: () => set({ pinnedRuns: [] }),

  clearLatestBacktest: () => set({ latestBacktest: null }),
}));
