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

import os
db_schema = os.environ.get("DATABASE_SCHEMA")

Base = declarative_base(metadata=MetaData(schema=db_schema))

class Symbols(Base):
    __tablename__ = "symbols"
    __table_args__ = (UniqueConstraint('cik_str',
                    name='symbol_constr'),
                    {"schema": db_schema})
    cik_str = Column(String, primary_key=True)
    ticker = Column(String)
    title = Column(String)
    meta_rel = relationship("Company_Meta", back_populates="cik_rel")
    mail_add_rel = relationship("Company_Mailing_Addresses", back_populates="cik_rel")
    busin_add_rel = relationship("Company_Business_Addresses", back_populates="cik_rel")
    filing_rel = relationship("Filings", back_populates="cik_rel")

class Company_Meta(Base):
    __tablename__ = "company_meta"
    __table_args__ = (UniqueConstraint('cik',
                    name='meta_constr'),
                    {"schema": db_schema})
    cik = Column(String, ForeignKey('symbols.cik_str'), autoincrement=False, primary_key=True)
    name = Column(String)
    tickers = Column(JSONB())
    exchanges = Column(JSONB())
    description = Column(String)
    website = Column(String)
    investorWebsite = Column(String)
    category = Column(String, index=True)
    fiscalYearEnd = Column(String)
    stateOfIncorporation = Column(String, index=True)
    stateOfIncorporationDescription = Column(String)
    ein = Column(String)
    entityType = Column(String)
    other = Column(String)
    sicDescription = Column(String)
    ownerOrg = Column(String)
    insiderTransactionForOwnerExists = Column(Boolean)
    insiderTransactionForIssuerExists = Column(Boolean)
    phone = Column(String)
    flags = Column(String)
    formerNames = Column(JSONB())
    cik_rel = relationship("Symbols", back_populates="meta_rel")

class Company_Mailing_Addresses(Base):
    __tablename__ = "mailing_addresses"
    __table_args__ = (UniqueConstraint('cik',
                    name='cma_constr'),
                    {"schema": db_schema})
    cik = Column(String, ForeignKey('symbols.cik_str'), autoincrement=False, primary_key=True)
    street1 = Column(String)
    street2 = Column(String)
    city = Column(String, index=True)
    stateOrCountry = Column(String, index=True)
    zipCode = Column(String)
    stateOrCountryDescription = Column(String, index=True)
    cik_rel = relationship("Symbols", back_populates="mail_add_rel")

class Company_Business_Addresses(Base):
    __tablename__ = "business_addresses"
    __table_args__ = (UniqueConstraint('cik',
                    name='cba_constr'),
                    {"schema": db_schema})
    cik = Column(String, ForeignKey('symbols.cik_str'), autoincrement=False, primary_key=True)
    street1 = Column(String)
    street2 = Column(String)
    city = Column(String, index=True)
    stateOrCountry = Column(String, index=True)
    zipCode = Column(String)
    stateOrCountryDescription = Column(String, index=True)
    cik_rel = relationship("Symbols", back_populates="busin_add_rel") 
