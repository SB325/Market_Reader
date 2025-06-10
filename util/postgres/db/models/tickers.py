from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    # DateTime,
    Float,
    ForeignKey,
    Integer,
    # Text,
    String,
    UniqueConstraint,
    PrimaryKeyConstraint,
    # text,
    MetaData,
    UniqueConstraint,
)

# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, declarative_base
# from sqlalchemy.sql import *
from sqlalchemy.dialects.postgresql import JSONB, BYTEA
from dotenv import load_dotenv
load_dotenv('.env')

import os
db_schema = os.getenv("DATABASE_SCHEMA")

Base = declarative_base(metadata=MetaData(schema=db_schema))

class Symbols(Base):
    __tablename__ = "symbols"
    __table_args__ = (UniqueConstraint("cik_str", 
                        name='symbols_uc'
                        ),
                        {"schema": db_schema},
                    )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik_str = Column(String)
    ticker = Column(String)
    title = Column(String)

class Company_Meta(Base):
    __tablename__ = "company_meta"
    __table_args__ = (UniqueConstraint("cik", "ein",
                        name='cmeta_uc',
                        ),
                        {"schema": db_schema},
                    )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String)  
    name = Column(String)
    tickers = Column(String)
    exchanges = Column(String)
    description = Column(String)
    website = Column(String)
    investorWebsite = Column(String)
    category = Column(String)
    fiscalYearEnd = Column(String, index=True)
    stateOfIncorporation = Column(String, index=True)
    stateOfIncorporationDescription = Column(String)
    ein = Column(String)
    entityType = Column(String, index=True)
    sicDescription = Column(String)
    ownerOrg = Column(String)
    insiderTransactionForOwnerExists = Column(Boolean)
    insiderTransactionForIssuerExists = Column(Boolean)
    phone = Column(String)
    flags = Column(String)
    formerNames = Column(String)

class Company_Mailing_Addresses(Base):
    __tablename__ = "mailing_addresses"
    __table_args__ = (UniqueConstraint("cik",
                        name='cma_uc',
                        ),
                        {"schema": db_schema},
                        )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String)  
    street1 = Column(String)
    street2 = Column(String)
    city = Column(String, index=True)
    stateOrCountry = Column(String, index=True)
    zipCode = Column(String)
    stateOrCountryDescription = Column(String, index=True)

class Company_Business_Addresses(Base):
    __tablename__ = "business_addresses"
    __table_args__ = (UniqueConstraint("cik",
                        name='cba_uc',
                        ),
                        {"schema": db_schema},
                    )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, index=True)  
    street1 = Column(String)
    street2 = Column(String)
    city = Column(String, index=True)
    stateOrCountry = Column(String, index=True)
    zipCode = Column(String)
    stateOrCountryDescription = Column(String)

class Filings(Base):
    __tablename__ = "company_filings"
    __table_args__ = (UniqueConstraint("cik", 
                        "accessionNumber",
                        name='filings_uc',
                        ),
                        {"schema": db_schema},
                        )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, index=True)
    accessionNumber = Column(String)
    filingDate = Column(String)
    reportDate = Column(String)
    acceptanceDateTime = Column(String)
    act = Column(String)
    form = Column(String, index=True)
    fileNumber = Column(String)
    filmNumber = Column(String)
    items = Column(String)
    core_type = Column(String)
    size = Column(BigInteger)
    isXBRL = Column(Boolean)
    isInlineXBRL = Column(Boolean)
    primaryDocument = Column(String)
    primaryDocDescription = Column(String)

class SharesOutstanding(Base):
    __tablename__ = "shares_outstanding"
    __table_args__ = (UniqueConstraint("cik", "accn", "fy", "form",
                        name='sharesoutstanding_uc',
                        ),
                        {"schema": db_schema},
                        )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, index=True)
    end = Column(String)
    val = Column(BigInteger)
    accn = Column(String)
    fy = Column(Integer, index=True)
    fp = Column(String, index=True)
    form = Column(String, index=True)
    filed = Column(String)
    frame = Column(String)
     
class StockFloat(Base):
    __tablename__ = "stock_float"
    __table_args__ = (UniqueConstraint("cik", "accn", "fy", "form",
                        name='stockfloat_uc',
                        ),
                        {"schema": db_schema},
                        )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, index=True)
    end = Column(String)
    val = Column(BigInteger)
    accn = Column(String)
    fy = Column(Integer, index=True)
    fp = Column(String, index=True)
    form = Column(String, index=True)
    filed = Column(String)
    frame = Column(String)
    currency = Column(String, index=True)

class Accounting(Base):
    __tablename__ = "accounting"
    __table_args__ = (UniqueConstraint("cik", 
                        "start",
                        "end",
                        "fy",
                        name='accounting_uc',
                        ),
                        {"schema": db_schema},
                    )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, index=True)
    start = Column(String)
    end = Column(String)
    val = Column(BigInteger)    
    accn = Column(String)
    fy = Column(Integer, index=True)
    fp = Column(String, index=True)
    form = Column(String, index=True)
    filed = Column(String)
    type = Column(String, index=True)
    frame = Column(String)

class Technicals(Base):
    __tablename__ = "technicals"
    __table_args__ = (UniqueConstraint(
                        'ticker', 
                        'datetime', 
                        name='technical_uc',
                        ),
                        {"schema": db_schema},
                    )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    ticker = Column(String, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    datetime = Column(Integer, index=True)
