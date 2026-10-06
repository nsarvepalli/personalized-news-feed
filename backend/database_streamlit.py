"""
Streamlit-compatible database module
Uses SQLite for local development, easily switched to Supabase PostgreSQL for production
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Database file path - use absolute path to avoid issues when running from different directories
import os
DB_PATH = Path(os.path.abspath(__file__)).parent.parent / "data" / "articles.db"
try:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"✅ Database directory ready: {DB_PATH.parent}")
except Exception as e:
    logger.error(f"❌ Failed to create database directory: {e}")


def get_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()

    # Articles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            source_id TEXT,
            category TEXT,
            published_at TIMESTAMP,
            image_url TEXT,
            authors TEXT,  -- JSON array as string
            content TEXT,
            article_type TEXT DEFAULT 'News',
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Summaries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            summary_text TEXT NOT NULL,
            summary_length TEXT DEFAULT '1-min read',
            relevance_score FLOAT DEFAULT 0.0,
            interest_tags TEXT,  -- JSON array as string
            model_used TEXT DEFAULT 'gpt-3.5-turbo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
        )
    """)

    # User preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interests TEXT NOT NULL,  -- JSON array as string
            age_range TEXT DEFAULT '25-35',
            demographic TEXT DEFAULT 'International Masters Student in USA',
            keywords_to_exclude TEXT,  -- JSON array as string
            preferred_sources TEXT DEFAULT '["nyt", "bloomberg", "washingtonpost"]',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Digests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            digest_type TEXT NOT NULL,  -- 'morning' or 'evening'
            summaries_count INTEGER,
            digest_content TEXT NOT NULL,  -- JSON
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP
        )
    """)

    # Saved articles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_url TEXT UNIQUE NOT NULL,
            article_title TEXT NOT NULL,
            article_source TEXT,
            article_category TEXT,
            article_summary TEXT,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    logger.info("✅ Database initialized successfully")


# CRUD Operations

def create_article(article_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new article"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        authors_json = json.dumps(article_data.get("authors", []))

        cursor.execute("""
            INSERT INTO articles (
                title, description, url, source, source_id, category,
                published_at, image_url, authors, content, article_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article_data.get("title"),
            article_data.get("description"),
            article_data.get("url"),
            article_data.get("source"),
            article_data.get("source_id"),
            article_data.get("category"),
            article_data.get("published_at"),
            article_data.get("image_url"),
            authors_json,
            article_data.get("content"),
            article_data.get("article_type", "News")
        ))

        conn.commit()
        article_id = cursor.lastrowid
        logger.info(f"✅ Article created: {article_id}")
        return {"id": article_id, **article_data}

    except sqlite3.IntegrityError:
        logger.warning(f"⚠️  Article already exists: {article_data.get('url')}")
        return None
    finally:
        conn.close()


def get_articles(skip: int = 0, limit: int = 20, source: Optional[str] = None) -> List[Dict]:
    """Get articles from database"""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM articles"
    params = []

    if source:
        query += " WHERE source = ?"
        params.append(source)

    query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, skip])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    articles = []
    for row in rows:
        article = dict(row)
        article["authors"] = json.loads(article.get("authors", "[]"))
        articles.append(article)

    return articles


def article_exists(url: str) -> bool:
    """Check if article already exists"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def create_summary(summary_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new summary"""
    conn = get_connection()
    cursor = conn.cursor()

    tags_json = json.dumps(summary_data.get("interest_tags", []))

    cursor.execute("""
        INSERT INTO summaries (
            article_id, summary_text, summary_length,
            relevance_score, interest_tags, model_used
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        summary_data.get("article_id"),
        summary_data.get("summary_text"),
        summary_data.get("summary_length", "1-min read"),
        summary_data.get("relevance_score", 0.0),
        tags_json,
        summary_data.get("model_used", "gpt-3.5-turbo")
    ))

    conn.commit()
    summary_id = cursor.lastrowid
    conn.close()

    logger.info(f"✅ Summary created: {summary_id}")
    return {"id": summary_id, **summary_data}


def get_summaries(skip: int = 0, limit: int = 20, interest: Optional[str] = None) -> List[Dict]:
    """Get summaries from database"""
    conn = get_connection()
    cursor = conn.cursor()

    if interest:
        # Search for interest in tags
        query = """
            SELECT s.*, a.title, a.url, a.source, a.category, a.published_at
            FROM summaries s
            JOIN articles a ON s.article_id = a.id
            WHERE s.interest_tags LIKE ?
            ORDER BY s.relevance_score DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, (f"%{interest}%", limit, skip))
    else:
        query = """
            SELECT s.*, a.title, a.url, a.source, a.category, a.published_at
            FROM summaries s
            JOIN articles a ON s.article_id = a.id
            ORDER BY s.created_at DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, (limit, skip))

    rows = cursor.fetchall()
    conn.close()

    summaries = []
    for row in rows:
        summary = dict(row)
        summary["interest_tags"] = json.loads(summary.get("interest_tags", "[]"))
        summaries.append(summary)

    return summaries


def create_or_update_preferences(preferences_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update user preferences"""
    conn = get_connection()
    cursor = conn.cursor()

    interests_json = json.dumps(preferences_data.get("interests", []))
    keywords_json = json.dumps(preferences_data.get("keywords_to_exclude", []))
    sources_json = json.dumps(preferences_data.get("preferred_sources", []))

    cursor.execute("""
        INSERT OR REPLACE INTO user_preferences (
            id, interests, age_range, demographic,
            keywords_to_exclude, preferred_sources
        ) VALUES (1, ?, ?, ?, ?, ?)
    """, (
        interests_json,
        preferences_data.get("age_range", "25-35"),
        preferences_data.get("demographic", "International Masters Student in USA"),
        keywords_json,
        sources_json
    ))

    conn.commit()
    conn.close()

    logger.info("✅ Preferences updated")
    return preferences_data


def get_preferences() -> Optional[Dict[str, Any]]:
    """Get user preferences"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_preferences WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        prefs = dict(row)
        prefs["interests"] = json.loads(prefs.get("interests", "[]"))
        prefs["keywords_to_exclude"] = json.loads(prefs.get("keywords_to_exclude", "[]"))
        prefs["preferred_sources"] = json.loads(prefs.get("preferred_sources", "[]"))
        return prefs

    return None


def create_digest(digest_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a digest record"""
    conn = get_connection()
    cursor = conn.cursor()

    content_json = json.dumps(digest_data.get("digest_content", {}))

    cursor.execute("""
        INSERT INTO digests (
            digest_type, summaries_count, digest_content
        ) VALUES (?, ?, ?)
    """, (
        digest_data.get("digest_type"),
        digest_data.get("summaries_count", 0),
        content_json
    ))

    conn.commit()
    digest_id = cursor.lastrowid
    conn.close()

    logger.info(f"✅ Digest created: {digest_id}")
    return {"id": digest_id, **digest_data}


def get_digests_by_type(digest_type: str, limit: int = 10) -> List[Dict]:
    """Get digests by type (morning/evening)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM digests
        WHERE digest_type = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (digest_type, limit))

    rows = cursor.fetchall()
    conn.close()

    digests = []
    for row in rows:
        digest = dict(row)
        digest["digest_content"] = json.loads(digest.get("digest_content", "{}"))
        digests.append(digest)

    return digests


# Saved Articles Functions
def save_article(article_url: str, article_data: Dict[str, Any]) -> bool:
    """Save an article to favorites"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if already saved
        cursor.execute("SELECT id FROM saved_articles WHERE article_url = ?", (article_url,))
        if cursor.fetchone():
            conn.close()
            return False  # Already saved

        # Insert saved article
        cursor.execute("""
            INSERT INTO saved_articles
            (article_url, article_title, article_source, article_category, article_summary, saved_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            article_url,
            article_data.get('title', '')[:500],
            article_data.get('source', ''),
            article_data.get('category', ''),
            article_data.get('summary', '')[:1000],
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()
        logger.info(f"❤️ Article saved: {article_data.get('title', 'Unknown')[:50]}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to save article: {e}")
        return False


def get_saved_articles(days_back: int = 7) -> List[Dict]:
    """Get saved articles from last N days"""
    try:
        from datetime import timedelta

        conn = get_connection()
        cursor = conn.cursor()

        # Calculate date cutoff
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        cursor.execute("""
            SELECT * FROM saved_articles
            WHERE saved_at >= ?
            ORDER BY saved_at DESC
        """, (cutoff_date,))

        rows = cursor.fetchall()
        conn.close()

        articles = []
        for row in rows:
            articles.append(dict(row))

        return articles

    except Exception as e:
        logger.error(f"❌ Failed to get saved articles: {e}")
        return []


def remove_saved_article(article_url: str) -> bool:
    """Remove article from saved"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM saved_articles WHERE article_url = ?", (article_url,))
        conn.commit()
        conn.close()

        logger.info(f"🗑️ Article removed from saved")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to remove saved article: {e}")
        return False


def is_article_saved(article_url: str) -> bool:
    """Check if article is saved"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM saved_articles WHERE article_url = ?", (article_url,))
        result = cursor.fetchone()
        conn.close()

        return result is not None

    except Exception as e:
        logger.error(f"❌ Failed to check saved status: {e}")
        return False


def cleanup_old_saved_articles(days: int = 7) -> int:
    """Delete saved articles older than N days"""
    try:
        from datetime import timedelta

        conn = get_connection()
        cursor = conn.cursor()

        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("DELETE FROM saved_articles WHERE saved_at < ?", (cutoff_date,))
        conn.commit()

        deleted_count = cursor.rowcount
        conn.close()

        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} saved articles older than {days} days")

        return deleted_count

    except Exception as e:
        logger.error(f"❌ Failed to cleanup old articles: {e}")
        return 0


# Initialize database on import
if __name__ == "__main__":
    init_db()
    logger.info(f"Database file: {DB_PATH}")
