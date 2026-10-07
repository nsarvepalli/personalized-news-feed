"""
Supabase PostgreSQL database module
Production-ready database layer using Supabase PostgreSQL
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from config import get_settings

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Supabase PostgreSQL database connection and operations"""

    def __init__(self):
        self.settings = get_settings()
        self.connection = None
        self._connect()

    def _connect(self):
        """Establish database connection"""
        try:
            if not self.settings.database_url:
                raise ValueError("DATABASE_URL not configured in environment variables")

            self.connection = psycopg2.connect(self.settings.database_url)
            logger.info("✅ Connected to Supabase PostgreSQL")
            self._init_tables()
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            raise

    def _init_tables(self):
        """Initialize database tables"""
        try:
            cursor = self.connection.cursor()

            # Articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    source_id TEXT,
                    category TEXT,
                    published_at TIMESTAMP,
                    image_url TEXT,
                    authors JSONB DEFAULT '[]'::jsonb,
                    content TEXT,
                    article_type TEXT DEFAULT 'News',
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Summaries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                    summary_text TEXT NOT NULL,
                    summary_length TEXT DEFAULT '1-min read',
                    relevance_score FLOAT DEFAULT 0.0,
                    interest_tags JSONB DEFAULT '[]'::jsonb,
                    model_used TEXT DEFAULT 'gpt-3.5-turbo',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id SERIAL PRIMARY KEY,
                    interests JSONB DEFAULT '[]'::jsonb,
                    age_range TEXT DEFAULT '25-35',
                    demographic TEXT DEFAULT 'International Masters Student in USA',
                    keywords_to_exclude JSONB DEFAULT '[]'::jsonb,
                    preferred_sources JSONB DEFAULT '["nyt", "washingtonpost"]'::jsonb,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Digests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS digests (
                    id SERIAL PRIMARY KEY,
                    digest_type TEXT NOT NULL,
                    summaries_count INTEGER,
                    digest_content JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP
                )
            """)

            # Saved articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_articles (
                    id SERIAL PRIMARY KEY,
                    article_url TEXT UNIQUE NOT NULL,
                    article_title TEXT NOT NULL,
                    article_source TEXT,
                    article_category TEXT,
                    article_summary TEXT,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.connection.commit()
            logger.info("✅ Database tables initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize tables: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    # CRUD Operations

    def save_article(self, article_url: str, article_data: Dict[str, Any]) -> bool:
        """Save an article to favorites"""
        try:
            cursor = self.connection.cursor()

            cursor.execute(
                """
                INSERT INTO saved_articles
                (article_url, article_title, article_source, article_category, article_summary, saved_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (article_url) DO NOTHING
                RETURNING id
                """,
                (
                    article_url,
                    article_data.get('title', '')[:500],
                    article_data.get('source', ''),
                    article_data.get('category', ''),
                    article_data.get('summary', '')[:1000],
                    datetime.now().isoformat()
                )
            )

            result = cursor.fetchone()
            self.connection.commit()

            if result:
                logger.info(f"❤️ Article saved: {article_data.get('title', 'Unknown')[:50]}")
                return True
            else:
                logger.info("Article already saved")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to save article: {e}")
            self.connection.rollback()
            return False

    def get_saved_articles(self, days_back: int = 7) -> List[Dict]:
        """Get saved articles from last N days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT * FROM saved_articles
                WHERE saved_at >= %s
                ORDER BY saved_at DESC
                """,
                (cutoff_date,)
            )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Failed to get saved articles: {e}")
            return []

    def remove_saved_article(self, article_url: str) -> bool:
        """Remove article from saved"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM saved_articles WHERE article_url = %s", (article_url,))
            self.connection.commit()

            logger.info("🗑️ Article removed from saved")
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"❌ Failed to remove saved article: {e}")
            self.connection.rollback()
            return False

    def is_article_saved(self, article_url: str) -> bool:
        """Check if article is saved"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM saved_articles WHERE article_url = %s", (article_url,))
            result = cursor.fetchone()
            return result is not None

        except Exception as e:
            logger.error(f"❌ Failed to check saved status: {e}")
            return False

    def cleanup_old_saved_articles(self, days: int = 7) -> int:
        """Delete saved articles older than N days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM saved_articles WHERE saved_at < %s", (cutoff_date,))
            self.connection.commit()

            deleted_count = cursor.rowcount
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} saved articles older than {days} days")

            return deleted_count

        except Exception as e:
            logger.error(f"❌ Failed to cleanup old articles: {e}")
            return 0


# Singleton instance
_db_instance: Optional[SupabaseDB] = None


def get_db() -> SupabaseDB:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDB()
    return _db_instance


def close_db():
    """Close database connection"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None
