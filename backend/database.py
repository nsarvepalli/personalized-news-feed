# SQLAlchemy database layer for Supabase PostgreSQL
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env file")

# Replace postgresql:// with postgresql+psycopg2:// (for SQLAlchemy 1.4)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

logger.info(f"Connecting to Supabase PostgreSQL...")

# Create engine with NullPool for serverless environments
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    poolclass=NullPool,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    try:
        from models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized (Supabase PostgreSQL)")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Saved Articles Functions
def save_article(db: Session, article_url: str, article_data: dict) -> bool:
    """Save an article to favorites"""
    try:
        from models import SavedArticle
        
        # Check if already saved
        existing = db.query(SavedArticle).filter(SavedArticle.article_url == article_url).first()
        if existing:
            return False  # Already saved

        db_saved = SavedArticle(
            article_url=article_url,
            article_title=article_data.get("title", "")[:500],
            article_source=article_data.get("source", ""),
            article_category=article_data.get("category", ""),
            article_summary=article_data.get("summary", "")[:1000]
        )
        db.add(db_saved)
        db.commit()
        logger.info(f"❤️ Article saved: {article_data.get('title', 'Unknown')[:50]}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to save article: {e}")
        return False


def get_saved_articles(db: Session, days_back: int = 7) -> List[dict]:
    """Get saved articles from last N days"""
    try:
        from models import SavedArticle
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        articles = db.query(SavedArticle).filter(SavedArticle.saved_at >= cutoff_date).order_by(SavedArticle.saved_at.desc()).all()

        return [
            {
                "id": a.id,
                "article_url": a.article_url,
                "article_title": a.article_title,
                "article_source": a.article_source,
                "article_category": a.article_category,
                "article_summary": a.article_summary,
                "saved_at": a.saved_at.isoformat()
            }
            for a in articles
        ]
    except Exception as e:
        logger.error(f"❌ Failed to get saved articles: {e}")
        return []


def remove_saved_article(db: Session, article_url: str) -> bool:
    """Remove article from saved"""
    try:
        from models import SavedArticle
        
        db.query(SavedArticle).filter(SavedArticle.article_url == article_url).delete()
        db.commit()
        logger.info(f"🗑️ Article removed from saved")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to remove saved article: {e}")
        return False


def is_article_saved(db: Session, article_url: str) -> bool:
    """Check if article is saved"""
    try:
        from models import SavedArticle
        
        return db.query(SavedArticle).filter(SavedArticle.article_url == article_url).first() is not None
    except Exception as e:
        logger.error(f"❌ Failed to check saved status: {e}")
        return False


def cleanup_old_saved_articles(db: Session, days: int = 7) -> int:
    """Delete saved articles older than N days"""
    try:
        from models import SavedArticle
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(SavedArticle).filter(SavedArticle.saved_at < cutoff_date).delete()
        db.commit()

        if deleted > 0:
            logger.info(f"🧹 Cleaned up {deleted} saved articles older than {days} days")

        return deleted
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to cleanup old articles: {e}")
        return 0
