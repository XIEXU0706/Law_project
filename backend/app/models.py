import uuid
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime

def generate_uuid():
    return str(uuid.uuid4())

# 声明基类
class Base(DeclarativeBase):
    create_time: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(),default=func.now(), comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), onupdate=func.now(),default=func.now, comment="更新时间")


class ChatSession(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, index=True, default=generate_uuid)
    title = Column(String(255), default="新会话")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.create_time")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"))
    role = Column(String(50))   # 'user' 或 'ai'
    content = Column(Text)      # 存储对话的具体内容
    session = relationship("ChatSession", back_populates="messages")
