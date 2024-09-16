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

from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB, BYTEA
from util.db.models.user_accounts import Base

import os
db_schema = os.environ.get("DATABASE_SCHEMA")

class User(Base):
    __tablename__ = "user"
    __table_args__ = (UniqueConstraint('user_name',
                    'email',
                    'phone',
                    name='user_uniconst'),
                    {"schema": db_schema})
    user_id = Column(BigInteger, primary_key=True)
    user_name = Column(String, ForeignKey('user_creds.user_name'))
    fname = Column(String)
    lname = Column(String)
    email = Column(String)
    phone = Column(String)
    payment_token = Column(String)
    access_privilege_conf = Column(String)
    user_creds = relationship("User_Creds", uselist=False, backref="user_name")

class HostTable(Base):
    __tablename__ = "host"
    __table_args__ = (UniqueConstraint('id',
                    name='host_uniconst'),       
                    {"schema": db_schema})
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('user.user_id'))
    event_id = Column(String, ForeignKey('event.event_id'))
    data_link_user = relationship("User", uselist=False, backref="host")
    data_link_event = relationship("Event", uselist=False, backref="host")

class GuestTable(Base):
    __tablename__ = "guest"
    __table_args__ = (UniqueConstraint('id',
                    name='guest_uniconst'),       
                    {"schema": db_schema})
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('user.user_id'))
    event_id = Column(String, ForeignKey('event.event_id'))
    attendance_is_publishable = Column(Boolean)
    rsvp_responded = Column(Boolean)
    rsvp_received = Column(Boolean)
    data_link_user = relationship("User", uselist=False, backref="guest")
    data_link_event = relationship("Event", uselist=False, backref="guest")

class Event(Base):
    __tablename__ = "event"
    __table_args__ = (UniqueConstraint('event_id',
                    name='event_uniconst'),       
                    {"schema": db_schema})
    event_id = Column(String, ForeignKey('guest.event_id'), primary_key=True)
    # data_link_guest = relationship("guest", backref="event")