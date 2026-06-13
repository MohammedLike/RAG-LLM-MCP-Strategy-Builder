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

export interface Trade {
  id: number;
  entry_date: string;
  exit_date: string;
  direction: string;
  entry_price: number;
  exit_price: number;
  pnl: number;
  pnl_pct: number;
  size: number;
  duration_days: number;
  exit_reason?: string;
}

export interface EquityPoint {
  date: string;
  value: number;
}

export interface BacktestResult {
  symbol: string;
  period: string;
  strategy_spec: any;
  timestamp?: string;
  label?: string;
  total_return: number;
  benchmark_return: number;
  cagr: number;
  calmar: number;
  sharpe: number;
  sortino: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  expectancy: number;
  instrument_type?: string;
  strike?: number;
  option_type?: string;
  equity_curve: EquityPoint[];
  drawdown: EquityPoint[];
  trades: Trade[];
  ohlcv?: { time: string; open: number; high: number; low: number; close: number; volume?: number }[];
  monthly_returns?: Record<string, (number | null)[]>;
  backtest_id?: string;
}

export interface Indicator {
  name: string;
  long_name: string;
  category: string;
  params: Record<string, any>;
  description: string;
  inputs: string[];
}

export interface Condition {
  id: string;
  indicator: string;
  params: Record<string, any>;
  operator: string;
  valueType: 'value' | 'indicator';
  value: number;
  compareIndicator: string;
  compareParams: Record<string, any>;
}
