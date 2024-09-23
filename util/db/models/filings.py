from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    # DateTime,
    # Float,
    ForeignKey,
    # Integer,
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
from sqlalchemy.dialects.postgresql import JSONB, BYTEA

from util.db.models.tickers import Base
import os
db_schema = os.environ.get("DATABASE_SCHEMA")

# Base = declarative_base(metadata=MetaData(schema=db_schema))

class Filings(Base):
    __tablename__ = "company_filings"
    __table_args__ = (UniqueConstraint('accessionNumber',
                    name='filings_constr'),
                    {"schema": db_schema})
    cik = Column(String, ForeignKey('symbols.cik_str'))
    accessionNumber = Column(String, primary_key=True)
    filingDate = Column(String, index=True)
    reportDate = Column(String, index=True)
    acceptanceDateTime = Column(String)
    act = Column(String, index=True)
    form = Column(String, index=True)
    fileNumber = Column(String)
    filmNumber = Column(String)
    items = Column(String)
    core_type = Column(String, index=True)
    size = Column(BigInteger)
    isXBRL = Column(Boolean)
    isInlineXBRL = Column(Boolean)
    primaryDocument = Column(String)
    primaryDocDescription = Column(String, index=True)
    cik_rel = relationship("Symbols", back_populates="filing_rel")