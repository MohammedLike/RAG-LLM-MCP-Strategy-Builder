import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE,
});

export const fetchQuote = async (symbol: string) => {
  const res = await api.get(`/market/${symbol}/quote`);
  return res.data;
};
