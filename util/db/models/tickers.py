from sqlalchemy import (
    BigInteger,
    # Boolean,
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
    __table_args__ = ({"schema": db_schema})
    symbol = Column(String, primary_key=True)
    name = Column(String)
    CIK = Column(String)