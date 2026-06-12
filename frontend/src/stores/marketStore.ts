import { create } from 'zustand';
import type { Quote } from '../types';
import { fetchQuote } from '../services/api';

interface MarketState {
  niftyQuote: Quote | null;
  bankNiftyQuote: Quote | null;
  setQuote: (quote: Quote) => void;
  fetchQuotes: () => Promise<void>;
}

export const useMarketStore = create<MarketState>((set) => ({
  niftyQuote: null,
  bankNiftyQuote: null,

  setQuote: (quote: Quote) => {
    if (quote.symbol === 'NIFTY' || quote.symbol === '^NSEI') {
      set({ niftyQuote: quote });
    } else if (quote.symbol === 'BANKNIFTY' || quote.symbol === '^NSEBANK') {
      set({ bankNiftyQuote: quote });
    }
  },

  fetchQuotes: async () => {
    try {
      const nifty = await fetchQuote('NIFTY');
      if (nifty && !nifty.error) set({ niftyQuote: nifty });
      const bank = await fetchQuote('BANKNIFTY');
      if (bank && !bank.error) set({ bankNiftyQuote: bank });
    } catch {}
  },
}));
