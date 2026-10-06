# 🚀 Quick Fix: Use NewsAPI for Reliable Articles

## Why NewsAPI?
- ✅ Works reliably (no selectors to break)
- ✅ 150+ news sources included
- ✅ Free tier: 100 requests/day
- ✅ Simple REST API
- ✅ No auth hassles like Bloomberg

## Setup (2 minutes)

### 1. Get Free API Key
- Go to https://newsapi.org/
- Sign up (free)
- Copy your API key

### 2. Add to `.env`
```
NEWSAPI_KEY=your_key_here
```

### 3. Install package
```bash
pip install newsapi
```

### 4. Add to `requirements.txt`
```
newsapi==0.1.2
```

---

## Create NewsAPI Fetcher

Create file: `backend/services/newsapi_fetcher.py`

```python
import logging
from typing import List
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from schemas import ArticleCreate

logger = logging.getLogger(__name__)

class NewsAPIFetcher:
    """Fetcher for NewsAPI - covers 150+ news sources"""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("NewsAPI key required")
        self.client = NewsApiClient(api_key=api_key)
    
    async def fetch(self, days_back: int = 1, query: str = None) -> List[ArticleCreate]:
        """
        Fetch articles from NewsAPI
        
        Args:
            days_back: Days back to fetch (max 30)
            query: Search query (e.g., "technology business")
        
        Returns:
            List of ArticleCreate objects
        """
        articles = []
        
        try:
            query = query or "business technology innovation startup"
            
            logger.info(f"🔍 Fetching from NewsAPI: '{query}'")
            
            # Get top headlines from multiple sources
            response = self.client.get_everything(
                q=query,
                sort_by="publishedAt",
                language="en",
                page_size=50,
            )
            
            if response.get("status") != "ok":
                logger.error(f"NewsAPI error: {response.get('message')}")
                return []
            
            articles_data = response.get("articles", [])
            logger.info(f"✅ NewsAPI returned {len(articles_data)} articles")
            
            for article_data in articles_data:
                try:
                    published = article_data.get("publishedAt", "")
                    if published:
                        published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    else:
                        published_at = datetime.utcnow()
                    
                    article = ArticleCreate(
                        title=article_data.get("title", "")[:500],
                        description=article_data.get("description", "")[:500],
                        url=article_data.get("url", ""),
                        source=article_data.get("source", {}).get("name", "NewsAPI").lower().replace(" ", ""),
                        source_id=article_data.get("url", "").split("/")[-1],
                        category=article_data.get("category", "General"),
                        published_at=published_at,
                        image_url=article_data.get("urlToImage"),
                        authors=[article_data.get("author", "")],
                        content=article_data.get("content", "")[:1000],
                        article_type="News"
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"NewsAPI fetch failed: {e}")
            return []
```

---

## Update NewsAggregator

In `backend/services/news_fetcher.py`, add NewsAPI fetcher:

```python
from services.newsapi_fetcher import NewsAPIFetcher

class NewsAggregator:
    def __init__(self, config=None):
        self.config = config or get_settings()
        self.nyt_fetcher = NYTFetcher(self.config.nyt_api_key)
        
        # Add NewsAPI as reliable fallback
        try:
            self.newsapi_fetcher = NewsAPIFetcher(self.config.newsapi_key)
            logger.info("✅ NewsAPI fetcher initialized")
        except:
            self.newsapi_fetcher = None
            logger.warning("⚠️  NewsAPI not configured")
        
        self.washingtonpost_fetcher = WashingtonPostFetcher()
        self.bloomberg_fetcher = None
        # ... rest of init
```

Then in `fetch_all()`:

```python
# Add NewsAPI if requested
if "newsapi" in sources:
    if self.newsapi_fetcher:
        tasks.append(("newsapi", self.newsapi_fetcher.fetch(days_back=days_back)))
        logger.info("📰 Added NewsAPI fetcher")
```

---

## Update Frontend

In `frontend/app.py` (line 50), add "NewsAPI" as option:

```python
sources = st.multiselect(
    "Select Sources",
    ["NYT", "NewsAPI", "Bloomberg", "Washington Post"],
    default=["NYT"],
    help="Choose which news sources to include"
)
```

---

## Test It

```bash
# Test fetcher directly
python backend/test_fetchers.py

# Run the app
streamlit run frontend/app.py
```

---

## Result

Now you have:
- ✅ **NYT** - Reliable API
- ✅ **NewsAPI** - 150+ sources, super reliable
- ⚠️ **Bloomberg** - Optional (fragile, may not work)
- ⚠️ **Washington Post** - Optional (fragile, may not work)

This ensures you always have working articles from at least 2 sources!

---

## Pricing

**NewsAPI Free Tier**: 100 requests/day
- Perfect for testing
- ~20 articles per request
- = 2000 articles/day maximum

**NewsAPI Premium**: $45-449/month
- Unlimited requests
- Same API
- For production use

For now, free tier is plenty for development!
