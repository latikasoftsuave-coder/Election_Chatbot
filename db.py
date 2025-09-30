from sqlalchemy import create_engine, Boolean, Integer, String, Column, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DB_USER = "qa_user"
DB_PASSWORD = "strongpassword123"
DB_NAME = "election_chatbot_db"
DB_HOST = "localhost"
DB_PORT = "5432"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Analysis(Base):
    __tablename__ = "analysis"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, unique=True)
    is_eligible = Column(Boolean, nullable=True)
    reason = Column(String, nullable=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)