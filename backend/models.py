# SQLAlchemy models for Supabase PostgreSQL
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Article(Base):
    """Article model"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False)
    source_id = Column(String(200), nullable=True)
    category = Column(String(100), nullable=True)
    published_at = Column(DateTime, nullable=True)
    image_url = Column(String(1000), nullable=True)
    authors = Column(JSON, nullable=True)
    content = Column(Text, nullable=True)
    article_type = Column(String(50), default='News')
    fetched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    summaries = relationship("Summary", back_populates="article", cascade="all, delete-orphan")


class Summary(Base):
    """Summary model"""
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    summary_text = Column(Text, nullable=False)
    summary_length = Column(String(50), default='1-min read')
    relevance_score = Column(Float, default=0.0)
    interest_tags = Column(JSON, nullable=True)
    model_used = Column(String(50), default='gpt-3.5-turbo')
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="summaries")


class UserPreference(Base):
    """User preferences model"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    interests = Column(JSON, default=[])
    age_range = Column(String(50), default='25-35')
    demographic = Column(String(200), default='International Masters Student in USA')
    keywords_to_exclude = Column(JSON, default=[])
    preferred_sources = Column(JSON, default=['nyt', 'bloomberg', 'washingtonpost'])
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Digest(Base):
    """Digest model"""
    __tablename__ = "digests"

    id = Column(Integer, primary_key=True, index=True)
    digest_type = Column(String(50), nullable=False)
    summaries_count = Column(Integer, default=0)
    digest_content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)


class SavedArticle(Base):
    """Saved articles model"""
    __tablename__ = "saved_articles"

    id = Column(Integer, primary_key=True, index=True)
    article_url = Column(String(1000), unique=True, nullable=False, index=True)
    article_title = Column(String(500), nullable=False)
    article_source = Column(String(50), nullable=True)
    article_category = Column(String(100), nullable=True)
    article_summary = Column(Text, nullable=True)
    saved_at = Column(DateTime, default=datetime.utcnow)
