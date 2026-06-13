import { useEffect, useRef } from 'react';
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type LineData,
  type HistogramData,
  type SeriesMarker,
  ColorType,
  CrosshairMode,
} from 'lightweight-charts';

export type OhlcvBar = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
};

export type LinePoint = {
  time: string;
  value: number;
};

type ChartKind = 'candlestick' | 'area' | 'histogram';

type TradingViewChartProps = {
  kind: ChartKind;
  candles?: OhlcvBar[];
  lineData?: LinePoint[];
  markers?: SeriesMarker<string>[];
  height?: number;
  className?: string;
};

function getTheme() {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  return {
    isLight,
    layout: {
      background: { type: ColorType.Solid, color: isLight ? '#ffffff' : '#0d0d0d' },
      textColor: isLight ? '#475569' : '#a3a3a3',
      fontFamily: 'Roboto, system-ui, sans-serif',
    },
    grid: {
      vertLines: { color: isLight ? 'rgba(15, 23, 42, 0.06)' : 'rgba(255, 255, 255, 0.05)' },
      horzLines: { color: isLight ? 'rgba(15, 23, 42, 0.06)' : 'rgba(255, 255, 255, 0.05)' },
    },
    crosshair: { mode: CrosshairMode.Normal },
  };
}

function toTime(value: string): string {
  return String(value).slice(0, 10);
}

export function TradingViewChart({
  kind,
  candles = [],
  lineData = [],
  markers = [],
  height = 280,
  className = '',
}: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    chartRef.current?.remove();
    chartRef.current = null;

    const theme = getTheme();
    const chart = createChart(container, {
      ...theme,
      width: container.clientWidth,
      height,
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false, timeVisible: true, secondsVisible: false },
    });

    if (kind === 'candlestick') {
      const series = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });
      const data: CandlestickData[] = candles.map((b) => ({
        time: toTime(b.time),
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      }));
      series.setData(data);
      if (markers.length) {
        series.setMarkers(markers);
      }
    } else if (kind === 'histogram') {
      const series = chart.addHistogramSeries({
        color: '#ef4444',
        priceFormat: { type: 'percent', precision: 2, minMove: 0.01 },
      });
      const data: HistogramData[] = lineData.map((p) => ({
        time: toTime(p.time),
        value: p.value,
        color: p.value <= 0 ? 'rgba(239, 68, 68, 0.55)' : 'rgba(34, 197, 94, 0.55)',
      }));
      series.setData(data);
    } else {
      const series = chart.addAreaSeries({
        lineColor: '#2962FF',
        topColor: 'rgba(41, 98, 255, 0.35)',
        bottomColor: 'rgba(41, 98, 255, 0.02)',
        lineWidth: 2,
      });
      const data: LineData[] = lineData.map((p) => ({
        time: toTime(p.time),
        value: p.value,
      }));
      series.setData(data);
    }

    chart.timeScale().fitContent();
    chartRef.current = chart;

    const ro = new ResizeObserver(() => {
      if (container && chartRef.current) {
        chartRef.current.applyOptions({ width: container.clientWidth });
      }
    });
    ro.observe(container);

    const onThemeChange = () => {
      chart.applyOptions(getTheme());
    };
    window.addEventListener('strykex-theme-change', onThemeChange);

    return () => {
      ro.disconnect();
      window.removeEventListener('strykex-theme-change', onThemeChange);
      chart.remove();
      chartRef.current = null;
    };
  }, [kind, candles, lineData, markers, height]);

  return <div ref={containerRef} className={`w-full ${className}`} style={{ height }} />;
}

export function buildTradeMarkers(trades: Array<{ entry_date?: string; exit_date?: string }>): SeriesMarker<string>[] {
  const markers: SeriesMarker<string>[] = [];
  for (const trade of trades) {
    if (trade.entry_date) {
      markers.push({
        time: toTime(trade.entry_date),
        position: 'belowBar',
        color: '#22c55e',
        shape: 'arrowUp',
        text: 'Entry',
      });
    }
    if (trade.exit_date) {
      markers.push({
        time: toTime(trade.exit_date),
        position: 'aboveBar',
        color: '#ef4444',
        shape: 'arrowDown',
        text: 'Exit',
      });
    }
  }
  return markers.sort((a, b) => String(a.time).localeCompare(String(b.time)));
}

export function toLineSeries(points: Array<{ date?: string; value?: number }>): LinePoint[] {
  return (points || [])
    .filter((p) => p.date && p.value !== undefined && p.value !== null)
    .map((p) => ({ time: String(p.date).slice(0, 10), value: Number(p.value) }));
}

export function toOhlcvSeries(bars: OhlcvBar[]): OhlcvBar[] {
  return (bars || []).map((b) => ({
    time: String(b.time).slice(0, 10),
    open: Number(b.open),
    high: Number(b.high),
    low: Number(b.low),
    close: Number(b.close),
    volume: Number(b.volume || 0),
  }));
}
