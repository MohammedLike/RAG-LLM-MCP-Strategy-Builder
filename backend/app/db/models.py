"""
Quant AI Agent — SQLAlchemy ORM Models

Maps to the PostgreSQL + TimescaleDB schema defined in infra/postgres/init.sql.
Uses async SQLAlchemy 2.0 style with mapped_column.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class OHLCV(Base):
    """
    Historical price data — OHLCV candles.
    TimescaleDB hypertable partitioned by timestamp.
    """

    __tablename__ = "ohlcv"

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    symbol: Mapped[str] = mapped_column(String(30), primary_key=True)
    interval: Mapped[str] = mapped_column(
        String(10), primary_key=True, default="1d"
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, default=0)
    vwap: Mapped[float | None] = mapped_column(Float, nullable=True)
    trades: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<OHLCV {self.symbol} {self.interval} "
            f"{self.timestamp:%Y-%m-%d} C={self.close}>"
        )


class OptionsChain(Base):
    """
    Options chain snapshot — captured at a point in time.
    Stores individual option contracts with Greeks.
    """

    __tablename__ = "options_chain"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    expiry: Mapped[date] = mapped_column(nullable=False)
    strike: Mapped[float] = mapped_column(Float, nullable=False)
    option_type: Mapped[str] = mapped_column(String(2), nullable=False)  # CE, PE

    # Market data
    ltp: Mapped[float | None] = mapped_column(Float, nullable=True)
    bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    open_interest: Mapped[int] = mapped_column(BigInteger, default=0)
    oi_change: Mapped[int] = mapped_column(BigInteger, default=0)
    volume: Mapped[int] = mapped_column(BigInteger, default=0)

    # Greeks
    iv: Mapped[float | None] = mapped_column(Float, nullable=True)
    delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    gamma: Mapped[float | None] = mapped_column(Float, nullable=True)
    theta: Mapped[float | None] = mapped_column(Float, nullable=True)
    vega: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Derived
    pcr: Mapped[float | None] = mapped_column(Float, nullable=True)
    underlying_ltp: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Option {self.symbol} {self.expiry} "
            f"{self.strike}{self.option_type} LTP={self.ltp}>"
        )


class Strategy(Base):
    """
    Strategy knowledge base — stores strategy definitions and backtest results.
    Entry/exit rules and results are stored as JSONB for flexibility.
    """

    __tablename__ = "strategies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    underlying: Mapped[list[str]] = mapped_column(
        ARRAY(String(30)), default=list
    )

    # Strategy definition
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    entry_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    exit_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    risk_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    market_conditions: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Results
    backtest_results: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Strategy {self.slug} [{self.category}]>"


class BacktestRun(Base):
    """Individual backtest execution with cached results."""

    __tablename__ = "backtest_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    strategy_slug: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Input
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, default=1_000_000)
    params: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Results
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    equity_curve: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    trade_log: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Meta
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<BacktestRun {self.strategy_slug} "
            f"{self.start_date}→{self.end_date}>"
        )


class ChatSession(Base):
    """Persistent chat session metadata."""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ChatSession {self.session_id}>"


class ChatMessage(Base):
    """Individual chat message within a session."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tool_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ChatMessage {self.role} in {self.session_id}>"
