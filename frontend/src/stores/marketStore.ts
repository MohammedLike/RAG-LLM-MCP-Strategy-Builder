import { create } from 'zustand'
import type { Quote } from '../types'

interface MarketState {
  niftyQuote: Quote | null;
  bankNiftyQuote: Quote | null;
  setQuote: (quote: Quote) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  niftyQuote: null,
  bankNiftyQuote: null,
  setQuote: (quote) => set((state) => {
    const normalized: Quote = {
      symbol: quote.symbol,
      ltp: quote.ltp ?? 0,
      change: quote.change ?? 0,
    };
    if (normalized.symbol === 'NIFTY') return { niftyQuote: normalized };
    if (normalized.symbol === 'BANKNIFTY') return { bankNiftyQuote: normalized };
    return state;
  }),
}))
