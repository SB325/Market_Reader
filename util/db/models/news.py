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
import os
os.path('../../../')
from dotenv import load_dotenv
load_dotenv(override=True) 

from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB, BYTEA
from util.db.models.filings import Base

db_schema = os.getenv("DATABASE_SCHEMA")

Base = declarative_base(metadata=MetaData(schema=db_schema))

class News(Base):
    __tablename__ = "news_main"
    __table_args__ = ({"schema": news_schema})
    id = Column(Integer, primary_key=True) 
    author = Column(String)
    created = Column(String)
    updated = Column(String)
    title = Column(String)
    teaser = Column(String)
    body = Column(String)
    url = Column(String)
    ment_img_rel = relationship("MentionedImages", back_populates="id_rel")
    ment_chan_rel = relationship("MentionedChannels", back_populates="id_rel")
    ment_stoc_rel = relationship("MentionedStocks", back_populates="id_rel")
    ment_tag_rel = relationship("MentionedTags", back_populates="id_rel")
    webhook_rel = relationship("Webhook", back_populates="id_rel")

class MentionedImages(Base):
    __tablename__ = "mentioned_images"
    __table_args__ = ({"schema": news_schema})
    id = Column(Integer, ForeignKey('News.id')) 
    size = Column(String, index=True)
    url = Column(String)
    id_rel = relationship("News", back_populates="ment_img_rel")

class MentionedChannels(Base):
    __tablename__ = "mentioned_channels"
    __table_args__ = ({"schema": news_schema})
    id = Column(Integer, ForeignKey('News.id')) 
    name = Column(String, index=True)
    id_rel = relationship("News", back_populates="ment_chan_rel")

class MentionedStocks(Base):
    __tablename__ = "mentioned_stocks"
    __table_args__ = ({"schema": news_schema})
    id = Column(Integer, ForeignKey('News.id')) 
    name = Column(String, index=True)
    id_rel = relationship("News", back_populates="ment_stoc_rel")
    
class MentionedTags(Base):
    __tablename__ = "mentioned_tags"
    __table_args__ = ({"schema": news_schema})
    id = Column(Integer, ForeignKey('News.id')) 
    name = Column(String, index=True)
    id_rel = relationship("News", back_populates="ment_tag_rel")

# Push webhook news content to news table prior to push to webhook table to 
# avoid Foreign Key constraint error.
class Webhook(Base):
    __tablename__ = "webhooks"
    __table_args__ = ({"schema": news_schema})
    id = Column(Integer, primary_key=True) 
    kind = Column(String)
    action = Column(String, index=True)
    news_id = Column(String, ForeignKey('News.id'))
    id_rel = relationship("News", back_populates="webhook_rel")