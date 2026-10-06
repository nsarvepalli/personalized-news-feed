from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from config import get_settings
from schemas import (
    ArticleResponse, ArticleCreate,
    SummaryResponse, SummaryCreate,
    UserPreferenceResponse, UserPreferenceCreate
)
from services.news_fetcher import NewsAggregator
from services.summarizer import ArticleSummarizer
import database_streamlit as db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Personalized News Feed API",
    description="Aggregates and summarizes news articles with AI",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase
settings = get_settings()

# Initialize news aggregator
news_aggregator = NewsAggregator(settings)
logger.info("✅ News aggregator initialized")

# Initialize summarizer
try:
    summarizer = ArticleSummarizer(settings.openai_api_key)
    logger.info("✅ Article summarizer initialized")
except Exception as e:
    logger.warning(f"⚠️  Summarizer initialization failed: {e}")
    summarizer = None

# Initialize SQLite database
try:
    db.init_db()
    logger.info("✅ Database initialized (SQLite)")

    # Cleanup old saved articles on startup (keep only last 7 days)
    deleted = db.cleanup_old_saved_articles(days=7)
    if deleted > 0:
        logger.info(f"🧹 Startup cleanup: Removed {deleted} old saved articles")
except Exception as e:
    logger.warning(f"⚠️  Database initialization failed: {e}")


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "Personalized News Feed API",
        "status": "🟢 Running",
        "version": "0.1.0"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "news_aggregator": "ready"
    }


# Articles endpoints
@app.get("/articles", tags=["Articles"])
async def list_articles(skip: int = 0, limit: int = 20, source: str = None):
    """Get all articles from database"""
    try:
        articles = db.get_articles(skip=skip, limit=limit, source=source)
        return {
            "status": "success",
            "total_articles": len(articles),
            "articles": articles
        }
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/articles", tags=["Articles"])
async def create_article(article: ArticleCreate):
    """Create a new article in database"""
    try:
        result = db.create_article(article.model_dump())
        if result:
            return {
                "status": "success",
                "article": result
            }
        else:
            raise HTTPException(status_code=409, detail="Article already exists")
    except Exception as e:
        logger.error(f"❌ Failed to create article: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Summaries endpoints
@app.get("/summaries", tags=["Summaries"])
async def list_summaries(skip: int = 0, limit: int = 20):
    """Get all article summaries from database"""
    try:
        summaries = db.get_summaries(skip=skip, limit=limit)
        return {
            "status": "success",
            "total_summaries": len(summaries),
            "summaries": summaries
        }
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summaries/by-interest", tags=["Summaries"])
async def get_summaries_by_interest(interest: str, skip: int = 0, limit: int = 20):
    """Get summaries filtered by interest from database"""
    try:
        summaries = db.get_summaries(skip=skip, limit=limit, interest=interest)
        return {
            "status": "success",
            "total_summaries": len(summaries),
            "interest": interest,
            "summaries": summaries
        }
    except Exception as e:
        logger.error(f"❌ Database query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/digests/morning", tags=["Digests"])
async def get_morning_digest():
    """Get latest morning digest"""
    try:
        digests = db.get_digests_by_type("morning", limit=1)
        if digests:
            return {
                "status": "success",
                "digest": digests[0]
            }
        return {"status": "success", "digest": None}
    except Exception as e:
        logger.error(f"❌ Failed to fetch digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/digests/evening", tags=["Digests"])
async def get_evening_digest():
    """Get latest evening digest"""
    try:
        digests = db.get_digests_by_type("evening", limit=1)
        if digests:
            return {
                "status": "success",
                "digest": digests[0]
            }
        return {"status": "success", "digest": None}
    except Exception as e:
        logger.error(f"❌ Failed to fetch digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# User preferences endpoints
@app.get("/preferences", tags=["Preferences"])
async def get_preferences():
    """Get user preferences from database"""
    try:
        prefs = db.get_preferences()
        if prefs:
            return {
                "status": "success",
                "preferences": prefs
            }
        return {
            "status": "success",
            "preferences": None,
            "message": "No preferences set yet"
        }
    except Exception as e:
        logger.error(f"❌ Failed to fetch preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/preferences", tags=["Preferences"])
async def update_preferences(prefs: UserPreferenceCreate):
    """Update user preferences in database"""
    try:
        result = db.create_or_update_preferences(prefs.model_dump())
        return {
            "status": "success",
            "preferences": result
        }
    except Exception as e:
        logger.error(f"❌ Failed to update preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# News Fetcher endpoints (for testing)
@app.post("/fetch/articles", tags=["Fetch"])
async def fetch_articles(days_back: int = 1, sources: str = None, interests: str = None):
    """
    Fetch articles from specified sources

    Args:
        days_back: Number of days to look back
        sources: Comma-separated sources (nyt, bloomberg, washingtonpost)
                 If None, fetches from all configured sources
        interests: Comma-separated interests to filter articles (e.g., business, ai, technology)

    This is a test endpoint to verify news fetchers are working.
    In production, this would be called by GitHub Actions on a schedule.
    """
    # MINIMAL DEBUG - Write raw request params to file IMMEDIATELY
    import os
    import sys
    cwd = os.getcwd()
    main_file = os.path.abspath(__file__)
    main_dir = os.path.dirname(main_file)
    debug_path = os.path.join(main_dir, "debug.log")
    sys.stderr.write(f"[DEBUG] CWD={cwd}, __file__={main_file}, debug_path={debug_path}\n")
    try:
        with open(debug_path, "a") as f:
            f.write(f"\n[ENDPOINT HIT] sources param = {repr(sources)}\n")
            f.write(f"[DEBUG] __file__={main_file}, debug_path={debug_path}\n")
            f.flush()
        sys.stderr.write(f"[DEBUG] Successfully wrote to {debug_path}\n")
    except Exception as e:
        sys.stderr.write(f"ERROR writing debug.log: {e}\n")

    try:
        # Parse sources
        sources_list = None
        if sources:
            sources_list = [s.strip().lower() for s in sources.split(",") if s.strip()]
            logger.info(f"RAW SOURCES RECEIVED: {sources}")
            logger.info(f"PARSED SOURCES LIST: {sources_list}")
        else:
            logger.info("📰 Fetching from all available sources (sources param is None/empty)")

        # Parse interests
        interests_list = None
        if interests:
            interests_list = [i.strip().lower() for i in interests.split(",") if i.strip()]
            logger.info(f"🎯 INTERESTS TO FILTER: {interests_list}")

        articles = await news_aggregator.fetch_all(days_back=days_back, sources=sources_list, interests=interests_list)

        # Log final results
        with open(debug_path, "a") as f:
            f.write(f"[RESULT] Got {len(articles)} articles\n")
            if articles:
                sources_in_results = set(a.source for a in articles)
                f.write(f"[SOURCES] {sources_in_results}\n")
            f.flush()

        logger.info(f"✅ FINAL ARTICLES COUNT: {len(articles)}")
        if articles:
            sources_in_results = set(a.source for a in articles)
            logger.info(f"✅ SOURCES IN RESULTS: {sources_in_results}")

        logger.info(f"✅ Fetch complete - {len(articles)} articles from {sources_list or 'all sources'}")

        return {
            "status": "success",
            "total_articles": len(articles),
            "articles": articles,
            "sources_requested": sources_list or "all",
            "message": f"Fetched {len(articles)} articles from {sources_list or 'all configured sources'}"
        }
    except Exception as e:
        logger.error(f"❌ Fetch articles failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {str(e)}")


@app.get("/fetch/cached", tags=["Fetch"])
async def get_cached_articles():
    """Get last fetched articles from cache"""
    articles = news_aggregator.get_cached_articles()
    return {
        "status": "success",
        "total_articles": len(articles),
        "articles": articles
    }


# Saved Articles endpoints
@app.post("/articles/save", tags=["Saved Articles"])
async def save_article(url: str, title: str = "", source: str = "", category: str = "", summary: str = ""):
    """Save an article to favorites"""
    try:
        article_data = {
            "title": title,
            "source": source,
            "category": category,
            "summary": summary
        }
        success = db.save_article(url, article_data)

        return {
            "status": "success" if success else "already_saved",
            "saved": success,
            "message": "Article saved successfully" if success else "Article already saved"
        }
    except Exception as e:
        logger.error(f"❌ Failed to save article: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save article: {str(e)}")


@app.get("/articles/saved", tags=["Saved Articles"])
async def get_saved_articles_endpoint(days_back: int = 7):
    """Get saved articles from last N days"""
    try:
        articles = db.get_saved_articles(days_back=days_back)
        logger.info(f"✅ Retrieved {len(articles)} saved articles from database")

        if articles:
            logger.info(f"📄 Sample article: {articles[0]}")

        return {
            "status": "success",
            "total_saved": len(articles),
            "days_back": days_back,
            "articles": articles
        }
    except Exception as e:
        logger.error(f"❌ Failed to get saved articles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get saved articles: {str(e)}")


@app.delete("/articles/save", tags=["Saved Articles"])
async def remove_saved_article(url: str):
    """Remove article from saved"""
    try:
        success = db.remove_saved_article(url)

        return {
            "status": "success" if success else "error",
            "removed": success,
            "message": "Article removed from saved" if success else "Failed to remove article"
        }
    except Exception as e:
        logger.error(f"❌ Failed to remove saved article: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove saved article: {str(e)}")


@app.get("/articles/save/check", tags=["Saved Articles"])
async def check_saved_article(url: str):
    """Check if article is saved"""
    try:
        is_saved = db.is_article_saved(url)

        return {
            "status": "success",
            "url": url,
            "is_saved": is_saved
        }
    except Exception as e:
        logger.error(f"❌ Failed to check saved status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check saved status: {str(e)}")


@app.post("/articles/cleanup", tags=["Saved Articles"])
async def cleanup_saved_articles_endpoint(days: int = 7):
    """Manually cleanup saved articles older than N days"""
    try:
        deleted = db.cleanup_old_saved_articles(days=days)

        return {
            "status": "success",
            "deleted_count": deleted,
            "message": f"Deleted {deleted} articles older than {days} days"
        }
    except Exception as e:
        logger.error(f"❌ Failed to cleanup articles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup articles: {str(e)}")


# Database Query Endpoints (deferred - SQLAlchemy compatibility issue)
# TODO: Implement after database layer is fixed
# - GET /articles/db
# - GET /summaries/db


# Summarizer endpoints
@app.post("/summarize/articles", tags=["Summarize"])
async def summarize_articles(
    days_back: int = 1,
    interests: str = "business,education,ai,upskilling"
):
    """
    Fetch articles and summarize them (in-memory, not saved to database)

    Args:
        days_back: Number of days to look back
        interests: Comma-separated interests

    Returns:
        Articles with summaries, tags, and relevance scores
    """
    if not summarizer:
        raise HTTPException(status_code=500, detail="Summarizer not initialized")

    try:
        # Fetch articles
        articles = await news_aggregator.fetch_all(days_back=days_back)

        if not articles:
            return {
                "status": "success",
                "total_articles": 0,
                "articles": [],
                "message": "No articles found to summarize"
            }

        # Summarize articles
        summarized = []
        user_interests = [i.strip() for i in interests.split(",") if i.strip()]

        for article in articles:
            try:
                # Summarize
                summary_text, tags = summarizer.summarize(
                    title=article.title,
                    description=article.description,
                    content=article.content,
                    interests=user_interests
                )

                # Calculate relevance
                relevance_score = summarizer.calculate_relevance_score(
                    article_title=article.title,
                    article_tags=tags,
                    user_interests=user_interests
                )

                # Build response
                summarized.append({
                    "title": article.title,
                    "description": article.description,
                    "url": article.url,
                    "source": article.source,
                    "published_at": article.published_at.isoformat() if hasattr(article.published_at, 'isoformat') else str(article.published_at),
                    "category": article.category,
                    "image_url": article.image_url,
                    "summary": summary_text,
                    "tags": tags,
                    "relevance_score": relevance_score
                })

            except Exception as e:
                logger.error(f"❌ Failed to process article: {e}")
                continue

        # Sort by relevance score
        summarized = sorted(summarized, key=lambda x: x.get("relevance_score", 0), reverse=True)

        return {
            "status": "success",
            "total_articles": len(summarized),
            "interests": user_interests,
            "articles": summarized,
            "message": f"Successfully summarized {len(summarized)} articles"
        }

    except Exception as e:
        logger.error(f"❌ Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@app.post("/summarize/cached", tags=["Summarize"])
async def summarize_cached_articles(interests: str = "business,education,ai,upskilling", save_to_db: bool = True):
    """
    Summarize articles from cache and optionally save to database

    Args:
        interests: Comma-separated interests
        save_to_db: Whether to save articles and summaries to database

    Returns:
        Cached articles with summaries, tags, and relevance scores
    """
    if not summarizer:
        raise HTTPException(status_code=500, detail="Summarizer not initialized")

    try:
        articles = news_aggregator.get_cached_articles()

        if not articles:
            return {
                "status": "success",
                "total_articles": 0,
                "articles": [],
                "message": "No cached articles to summarize"
            }

        # Convert to dict format
        articles_dict = [
            {
                "title": a.title,
                "description": a.description,
                "content": a.content,
                "url": a.url,
                "source": a.source,
                "source_id": getattr(a, 'source_id', ''),
                "published_at": a.published_at.isoformat() if hasattr(a.published_at, 'isoformat') else str(a.published_at),
                "category": a.category,
                "image_url": a.image_url,
                "article_type": getattr(a, 'article_type', 'News')
            }
            for a in articles
        ]

        # Parse interests
        user_interests = [i.strip() for i in interests.split(",") if i.strip()]

        # Summarize
        logger.info(f"📝 Summarizing {len(articles_dict)} cached articles")
        summarized = summarizer.batch_summarize(articles_dict, user_interests)

        # Save to database if requested
        if save_to_db:
            for i, article_data in enumerate(articles_dict):
                try:
                    # Save article if not exists
                    if not db.article_exists(article_data["url"]):
                        db.create_article(article_data)

                    # Save summary for this article
                    if i < len(summarized):
                        summary_data = {
                            "article_id": i + 1,  # Will be updated after article fetch
                            "summary_text": summarized[i].get("summary", ""),
                            "interest_tags": summarized[i].get("tags", []),
                            "relevance_score": summarized[i].get("relevance_score", 0.0),
                            "model_used": "gpt-3.5-turbo"
                        }
                        db.create_summary(summary_data)
                except Exception as e:
                    logger.warning(f"⚠️  Failed to save article/summary to DB: {e}")
                    continue

        # Sort by relevance score
        summarized = sorted(summarized, key=lambda x: x.get("relevance_score", 0), reverse=True)

        return {
            "status": "success",
            "total_articles": len(summarized),
            "interests": user_interests,
            "articles": summarized,
            "saved_to_db": save_to_db,
            "message": f"Successfully summarized {len(summarized)} cached articles"
        }

    except Exception as e:
        logger.error(f"❌ Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Changed to 8001 to avoid port conflict
        reload=False  # DISABLED for debugging - print statements need single process
    )
