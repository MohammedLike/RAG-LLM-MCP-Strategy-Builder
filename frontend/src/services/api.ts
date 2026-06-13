import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : 'http://localhost:8001/api';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000,
});

export const fetchQuote = async (symbol: string) => {
  const res = await api.get(`/market/${symbol}/quote`);
  return res.data;
};

export const fetchCompanies = async () => {
  const res = await api.get('/market/companies');
  return res.data;
};

export const sendChatMessage = async (message: string, sessionId: string) => {
  const res = await api.post('/chat', { message, session_id: sessionId });
  return res.data;
};

export const fetchStrategies = async () => {
  const res = await api.get('/strategies');
  return res.data;
};

export const runBacktest = async (symbol: string, strategy_spec: object, period = '1y') => {
  const res = await api.post('/backtest', {
    strategy_spec,
    symbol,
    period,
  });
  return res.data;
};

export const runBacktestAsync = async (requests: any[]) => {
  const res = await api.post('/backtest/async', requests);
  return res.data;
};

export const pollBacktestResult = async (taskId: string) => {
  const res = await api.get(`/backtest/async/${taskId}`);
  return res.data;
};

export const fetchBacktestHistory = async (limit = 50, symbol?: string) => {
  const params: Record<string, string | number> = { limit };
  if (symbol) params.symbol = symbol;
  const res = await api.get('/backtest/history', { params });
  return res.data;
};

export const fetchBacktestById = async (id: string) => {
  const res = await api.get(`/backtest/${id}`);
  return res.data;
};

export const optimizeBacktest = async (
  symbol: string,
  strategy_spec: object,
  period: string,
  param_grid?: Record<string, number[]>
) => {
  const res = await api.post('/backtest/optimize', {
    symbol,
    strategy_spec,
    period,
    param_grid,
  });
  return res.data;
};

export const compareBacktests = async (runs: object[]) => {
  const res = await api.post('/backtest/compare', { runs });
  return res.data;
};

export const runMonteCarlo = async (trades: object[], n_simulations = 1000) => {
  const res = await api.post('/backtest/monte-carlo', { trades, n_simulations });
  return res.data;
};

export const runWalkForward = async (
  symbol: string,
  strategy_spec: object,
  period: string,
  n_splits = 5
) => {
  const res = await api.post('/backtest/walk-forward', {
    symbol,
    strategy_spec,
    period,
    n_splits,
  });
  return res.data;
};

export const fetchOptionsPayoff = async (symbol: string, strategy_spec: object) => {
  const res = await api.post('/backtest/payoff', { symbol, strategy_spec });
  return res.data;
};

export const exportBacktest = async (format: string, result: object) => {
  const res = await api.post('/pipeline/export', { format, result }, { responseType: 'blob' });
  return res.data;
};

export const fetchMcpTools = async () => {
  const res = await api.get('/mcp/tools');
  return res.data;
};

export const executeMcpTool = async (toolName: string, argumentsData: object) => {
  const res = await api.post('/mcp/execute', { tool_name: toolName, arguments: argumentsData });
  return res.data;
};
