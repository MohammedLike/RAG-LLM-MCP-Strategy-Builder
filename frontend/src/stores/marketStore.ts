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
    if (quote.symbol === 'NIFTY') return { niftyQuote: quote }
    if (quote.symbol === 'BANKNIFTY') return { bankNiftyQuote: quote }
    return state
  })
}))
