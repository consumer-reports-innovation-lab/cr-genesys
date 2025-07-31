from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid
import cuid
import enum

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    email_verified = Column(DateTime, nullable=True)
    password = Column(String, nullable=True)
    image = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    chats = relationship('Chat', back_populates='user')
    sessions = relationship('Session', back_populates='user')
    # Add accounts, authenticators as needed

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(String, primary_key=True, index=True)
    session_token = Column(String, unique=True, nullable=False)
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    expires = Column(DateTime, nullable=False)
    device_id = Column(String, nullable=True)  # Add missing device_id column
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship('User', back_populates='sessions')

class ChatStatus(enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=True)
    status = Column(Enum(ChatStatus), default=ChatStatus.OPEN, nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Genesys Open Messaging fields
    genesys_open_message_session_id = Column(String, nullable=True)
    genesys_open_message_active = Column(Boolean, default=True)

    user = relationship('User', back_populates='chats')
    messages = relationship('Message', back_populates='chat')

class Message(Base):
    __tablename__ = 'messages'
    id = Column(String, primary_key=True, index=True, default=cuid.cuid)
    content = Column(Text, nullable=False)
    chat_id = Column(String, ForeignKey('chats.id'), nullable=False)
    is_system = Column(Boolean, default=False)
    is_markdown = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Genesys Open Messaging fields
    sent_to_genesys = Column(Boolean, default=False)
    genesys_message_id = Column(String, nullable=True)
    
    # Message type for UI styling: 'user', 'system', 'system_to_genesys', 'genesys'
    message_type = Column(String, default='user', nullable=False)

    chat = relationship('Chat', back_populates='messages')
