export interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: number;
}

export interface Quote {
  symbol: string;
  ltp: number;
  change: number;
  iv?: number;
}
