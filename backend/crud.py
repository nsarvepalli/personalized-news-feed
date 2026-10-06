# CRUD Operations
# Database operations for all models

import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from models import Article, Summary, UserPreference, Digest
from schemas import (
    ArticleCreate, SummaryCreate,
    UserPreferenceCreate, DigestCreate
)
from datetime import datetime, timedelta
from typing import List, Optional

logger = logging.getLogger(__name__)


# ============ Article CRUD ============

def create_article(db: Session, article: ArticleCreate) -> Article:
    """Create a new article, skip if already exists"""
    # Check if already exists
    existing = db.query(Article).filter(
        Article.source_id == article.source_id
    ).first()

    if existing:
        logger.info(f"📰 Article already exists: {article.source_id}")
        return existing

    db_article = Article(
        source=article.source,
        source_id=article.source_id,
        title=article.title,
        description=article.description,
        url=article.url,
        image_url=article.image_url,
        published_at=article.published_at,
        category=article.category,
        authors=article.authors,
        content=article.content
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    logger.info(f"✅ Created article: {db_article.title[:50]}")
    return db_article


def get_article(db: Session, article_id: int) -> Optional[Article]:
    """Get article by ID"""
    return db.query(Article).filter(Article.id == article_id).first()


def get_articles(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    source: Optional[str] = None,
    category: Optional[str] = None
) -> List[Article]:
    """Get articles with optional filters, sorted by published date"""
    query = db.query(Article)

    if source:
        query = query.filter(Article.source == source)
    if category:
        query = query.filter(Article.category == category)

    return query.order_by(desc(Article.published_at)).offset(skip).limit(limit).all()


def get_articles_by_date_range(
    db: Session,
    start_date: datetime,
    end_date: datetime
) -> List[Article]:
    """Get articles published between start and end dates"""
    return db.query(Article).filter(
        and_(
            Article.published_at >= start_date,
            Article.published_at <= end_date
        )
    ).order_by(desc(Article.published_at)).all()


def article_exists(db: Session, source_id: str) -> bool:
    """Check if article already exists by source_id"""
    return db.query(Article).filter(Article.source_id == source_id).first() is not None


def get_article_count(db: Session) -> int:
    """Get total article count"""
    return db.query(Article).count()


# ============ Summary CRUD ============

def create_summary(db: Session, article_id: int, summary_text: str, tags: List[str], relevance_score: float) -> Summary:
    """Create a new summary"""
    db_summary = Summary(
        article_id=article_id,
        summary_text=summary_text,
        interest_tags=tags,
        relevance_score=relevance_score
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    logger.info(f"✅ Created summary for article {article_id}")
    return db_summary


def get_summary(db: Session, summary_id: int) -> Optional[Summary]:
    """Get summary by ID"""
    return db.query(Summary).filter(Summary.id == summary_id).first()


def get_summaries(
    db: Session,
    skip: int = 0,
    limit: int = 20
) -> List[Summary]:
    """Get all summaries, sorted by relevance"""
    return db.query(Summary).order_by(desc(Summary.relevance_score)).offset(skip).limit(limit).all()


def get_summaries_by_interest(
    db: Session,
    interest: str,
    skip: int = 0,
    limit: int = 20
) -> List[Summary]:
    """Get summaries filtered by interest tag"""
    # Filter by interest tag in JSON array
    query = db.query(Summary).filter(
        Summary.interest_tags.ilike(f'%{interest}%')
    ).order_by(desc(Summary.relevance_score))

    return query.offset(skip).limit(limit).all()


def get_summaries_by_date_range(
    db: Session,
    start_date: datetime,
    end_date: datetime
) -> List[Summary]:
    """Get summaries created between dates"""
    return db.query(Summary).filter(
        and_(
            Summary.created_at >= start_date,
            Summary.created_at <= end_date
        )
    ).order_by(desc(Summary.created_at)).all()


def delete_old_summaries(db: Session, days: int = 30) -> int:
    """Delete summaries older than N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(Summary).filter(Summary.created_at < cutoff_date).delete()
    db.commit()
    logger.info(f"🗑️  Deleted {deleted} old summaries")
    return deleted


# ============ User Preference CRUD ============

def create_or_update_preferences(
    db: Session,
    preferences: UserPreferenceCreate
) -> UserPreference:
    """Create or update user preferences (single record)"""
    # Get existing or create new
    existing = db.query(UserPreference).first()

    if existing:
        existing.interests = preferences.interests
        existing.age_range = preferences.age_range
        existing.demographic = preferences.demographic
        existing.keywords_to_exclude = preferences.keywords_to_exclude
        existing.preferred_sources = preferences.preferred_sources
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        logger.info("✅ Updated user preferences")
        return existing

    db_prefs = UserPreference(
        interests=preferences.interests,
        age_range=preferences.age_range,
        demographic=preferences.demographic,
        keywords_to_exclude=preferences.keywords_to_exclude,
        preferred_sources=preferences.preferred_sources
    )
    db.add(db_prefs)
    db.commit()
    db.refresh(db_prefs)
    logger.info("✅ Created user preferences")
    return db_prefs


def get_preferences(db: Session) -> Optional[UserPreference]:
    """Get user preferences (single record)"""
    return db.query(UserPreference).first()


# ============ Digest CRUD ============

def create_digest(db: Session, digest_type: str, summaries_count: int, digest_content: dict) -> Digest:
    """Create a digest"""
    db_digest = Digest(
        digest_type=digest_type,
        summaries_count=summaries_count,
        digest_content=digest_content
    )
    db.add(db_digest)
    db.commit()
    db.refresh(db_digest)
    logger.info(f"✅ Created {digest_type} digest with {summaries_count} articles")
    return db_digest


def get_digest(db: Session, digest_id: int) -> Optional[Digest]:
    """Get digest by ID"""
    return db.query(Digest).filter(Digest.id == digest_id).first()


def get_digests_by_type(
    db: Session,
    digest_type: str,  # "morning" or "evening"
    days: int = 7
) -> List[Digest]:
    """Get digests of a specific type from last N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return db.query(Digest).filter(
        and_(
            Digest.digest_type == digest_type,
            Digest.created_at >= cutoff_date
        )
    ).order_by(desc(Digest.created_at)).all()


def mark_digest_as_sent(db: Session, digest_id: int) -> bool:
    """Mark digest as sent"""
    digest = db.query(Digest).filter(Digest.id == digest_id).first()
    if digest:
        digest.sent_at = datetime.utcnow()
        db.commit()
        logger.info(f"✅ Marked digest {digest_id} as sent")
        return True
    return False
