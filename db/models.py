# db/models.py
from sqlalchemy import (
    create_engine, Column, Integer, Text, DateTime
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()
DB_PATH = os.getenv("DB_PATH", "./cyberintel.db")
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False)


class Article(Base):
    __tablename__ = "articles"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    url            = Column(Text, unique=True, nullable=False)
    url_hash       = Column(Text, unique=True, nullable=False)
    content_hash   = Column(Text, nullable=False)
    title          = Column(Text)
    author         = Column(Text)
    date           = Column(Text)
    source         = Column(Text, nullable=False)
    categories     = Column(Text)        # JSON string
    tags           = Column(Text)        # JSON string
    raw_text       = Column(Text)
    clean_text     = Column(Text)
    parse_status   = Column(Text, default="pending")
    crawled_at     = Column(DateTime, server_default=func.now())
    parsed_at      = Column(DateTime)
    groq_summary   = Column(Text)
    report_id      = Column(Integer)


class Report(Base):
    __tablename__ = "reports"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    title      = Column(Text)
    template   = Column(Text)
    content    = Column(Text)
    pdf_path   = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


def init_db():
    Base.metadata.create_all(ENGINE)
    print("Database initialized at", DB_PATH)
