from sqlalchemy import Column, String, Float, BigInteger, JSON, Date, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class OHLCV(Base):
    __tablename__ = 'ohlcv'
    
    time = Column(DateTime(timezone=True), primary_key=True)
    symbol = Column(String, primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)

class OptionsChain(Base):
    __tablename__ = 'options_chain'
    
    timestamp = Column(DateTime(timezone=True), primary_key=True)
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
