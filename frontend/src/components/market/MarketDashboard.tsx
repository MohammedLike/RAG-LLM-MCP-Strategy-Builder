import { useEffect } from 'react';
import { useMarketStore } from '../../stores/marketStore';
import { fetchQuote } from '../../services/api';

export const MarketDashboard = () => {
  const { niftyQuote, bankNiftyQuote, setQuote } = useMarketStore();

  useEffect(() => {
    // Initial fetch mock
    fetchQuote('NIFTY').then(setQuote).catch(console.error);
    fetchQuote('BANKNIFTY').then(setQuote).catch(console.error);
  }, []);

  return (
    <div className="p-6 grid grid-cols-2 gap-4">
      <div className="bg-slate-800 p-4 rounded-xl shadow-lg border border-slate-700">
        <h3 className="text-slate-400 font-semibold mb-2">NIFTY 50</h3>
        <div className="text-3xl font-bold">{niftyQuote?.ltp || '---'}</div>
        <div className="text-accent-green">+{niftyQuote?.change || '---'}</div>
      </div>
      <div className="bg-slate-800 p-4 rounded-xl shadow-lg border border-slate-700">
        <h3 className="text-slate-400 font-semibold mb-2">BANKNIFTY</h3>
        <div className="text-3xl font-bold">{bankNiftyQuote?.ltp || '---'}</div>
        <div className="text-accent-green">+{bankNiftyQuote?.change || '---'}</div>
      </div>
    </div>
  );
};
