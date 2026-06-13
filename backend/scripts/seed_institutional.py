import uuid
import json
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import sys
import os

# Add the 'app' directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import settings

strategies = [
    {
        'name': 'RSI Oversold + EMA Uptrend',
        'slug': 'rsi-oversold-ema-uptrend',
        'category': 'Mean Reversion',
        'hypothesis': 'Buy RSI pullbacks (<30) while the long-term trend (EMA50 > EMA200) remains bullish.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 30},
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 60}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 7.0, 'take_profit': 10.0}
    },
    {
        'name': 'CCI Oversold + EMA Uptrend',
        'slug': 'cci-oversold-ema-uptrend-v2',
        'category': 'Mean Reversion',
        'hypothesis': 'Buy deep CCI oversold conditions (<-100) in a bullish trend confirmed by EMA and RSI.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'CCI', 'params': {'timeperiod': 20}, 'operator': '<', 'value': -100},
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
                {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 35}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'CCI', 'params': {'timeperiod': 20}, 'operator': '>', 'value': 0}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 7.0, 'take_profit': 10.0}
    },
    {
        'name': 'Bollinger Lower Band Touch + RSI Uptrend',
        'slug': 'bb-lower-rsi-uptrend',
        'category': 'Mean Reversion',
        'hypothesis': 'Buy lower Bollinger Band touches in an uptrend with RSI confirmation.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'CLOSE', 'params': {}, 'operator': '<=', 'value': {'indicator': 'BBANDS', 'params': {'timeperiod': 20, 'nbdevup': 2, 'output_index': 'lower'}}},
                {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 42},
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'CLOSE', 'params': {}, 'operator': '>=', 'value': {'indicator': 'BBANDS', 'params': {'timeperiod': 20, 'nbdevup': 2, 'output_index': 'middle'}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 7.0, 'take_profit': 10.0}
    },
    {
        'name': 'MFI Wide Oversold + EMA Uptrend',
        'slug': 'mfi-wide-oversold-ema-uptrend-v2',
        'category': 'Volume-Based',
        'hypothesis': 'Buy when money flow (MFI) becomes oversold (<35) in a bullish trend.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'MFI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 35},
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
                {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'MFI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 65}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 7.0, 'take_profit': 10.0}
    },
    {
        'name': 'Williams %R Deep Oversold + Uptrend',
        'slug': 'williams-r-oversold-uptrend',
        'category': 'Momentum',
        'hypothesis': 'Buy deeply oversold Williams %R readings (<-80) in a strong trend (ADX > 18).',
        'entry_rules': {
            'conditions': [
                {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '<', 'value': -80},
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
                {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 18}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '>', 'value': -20}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 7.0, 'take_profit': 10.0}
    },
    {
        'name': 'RSI Pullback + EMA Uptrend',
        'slug': 'rsi-pullback-ema-uptrend-v2',
        'category': 'Trend Following',
        'hypothesis': 'Buy moderate RSI pullbacks (<40) in a clear uptrend (EMA21 > EMA50).',
        'entry_rules': {
            'conditions': [
                {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 40},
                {'indicator': 'EMA', 'params': {'timeperiod': 21}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}},
                {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 60}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 2.0, 'take_profit': 3.0}
    },
    {
        'name': 'Stochastic Oversold + EMA Uptrend',
        'slug': 'stochastic-oversold-ema-uptrend-v2',
        'category': 'Mean Reversion',
        'hypothesis': 'Buy stochastic oversold reversals (%K < 25 and %K > %D) in an uptrend.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'STOCH', 'params': {'fastk_period': 14, 'slowd_period': 3, 'output_index': 'slowk'}, 'operator': '<', 'value': 25},
                {'indicator': 'STOCH', 'params': {'fastk_period': 14, 'slowd_period': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': {'indicator': 'STOCH', 'params': {'fastk_period': 14, 'slowd_period': 3, 'output_index': 'slowd'}}},
                {'indicator': 'EMA', 'params': {'timeperiod': 21}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'STOCH', 'params': {'fastk_period': 14, 'slowd_period': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': 75}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 2.0, 'take_profit': 3.0}
    },
    {
        'name': 'Stochastic Oversold Pullback in Uptrend',
        'slug': 'stochastic-pullback-uptrend',
        'category': 'Pullback',
        'hypothesis': 'Buy oversold stochastic pullbacks inside a strong long-term uptrend.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'STOCH', 'params': {'fastk_period': 14, 'slowd_period': 3, 'output_index': 'slowk'}, 'operator': '<', 'value': 25},
                {'indicator': 'STOCH', 'params': {'fastk_period': 14, 'slowd_period': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': {'indicator': 'STOCH', 'params': {'fastk_period': 14, 'slowd_period': 3, 'output_index': 'slowd'}}},
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
                {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'STOCH', 'params': {'fastk_period': 14, 'slowd_period': 3, 'output_index': 'slowk'}, 'operator': '>', 'value': 75}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 7.0, 'take_profit': 10.0}
    },
    {
        'name': 'Williams %R Oversold + RSI + ADX',
        'slug': 'williams-rsi-adx-combo',
        'category': 'Momentum',
        'hypothesis': 'Multi-indicator oversold strategy using Williams %R, RSI, and ADX filters.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '<', 'value': -70},
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}},
                {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 20},
                {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 35}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '>', 'value': -20}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 7.0, 'take_profit': 10.0}
    },
    {
        'name': 'SuperTrend + Ichimoku Span B Filter',
        'slug': 'supertrend-ichimoku-v2',
        'category': 'Trend Following',
        'hypothesis': 'Trend-following breakout strategy using SuperTrend and Ichimoku Cloud filters.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'SAR', 'params': {}}}, # Using SAR as proxy for SuperTrend
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'CLOSE', 'params': {}, 'operator': '<', 'value': {'indicator': 'SAR', 'params': {}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 7.0, 'take_profit': 10.0}
    },
    {
        'name': 'CCI + Williams %R Mean Reversion',
        'slug': 'cci-williams-mean-reversion-v2',
        'category': 'Mean Reversion',
        'hypothesis': 'Dual oversold oscillator strategy using CCI and Williams %R.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'CCI', 'params': {'timeperiod': 20}, 'operator': '<', 'value': -100},
                {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '<', 'value': -75},
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [
                {'indicator': 'CCI', 'params': {'timeperiod': 20}, 'operator': '>', 'value': 0},
                {'indicator': 'WILLR', 'params': {'timeperiod': 14}, 'operator': '>', 'value': -25}
            ],
            'logical_operator': 'OR'
        },
        'risk_params': {'stop_loss': 7.0, 'take_profit': 10.0}
    },
    {
        'name': 'EMA Golden Cross Strategy',
        'slug': 'ema-golden-cross',
        'category': 'Trend Following',
        'hypothesis': 'Classic moving average crossover system (EMA50/200).',
        'entry_rules': {
            'conditions': [{'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': 'crosses_above', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': 'crosses_below', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 5.0, 'take_profit': 15.0}
    },
    {
        'name': 'EMA Pullback Strategy',
        'slug': 'ema-pullback',
        'category': 'Pullback',
        'hypothesis': 'Buy price pullbacks to the EMA while the long-term trend remains bullish.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'CLOSE', 'params': {}, 'operator': '<=', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 20}}},
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 20}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 3.0, 'take_profit': 10.0}
    },
    {
        'name': 'MACD Bullish Crossover',
        'slug': 'macd-bull-cross',
        'category': 'Momentum',
        'hypothesis': 'Classic momentum strategy using MACD/Signal crossover.',
        'entry_rules': {
            'conditions': [{'indicator': 'MACD', 'params': {}, 'operator': 'crosses_above', 'value': {'indicator': 'MACD', 'params': {'output_index': 'signal'}}}],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'MACD', 'params': {}, 'operator': 'crosses_below', 'value': {'indicator': 'MACD', 'params': {'output_index': 'signal'}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 3.0, 'take_profit': 8.0}
    },
    {
        'name': 'MACD + RSI Confirmation',
        'slug': 'macd-rsi-confirm',
        'category': 'Momentum',
        'hypothesis': 'MACD bullish crossover with RSI filter to avoid overbought entries.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'MACD', 'params': {}, 'operator': 'crosses_above', 'value': {'indicator': 'MACD', 'params': {'output_index': 'signal'}}},
                {'indicator': 'RSI', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 60}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'MACD', 'params': {}, 'operator': 'crosses_below', 'value': {'indicator': 'MACD', 'params': {'output_index': 'signal'}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 4.0, 'take_profit': 12.0}
    },
    {
        'name': 'ADX Trend Strength Strategy',
        'slug': 'adx-trend-strength',
        'category': 'Trend Strength',
        'hypothesis': 'Only enters trades when ADX confirms a strong trend (>25).',
        'entry_rules': {
            'conditions': [
                {'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '>', 'value': 25},
                {'indicator': 'PLUS_DI', 'params': {'timeperiod': 14}, 'operator': '>', 'value': {'indicator': 'MINUS_DI', 'params': {'timeperiod': 14}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'ADX', 'params': {'timeperiod': 14}, 'operator': '<', 'value': 20}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 5.0, 'take_profit': 15.0}
    },
    {
        'name': 'Breakout Above Resistance',
        'slug': 'resistance-breakout',
        'category': 'Breakout',
        'hypothesis': 'Price breakout strategy above recent highs with volume confirmation.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'HIGH', 'params': {'timeperiod': 20}}},
                {'indicator': 'VOLUME', 'params': {}, 'operator': '>', 'value': {'indicator': 'SMA', 'params': {'indicator': 'VOLUME', 'timeperiod': 20}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'CLOSE', 'params': {}, 'operator': '<', 'value': {'indicator': 'LOW', 'params': {'timeperiod': 10}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 4.0, 'take_profit': 12.0}
    },
    {
        'name': 'Volume Breakout Strategy',
        'slug': 'volume-breakout',
        'category': 'Breakout',
        'hypothesis': 'Price breakout confirmed by a significant volume surge.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'CLOSE', 'params': {}, 'operator': 'crosses_above', 'value': {'indicator': 'BBANDS', 'params': {'output_index': 'upper'}}},
                {'indicator': 'VOLUME', 'params': {}, 'operator': '>', 'value': {'indicator': 'SMA', 'params': {'indicator': 'VOLUME', 'timeperiod': 20}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'CLOSE', 'params': {}, 'operator': 'crosses_below', 'value': {'indicator': 'BBANDS', 'params': {'output_index': 'middle'}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 5.0, 'take_profit': 15.0}
    },
    {
        'name': 'ATR Volatility Expansion',
        'slug': 'atr-volatility-expansion',
        'category': 'Volatility',
        'hypothesis': 'Trades volatility expansion moves confirmed by ATR and directional alignment.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'ATR', 'params': {'timeperiod': 14}, 'operator': '>', 'value': {'indicator': 'SMA', 'params': {'indicator': 'ATR', 'timeperiod': 20}}},
                {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 20}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'ATR', 'params': {'timeperiod': 14}, 'operator': '<', 'value': {'indicator': 'SMA', 'params': {'indicator': 'ATR', 'timeperiod': 20}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 6.0, 'take_profit': 18.0}
    },
    {
        'name': 'Ichimoku Cloud Breakout',
        'slug': 'ichimoku-breakout',
        'category': 'Trend Following',
        'hypothesis': 'Full cloud breakout system for strong directional moves.',
        'entry_rules': {
            'conditions': [
                {'indicator': 'CLOSE', 'params': {}, 'operator': '>', 'value': {'indicator': 'SAR', 'params': {}}}, # Cloud proxy
                {'indicator': 'EMA', 'params': {'timeperiod': 50}, 'operator': '>', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 200}}}
            ],
            'logical_operator': 'AND'
        },
        'exit_rules': {
            'conditions': [{'indicator': 'CLOSE', 'params': {}, 'operator': '<', 'value': {'indicator': 'EMA', 'params': {'timeperiod': 50}}}],
            'logical_operator': 'AND'
        },
        'risk_params': {'stop_loss': 8.0, 'take_profit': 25.0}
    },
    {
        'name': 'Revenue Per Share Strategy',
        'slug': 'revenue-per-share',
        'category': 'Fundamental',
        'hypothesis': 'Select companies with Revenue/Share > ₹100 and Revenue Growth >10%.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    },
    {
        'name': 'Promoter Shareholding Strategy',
        'slug': 'promoter-holding',
        'category': 'Fundamental',
        'hypothesis': 'Promoter Holding >50% and increasing QoQ.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    },
    {
        'name': 'Revenue Growth & EBITDA Strategy',
        'slug': 'revenue-ebitda',
        'category': 'Fundamental',
        'hypothesis': 'Revenue Growth >20%, EBITDA Margin improving.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    },
    {
        'name': 'ROI & Profitability Strategy',
        'slug': 'roi-profitability',
        'category': 'Fundamental',
        'hypothesis': 'ROI >20%, profitable for 3 years.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    },
    {
        'name': 'P/E Ratio & EPS Growth Strategy',
        'slug': 'pe-eps-growth',
        'category': 'Fundamental',
        'hypothesis': 'P/E <25, EPS Growth >10%.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    },
    {
        'name': 'EPS & Revenue Growth Strategy',
        'slug': 'eps-revenue-growth',
        'category': 'Fundamental',
        'hypothesis': 'EPS Growth >20%, Revenue Growth >15%.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    },
    {
        'name': 'Dividend Per Share Strategy',
        'slug': 'dividend-per-share',
        'category': 'Fundamental',
        'hypothesis': 'DPS >₹10, Dividend Yield >2%.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    },
    {
        'name': 'Dividend CAGR Strategy',
        'slug': 'dividend-cagr',
        'category': 'Fundamental',
        'hypothesis': '3Y Dividend CAGR >15%, Payout Ratio <60%.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    },
    {
        'name': 'Debt-to-Equity & ROE Strategy',
        'slug': 'debt-equity-roe',
        'category': 'Fundamental',
        'hypothesis': 'D/E <0.3, ROE >15%.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    },
    {
        'name': 'Book Value Per Share Strategy',
        'slug': 'book-value-per-share',
        'category': 'Fundamental',
        'hypothesis': 'Book Value/Share >₹400, P/B <2.',
        'entry_rules': {'conditions': [], 'logical_operator': 'AND'},
        'exit_rules': {'conditions': [], 'logical_operator': 'AND'},
        'risk_params': {}
    }
]

async def seed():
    print(f"Connecting to {settings.DATABASE_URL}...")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    success_count = 0
    update_count = 0
    
    async with async_session() as session:
        for s in strategies:
            # Check if exists by slug
            res = await session.execute(text("SELECT id FROM strategies WHERE slug = :slug"), {'slug': s['slug']})
            row = res.fetchone()
            
            entry_rules = json.dumps(s['entry_rules'])
            exit_rules = json.dumps(s['exit_rules'])
            risk_params = json.dumps(s['risk_params'])
            
            if not row:
                await session.execute(
                    text("INSERT INTO strategies (id, name, slug, category, hypothesis, entry_rules, exit_rules, risk_params, created_at) "
                         "VALUES (:id, :name, :slug, :category, :hypothesis, :entry_rules, :exit_rules, :risk_params, :created_at)"),
                    {
                        'id': uuid.uuid4(),
                        'name': s['name'],
                        'slug': s['slug'],
                        'category': s['category'],
                        'hypothesis': s['hypothesis'],
                        'entry_rules': entry_rules,
                        'exit_rules': exit_rules,
                        'risk_params': risk_params,
                        'created_at': datetime.utcnow()
                    }
                )
                success_count += 1
            else:
                # Update existing
                await session.execute(
                    text("UPDATE strategies SET name=:name, category=:category, hypothesis=:hypothesis, "
                         "entry_rules=:entry_rules, exit_rules=:exit_rules, risk_params=:risk_params "
                         "WHERE slug=:slug"),
                    {
                        'name': s['name'],
                        'slug': s['slug'],
                        'category': s['category'],
                        'hypothesis': s['hypothesis'],
                        'entry_rules': entry_rules,
                        'exit_rules': exit_rules,
                        'risk_params': risk_params
                    }
                )
                update_count += 1
                
        await session.commit()
    await engine.dispose()
    print(f"Seeding Complete! Inserted: {success_count}, Updated: {update_count}, Total: {len(strategies)}")

if __name__ == '__main__':
    asyncio.run(seed())
