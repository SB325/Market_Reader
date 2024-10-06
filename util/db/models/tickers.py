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
from sqlalchemy.dialects.postgresql import JSONB, BYTEA

import os
db_schema = os.environ.get("DATABASE_SCHEMA")

Base = declarative_base(metadata=MetaData(schema=db_schema))

class Symbols(Base):
    __tablename__ = "symbols"
    __table_args__ = ({"schema": db_schema})
    ind = Column(Integer, autoincrement=True) 
    cik_str = Column(String, primary_key=True)
    ticker = Column(String)
    title = Column(String)
    meta_rel = relationship("Company_Meta", back_populates="cik_rel")
    mail_add_rel = relationship("Company_Mailing_Addresses", back_populates="cik_rel")
    busin_add_rel = relationship("Company_Business_Addresses", back_populates="cik_rel")
    filing_rel = relationship("Filings", back_populates="cik_rel")
    filing_shares = relationship("SharesOutstanding", back_populates="cik_rel")
    filing_float = relationship("StockFloat", back_populates="cik_rel")
    filing_acct = relationship("Accounting", back_populates="cik_rel")

class Company_Meta(Base):
    __tablename__ = "company_meta"
    __table_args__ = ({"schema": db_schema})
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, ForeignKey('symbols.cik_str'))  
    name = Column(String)
    tickers = Column(String)
    exchanges = Column(String)
    description = Column(String)
    website = Column(String)
    investorWebsite = Column(String)
    category = Column(String)
    fiscalYearEnd = Column(String)
    stateOfIncorporation = Column(String)
    stateOfIncorporationDescription = Column(String)
    ein = Column(String)
    entityType = Column(String)
    sicDescription = Column(String)
    ownerOrg = Column(String)
    insiderTransactionForOwnerExists = Column(Boolean)
    insiderTransactionForIssuerExists = Column(Boolean)
    phone = Column(String)
    flags = Column(String)
    formerNames = Column(String)
    cik_rel = relationship("Symbols", back_populates="meta_rel")

class Company_Mailing_Addresses(Base):
    __tablename__ = "mailing_addresses"
    __table_args__ = ({"schema": db_schema})
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, ForeignKey('symbols.cik_str'))  
    street1 = Column(String)
    street2 = Column(String)
    city = Column(String)
    stateOrCountry = Column(String)
    zipCode = Column(String)
    stateOrCountryDescription = Column(String)
    cik_rel = relationship("Symbols", back_populates="mail_add_rel")

class Company_Business_Addresses(Base):
    __tablename__ = "business_addresses"
    __table_args__ = ({"schema": db_schema})
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, ForeignKey('symbols.cik_str'))  
    street1 = Column(String)
    street2 = Column(String)
    city = Column(String)
    stateOrCountry = Column(String)
    zipCode = Column(String)
    stateOrCountryDescription = Column(String)
    cik_rel = relationship("Symbols", back_populates="busin_add_rel") 
