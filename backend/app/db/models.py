from sqlalchemy import Column, String, Float, BigInteger, JSON, Date, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
import uuid
from datetime import datetime

Base = declarative_base()

class OHLCV(Base):
    __tablename__ = 'ohlcv'
    
    time = Column(DateTime(timezone=True), primary_key=True)
    symbol = Column(String, primary_key=True)
    resolution = Column(String, primary_key=True) # '1m', '5m', '1h', '1d'
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)

class OptionsChain(Base):
    __tablename__ = 'options_chain'
    
    time = Column(DateTime(timezone=True), primary_key=True)
    symbol = Column(String, primary_key=True)
    expiry = Column(Date, primary_key=True)
    strike = Column(Float, primary_key=True)
    option_type = Column(String, primary_key=True) # 'CE' or 'PE'
    oi = Column(BigInteger)
    volume = Column(BigInteger)
    iv = Column(Float)
    ltp = Column(Float)
    greeks_json = Column(JSONB)

class Strategy(Base):
    __tablename__ = 'strategies'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    hypothesis = Column(Text)
    entry_rules = Column(JSONB)
    exit_rules = Column(JSONB)
    risk_params = Column(JSONB)
    backtest_results = Column(JSONB)
    strategy_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class PineScript(Base):
    __tablename__ = "pine_scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    source = Column(String, nullable=False, default="upload")
    pine_script = Column(Text, nullable=False)
    strategy_spec = Column(JSONB)
    symbol = Column(String)
    period = Column(String)
    resolution = Column(String)
    prompt = Column(Text)
    script_metadata = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    backtests = relationship("BacktestRun", back_populates="pine_script")


class BacktestRun(Base):
    __tablename__ = "backtests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=True)
    pine_script_id = Column(UUID(as_uuid=True), ForeignKey("pine_scripts.id"), nullable=True)
    user_request_json = Column(JSONB)
    status = Column(String, default="pending")
    symbol = Column(String)
    period = Column(String)
    resolution = Column(String)
    strategy_spec = Column(JSONB)
    strategy_label = Column(String)
    source = Column(String, default="engine")
    metrics = Column(JSONB)
    equity_curve = Column(JSONB)
    trade_log = Column(JSONB)
    drawdown_series = Column(JSONB)
    monthly_returns = Column(JSONB)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))

    pine_script = relationship("PineScript", back_populates="backtests")


class IndependentStrategy(Base):
    __tablename__ = 'independent_strategies'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    hypothesis = Column(Text)
    entry_rules = Column(JSONB)
    exit_rules = Column(JSONB)
    risk_params = Column(JSONB)
    strategy_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
