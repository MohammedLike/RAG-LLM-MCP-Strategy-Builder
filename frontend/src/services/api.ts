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

export const fetchMcpTools = async () => {
  const res = await api.get('/mcp/tools');
  return res.data;
};

export const executeMcpTool = async (toolName: string, argumentsData: object) => {
  const res = await api.post('/mcp/execute', { tool_name: toolName, arguments: argumentsData });
  return res.data;
};
