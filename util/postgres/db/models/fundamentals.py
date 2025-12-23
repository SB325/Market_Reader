from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    String,
    UniqueConstraint,
    PrimaryKeyConstraint,
    MetaData,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, declarative_base
# from sqlalchemy.sql import *
from sqlalchemy.dialects.postgresql import JSONB, BYTEA
from dotenv import load_dotenv
load_dotenv('.env')

import os
db_schema = os.getenv("DATABASE_SCHEMA")

FundamentalsBase = declarative_base(metadata=MetaData(schema=db_schema))

class FundamentalsArtifacts(FundamentalsBase):
    __tablename__ = "fundamentals_artifacts"
    __table_args__ = (UniqueConstraint("accessionNumber",
                        name='fartifacts_uc',
                        ),
                        {"schema": db_schema},
                    )
    ind = Column(Integer, primary_key=True, autoincrement=True) 
    cik = Column(String, index=True)  
    reportDate = Column(String)
    acceptanceDateTime = Column(DateTime)
    accessionNumber = Column(String)
    uri = Column(String)
    primaryDocDescription = Column(String, index=True)
    filename = Column(String)
    rawContent = Column(Text)
    cleanContent = Column(JSONB)