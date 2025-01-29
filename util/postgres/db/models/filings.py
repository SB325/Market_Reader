from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    # DateTime,
    # Float,
    ForeignKey,
    Integer,
    # Text,
    String,
    UniqueConstraint,
    PrimaryKeyConstraint,
    # text,
    MetaData,
)

# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, declarative_base
# from sqlalchemy.sql import *
from sqlalchemy.dialects.postgresql import BYTEA

from util.db.models.tickers import Base
import os
db_schema = os.environ.get("DATABASE_SCHEMA")

class Filings(Base):
    __tablename__ = "company_filings"
    __table_args__ = ({"schema": db_schema})
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, ForeignKey('symbols.cik_str'))
    accessionNumber = Column(String)
    filingDate = Column(String)
    reportDate = Column(String)
    acceptanceDateTime = Column(String)
    act = Column(String)
    form = Column(String)
    fileNumber = Column(String)
    filmNumber = Column(String)
    items = Column(String)
    core_type = Column(String)
    size = Column(BigInteger)
    isXBRL = Column(Boolean)
    isInlineXBRL = Column(Boolean)
    primaryDocument = Column(String)
    primaryDocDescription = Column(String)
    cik_rel = relationship("Symbols", back_populates="filing_rel")

class SharesOutstanding(Base):
    __tablename__ = "shares_outstanding"
    __table_args__ = ({"schema": db_schema})
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, ForeignKey('symbols.cik_str'))
    end = Column(String)
    val = Column(BigInteger)
    accn = Column(String)
    fy = Column(Integer)
    fp = Column(String)
    form = Column(String)
    filed = Column(String)
    frame = Column(String)
    cik_rel = relationship("Symbols", back_populates="filing_shares")
     
class StockFloat(Base):
    __tablename__ = "stock_float"
    __table_args__ = ({"schema": db_schema})
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, ForeignKey('symbols.cik_str'))
    end = Column(String)
    val = Column(BigInteger)
    accn = Column(String)
    fy = Column(Integer)
    fp = Column(String)
    form = Column(String)
    filed = Column(String)
    frame = Column(String)
    currency = Column(String)
    cik_rel = relationship("Symbols", back_populates="filing_float")

class Accounting(Base):
    __tablename__ = "accounting"
    __table_args__ = ({"schema": db_schema})
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, ForeignKey('symbols.cik_str'))
    start = Column(String)
    end = Column(String)
    val = Column(BigInteger)    
    accn = Column(String)
    fy = Column(Integer)
    fp = Column(String)
    form = Column(String)
    filed = Column(String)
    type = Column(String)
    frame = Column(String)
    cik_rel = relationship("Symbols", back_populates="filing_acct")