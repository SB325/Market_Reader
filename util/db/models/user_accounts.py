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

class User_Creds(Base):
    __tablename__ = "user_creds"
    __table_args__ = (UniqueConstraint('user_name',
                    name='user_creds_uniconst'),
                    {"schema": db_schema})
    user_id = Column(BigInteger, primary_key=True)
    user_name = Column(String)
    hashed_key = Column(String)
    user_metrics = relationship("User_Metrics", back_populates="user_creds")
    
class User_Metrics(Base):
    __tablename__ = "metrics"
    __table_args__ = {"schema": db_schema}  
    user_id = Column(BigInteger, primary_key=True)
    user_name = Column(String, ForeignKey('user_creds.user_name'), primary_key=True)
    endpoint = Column(JSONB, primary_key=True)
    parameters = Column(JSONB, primary_key=True)
    request_time = Column(String, primary_key=True)
    run_time = Column(String)
    user_creds = relationship("User_Creds", uselist=False, back_populates="user_name")