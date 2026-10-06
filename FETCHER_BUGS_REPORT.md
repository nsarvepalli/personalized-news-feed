# 🐛 News Fetcher Defects Report

## Issues Found

### 🔴 CRITICAL: Washington Post RSS Feeds Not Working

**File**: `backend/services/news_fetcher.py` (line 167-171)

**Problem**: 
```python
self.feed_urls = [
    "https://feeds.washingtonpost.com/rss/business",
    "https://feeds.washingtonpost.com/rss/technology"
]
```

**Why it's broken**:
- Washington Post removed most public RSS feeds or moved them behind authentication walls
- These URLs likely return empty/invalid content
- Even if you have a subscription, RSS feeds may require auth headers

**Result**: 0 articles fetched from Washington Post

**Fix Options**:
1. **Use alternative RSS feeds** (Reuters, BBC, etc.)
   ```python
   self.feed_urls = [
       "http://feeds.reuters.com/reuters/businessNews",
       "http://feeds.bbc.co.uk/news/rss.xml",
   ]
   ```

2. **Use NewsAPI** instead (free, supports 150+ sources)
   - Add to `.env`: `NEWSAPI_KEY=your_key` (get free key at newsapi.org)
   - Fetch from multiple sources: Reuters, Bloomberg, WSJ, etc.

3. **Add authentication headers** if you know the correct RSS URLs

---

### 🔴 CRITICAL: Bloomberg Selenium Login Broken

**File**: `backend/services/news_fetcher.py` (line 278-330)

**Problem**: 
- Bloomberg website structure changes frequently
- Selectors for login button, email field, password field are hardcoded
- When structure changes, login fails silently
- Article scraping selectors are also outdated

**Current selectors that may not work**:
```python
# Login button selector
"//a[contains(text(), 'Log in')] | //button[contains(text(), 'Log in')]"

# Email field
By.NAME, "email"

# Password field  
By.NAME, "password"

# Article selector
soup.find_all("a", {"data-test": "internal-link"})
```

**Why it fails**:
- Bloomberg.com HTML changes regularly
- These CSS/XPath selectors no longer match
- Selenium gets stuck or times out during login

**Result**: 0 articles fetched from Bloomberg

**Fix Options**:
1. **Use Bloomberg API** (if you have enterprise access)
2. **Use Playwright instead of Selenium** (more robust)
3. **Use web scraping library** like Apify (handles dynamic content)
4. **Add manual login once, then use session cookies**
5. **Use alternative financial news sources** that don't require login:
   - Reuters
   - Financial Times RSS
   - Yahoo Finance
   - MarketWatch

---

### 🟡 MODERATE: Article Scraping Selectors Fragile

**File**: `backend/services/news_fetcher.py` (line 361-391)

**Current issue**:
```python
article_elements = soup.find_all("a", {"data-test": "internal-link"})
```

**Fix applied**: Added 4 fallback selectors to find articles. Better, but still fragile.

**Underlying problem**: Relying on HTML structure for dynamic websites = will break when site updates.

---

## 🔧 Immediate Fixes Applied

✅ Added detailed error logging to Bloomberg login
✅ Added 4 fallback selectors for Bloomberg articles  
✅ Added response validation for Washington Post
✅ Added logging to show which selectors are matching

---

## 📋 Action Plan

### Step 1: Test Current State
```bash
cd backend
python test_fetchers.py
```

This will show you:
- ✅ NYT: Working or not
- ✅ Washington Post: Working or not
- ✅ Bloomberg: Working or not
- 📋 Specific errors for each

### Step 2: Based on Results

**If NYT works but Washington Post/Bloomberg don't:**

Option A (RECOMMENDED): Use NewsAPI
- Free tier: 100 requests/day (enough for testing)
- Paid tier: Unlimited, many sources
- Super reliable, no selectors to break
- Code: Simple API calls, not web scraping

Option B: Replace Washington Post with Reuters/BBC RSS
- Free public RSS feeds
- Reliable long-term
- Easy to implement

Option C: Get enterprise Bloomberg access
- Bloomberg terminal has API
- Not free, but official
- Most reliable

---

## 🚀 Quick Fix: Use NewsAPI Instead

Add to `requirements.txt`:
```
newsapi==0.1.2
```

Create `backend/services/newsapi_fetcher.py`:
```python
from newsapi import NewsApiClient

class NewsAPIFetcher:
    def __init__(self, api_key):
        self.client = NewsApiClient(api_key=api_key)
    
    async def fetch(self, days_back: 1, query: "business ai technology"):
        articles = self.client.get_top_headlines(q=query, language="en")
        # Convert to ArticleCreate format
        # Return list
```

Then update `news_fetcher.py` to use NewsAPI for sources that don't have working APIs.

---

## 🧪 Testing

Run the debug script to identify exact issues:
```bash
python test_fetchers.py
```

Watch the logs carefully for:
- ❌ Login failed errors
- ❌ Selector not found messages
- ❌ HTTP errors from RSS feeds
- ✅ Number of articles fetched per source

---

## 📞 Summary

| Source | Status | Root Cause | Fix Difficulty |
|--------|--------|-----------|-----------------|
| NYT API | Should work | None | ✅ Easy |
| Washington Post | 🔴 Broken | RSS feeds blocked | 🟡 Medium |
| Bloomberg | 🔴 Broken | Selectors outdated | 🔴 Hard |

**Recommendation**: Switch to NewsAPI + Reuters RSS for reliable, maintainable news aggregation.
