import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE,
});

export const fetchQuote = async (symbol: string) => {
  const res = await api.get(`/market/${symbol}/quote`);
  return res.data;
};

export const sendChatMessage = async (message: string, sessionId: string) => {
  const res = await api.post('/chat', { message, session_id: sessionId });
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
