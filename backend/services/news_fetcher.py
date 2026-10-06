# News Fetcher Service
# Hybrid approach: NYT API + Bloomberg Web Scraping

import logging
import requests
from typing import List, Optional
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import asyncio
import time
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from schemas import ArticleCreate
from config import get_settings

logger = logging.getLogger(__name__)


class NYTFetcher:
    """New York Times API fetcher"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.base_url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"

    async def fetch(
        self,
        days_back: int = 1,
        query: Optional[str] = None,
        include_editorial: bool = True
    ) -> List[ArticleCreate]:
        """
        Fetch articles from NYT API (including news and editorial)

        Args:
            days_back: Number of days to look back
            query: Search query (default: business, education, technology)
            include_editorial: Include editorial/opinion articles

        Returns:
            List of ArticleCreate objects
        """
        if not self.api_key:
            logger.warning("❌ NYT API key not configured")
            return []

        articles = []
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # Default to business/education/AI/upskilling related topics
            query = query or "business OR education OR artificial intelligence OR technology"

            params = {
                "q": query,
                "api-key": self.api_key,
                "sort": "newest",
                "begin_date": start_date.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d"),
                "page": 0
            }

            logger.info(f"🔍 Fetching NYT articles: {query}")
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "OK":
                logger.error(f"❌ NYT API error: {data.get('message')}")
                return []

            docs = data.get("response", {}).get("docs", [])
            logger.info(f"✅ NYT: Fetched {len(docs)} articles")

            for doc in docs:
                try:
                    # Check document type
                    doc_type = doc.get("type_of_material", "").lower()
                    news_desk = doc.get("news_desk", "").lower()

                    # Include news articles
                    is_news = doc_type in ["news", "article", "blog"] or "business" in news_desk or "technology" in news_desk

                    # Include editorial/opinion if requested
                    is_editorial = doc_type in ["editorial", "op-ed", "opinion", "column"] or "opinion" in news_desk

                    if not (is_news or (include_editorial and is_editorial)):
                        continue

                    # Extract image safely
                    image_url = None
                    multimedia = doc.get("multimedia", [])
                    if isinstance(multimedia, list):
                        for media in multimedia:
                            if isinstance(media, dict) and media.get("type") == "image":
                                image_url = f"https://www.nytimes.com/{media.get('url', '')}"
                                break

                    # Parse published date
                    try:
                        pub_date = date_parser.parse(doc.get("pub_date", datetime.utcnow().isoformat()))
                    except:
                        pub_date = datetime.utcnow()

                    # Extract authors safely
                    authors = []
                    byline = doc.get("byline")
                    if byline:
                        if isinstance(byline, dict):
                            author_name = byline.get("original", "")
                            if author_name:
                                authors = [author_name]
                        elif isinstance(byline, str):
                            authors = [byline]

                    # Extract title safely
                    headline = doc.get("headline", {})
                    title = headline.get("main", "") if isinstance(headline, dict) else str(headline)

                    # Determine article type
                    article_type = "Editorial" if is_editorial else "News"

                    article = ArticleCreate(
                        title=title,
                        description=doc.get("lead_paragraph", ""),
                        url=doc.get("web_url", ""),
                        source="nyt",
                        source_id=doc.get("_id", ""),
                        category=doc.get("section_name", "General"),
                        published_at=pub_date,
                        image_url=image_url,
                        authors=authors,
                        content=doc.get("abstract", ""),
                        article_type=article_type  # Add article type
                    )
                    articles.append(article)

                except Exception as e:
                    logger.warning(f"⚠️  Failed to parse NYT article: {e}")
                    continue

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ NYT API request failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching from NYT: {e}")

        return articles


class WashingtonPostFetcher:
    """Washington Post fetcher using web scraping (for subscribers)"""

    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.washingtonpost.com"
        # Set user agent to avoid blocking
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    async def fetch(self, days_back: int = 1) -> List[ArticleCreate]:
        """
        Fetch articles from Washington Post by scraping (works for subscribers)

        Args:
            days_back: Number of days to look back

        Returns:
            List of ArticleCreate objects
        """
        articles = []

        # Washington Post article sections to scrape
        sections = [
            "/politics",
            "/business",
            "/technology",
            "/world"
        ]

        try:
            logger.info("🔍 Fetching Washington Post articles...")

            for section in sections:
                try:
                    url = f"{self.base_url}{section}"
                    logger.info(f"   Scraping {section}...")

                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()

                    if not response.text:
                        logger.warning(f"⚠️  Empty response from {section}")
                        continue

                    # Parse with BeautifulSoup
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Washington Post article selectors (updated for current site)
                    # Look for article links in main content
                    articles_found = 0

                    # Try selector 1: articles in article containers
                    article_links = soup.find_all("a", {
                        "data-link-type": "article"
                    })

                    if not article_links:
                        # Try selector 2: generic article links
                        article_links = soup.find_all("a", href=lambda x: x and "/story/" in x)

                    if not article_links:
                        # Try selector 3: article heading links
                        article_links = soup.find_all("a", href=lambda x: x and x.startswith(("/202", self.base_url)))

                    logger.info(f"   Found {len(article_links)} links in {section}")

                    for link in article_links[:15]:  # Limit 15 per section
                        try:
                            href = link.get("href", "")
                            title = link.get_text(strip=True)

                            # Skip if no title or URL
                            if not title or len(title) < 5:
                                continue
                            if not href:
                                continue

                            # Make absolute URL
                            if href.startswith("/"):
                                href = f"{self.base_url}{href}"
                            elif not href.startswith("http"):
                                continue

                            # Skip non-article URLs
                            if "facebook.com" in href or "twitter.com" in href:
                                continue

                            article = ArticleCreate(
                                title=title,  # Full title preserved
                                description=title,  # WashPo doesn't expose descriptions in HTML
                                url=href,
                                source="washingtonpost",
                                source_id=href.split("/")[-1][:50],
                                category=section.strip("/").title(),
                                published_at=datetime.utcnow(),
                                image_url=None,
                                authors=["Washington Post"],
                                content=title,  # Full content preserved
                                article_type="News"
                            )
                            articles.append(article)
                            articles_found += 1

                        except Exception as e:
                            logger.warning(f"   ⚠️  Parse error: {e}")
                            continue

                    logger.info(f"   ✅ {section}: {articles_found} articles")

                except requests.exceptions.RequestException as e:
                    logger.warning(f"⚠️  Failed to fetch {section}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"⚠️  Error scraping {section}: {e}")
                    continue

            logger.info(f"✅ Washington Post: Total {len(articles)} articles")

        except Exception as e:
            logger.error(f"❌ Washington Post fetcher error: {e}")

        return articles


class BloombergFetcher:
    """Bloomberg web scraper using Selenium - CUSTOMIZED FOR LIVE WEBSITE"""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.driver = None
        self.base_url = "https://www.bloomberg.com"

    def _init_driver(self):
        """Initialize Chrome WebDriver with stealth options"""
        try:
            options = webdriver.ChromeOptions()
            # Anti-detection measures
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Chrome WebDriver initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize WebDriver: {e}")
            raise

    def _login(self) -> bool:
        """Login to Bloomberg with current website selectors"""
        try:
            logger.info("🔐 Logging into Bloomberg.com...")

            # Navigate to login page directly (faster than clicking)
            self.driver.get(f"{self.base_url}/account/login")
            logger.info("✅ Navigated to login page")
            time.sleep(3)

            # Find and fill email field (updated selector for current Bloomberg)
            try:
                email_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[id*='email'], input[placeholder*='Email']"))
                )
                logger.info("📧 Found email field")
                email_input.send_keys(self.email)
                time.sleep(1)
            except TimeoutException:
                logger.error("❌ Email field timeout - page structure may have changed")
                logger.info("   Trying alternative selectors...")
                try:
                    email_input = self.driver.find_element(By.XPATH, "//input[@type='email' or @type='text' and @name='email']")
                    email_input.send_keys(self.email)
                    logger.info("✅ Email entered (via fallback)")
                except:
                    logger.error("❌ Could not find email field with any selector")
                    return False

            # Find and fill password field
            try:
                password_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                )
                logger.info("🔑 Found password field")
                password_input.send_keys(self.password)
                time.sleep(1)
            except TimeoutException:
                logger.error("❌ Password field timeout")
                return False

            # Find and click submit button
            try:
                # Try multiple submit button selectors
                submit_btn = None
                selectors = [
                    "button[type='submit']",
                    "button[id*='submit']",
                    "button:contains('Log In')",
                    "//button[contains(text(), 'Log In')]",
                    "//button[contains(text(), 'Sign In')]"
                ]

                for selector in selectors:
                    try:
                        if selector.startswith("//"):
                            submit_btn = self.driver.find_element(By.XPATH, selector)
                        else:
                            submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if submit_btn:
                            logger.info(f"✅ Found submit button: {selector}")
                            break
                    except:
                        continue

                if not submit_btn:
                    logger.error("❌ Submit button not found")
                    return False

                submit_btn.click()
                logger.info("✅ Clicked login button")

            except Exception as e:
                logger.error(f"❌ Could not click submit button: {e}")
                return False

            # Wait for page to load (check for dashboard or articles)
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )
                logger.info("✅ Login successful - page loaded")
                return True
            except TimeoutException:
                # Check if we're at least on a Bloomberg page
                current_url = self.driver.current_url
                logger.warning(f"⚠️  Page load timeout, but at URL: {current_url}")
                if "bloomberg" in current_url:
                    logger.info("✅ Appears to be logged in (at Bloomberg URL)")
                    return True
                else:
                    logger.error("❌ Not at Bloomberg URL after login")
                    return False

        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False

    async def fetch(self, days_back: int = 1) -> List[ArticleCreate]:
        """
        Fetch articles from Bloomberg after login

        Args:
            days_back: Number of days to look back

        Returns:
            List of ArticleCreate objects
        """
        if not self.email or not self.password:
            logger.warning("⚠️  Bloomberg credentials not configured")
            return []

        articles = []
        try:
            logger.info("🚀 Starting Bloomberg fetcher (20-40 seconds - includes login)...")
            self._init_driver()

            # Login
            if not self._login():
                logger.error("❌ Bloomberg login failed - check credentials or page structure")
                return []

            logger.info("📰 Scraping Bloomberg articles...")

            # Navigate to markets section for business articles
            self.driver.get(f"{self.base_url}/markets")
            time.sleep(5)

            # Parse page with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            logger.info("🔍 Searching for article elements...")

            # Find articles - Bloomberg uses <article> tags and links within them
            article_elements = soup.find_all("article")
            logger.info(f"📊 Found {len(article_elements)} <article> elements")

            if not article_elements:
                # Fallback: look for div with article-like structure
                article_elements = soup.find_all("div", {"data-component": "ArticleCard"})
                logger.info(f"📊 Fallback (ArticleCard divs): Found {len(article_elements)}")

            if not article_elements:
                # Last resort: find all links with /news/ in them
                all_links = soup.find_all("a", href=lambda x: x and "/news/" in x)
                logger.info(f"📊 Fallback (links with /news/): Found {len(all_links)}")
                article_elements = all_links[:30]

            logger.info(f"✅ Processing {len(article_elements)} article elements...")

            for idx, element in enumerate(article_elements[:25]):  # Limit to 25
                try:
                    # Extract title
                    title = None
                    if element.name == "article":
                        title_elem = element.find("h3") or element.find("h2") or element.find("a")
                        title = title_elem.get_text(strip=True) if title_elem else None
                    else:
                        title = element.get_text(strip=True)[:100]

                    if not title or len(title) < 5:
                        continue

                    # Extract URL
                    url = None
                    link = element.find("a")
                    if link:
                        url = link.get("href", "")

                    if not url:
                        continue

                    # Make absolute URL
                    if url.startswith("/"):
                        url = f"{self.base_url}{url}"
                    elif not url.startswith("http"):
                        url = f"{self.base_url}/{url}"

                    # Skip non-article URLs
                    if "/news/" not in url and "/markets/" not in url:
                        continue

                    article = ArticleCreate(
                        title=title,  # Full title preserved
                        description=element.get_text(strip=True) if element else "Bloomberg article",  # Full description
                        url=url,
                        source="bloomberg",
                        source_id=url.split("/")[-1][:50],
                        category="Business/Markets",
                        published_at=datetime.utcnow(),
                        image_url=None,
                        authors=["Bloomberg"],
                        content=None,
                        article_type="News"
                    )
                    articles.append(article)
                    logger.info(f"   ✓ Article {idx+1}: {title[:60]}...")

                except Exception as e:
                    logger.warning(f"   ⚠️  Article parse error: {e}")
                    continue

            logger.info(f"✅ Bloomberg: Extracted {len(articles)} articles")

        except Exception as e:
            logger.error(f"❌ Bloomberg scraping failed: {e}")

        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("🗑️  WebDriver closed")
                except:
                    pass

        return articles if articles else []


class NewsAggregator:
    """Aggregates articles from multiple sources (NYT + Bloomberg + Washington Post)"""

    def __init__(self, config=None):
        self.config = config or get_settings()
        self.nyt_fetcher = NYTFetcher(self.config.nyt_api_key)
        self.bloomberg_fetcher = None
        self.washingtonpost_fetcher = WashingtonPostFetcher()
        self.articles_cache = []

        # Initialize Bloomberg fetcher if enabled
        if self.config.bloomberg_enabled and self.config.bloomberg_email and self.config.bloomberg_password:
            self.bloomberg_fetcher = BloombergFetcher(
                self.config.bloomberg_email,
                self.config.bloomberg_password
            )
            logger.info("✅ Bloomberg fetcher initialized")
        else:
            logger.info("⏭️  Bloomberg fetcher disabled or credentials missing")

        # Washington Post fetcher is always available (uses RSS)
        logger.info("✅ Washington Post fetcher initialized (RSS)")

    async def fetch_all(self, days_back: int = 1, sources: List[str] = None) -> List[ArticleCreate]:
        """
        Fetch from configured sources in parallel, with optional filtering

        Args:
            days_back: Number of days to look back
            sources: List of sources to fetch from (nyt, bloomberg, washingtonpost)
                    If None, fetches from all available sources

        Returns:
            Aggregated list of unique articles
        """
        # PRINT DEBUG
        import os
        debug_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug.log")
        with open(debug_path, "a") as f:
            f.write(f"\n[fetch_all] Input sources: {repr(sources)}\n")

        # Default to NYT only if not specified (most reliable)
        with open(debug_path, "a") as f:
            if sources is None:
                f.write(f"[fetch_all] Sources is None - defaulting to NYT\n")
                sources = ["nyt"]
            else:
                # Normalize source names (remove spaces, lowercase)
                f.write(f"[fetch_all] Normalizing sources...\n")
                normalized_sources = []
                for s in sources:
                    f.write(f"[fetch_all]   Processing: {repr(s)}\n")
                    normalized = s.lower().replace(" ", "")
                    f.write(f"[fetch_all]   After normalize: {repr(normalized)}\n")
                    if normalized in ["nyt", "bloomberg", "washingtonpost"]:
                        f.write(f"[fetch_all]   MATCHED - Adding to normalized_sources\n")
                        normalized_sources.append(normalized)
                    else:
                        f.write(f"[fetch_all]   NOT MATCHED - Skipping\n")
                sources = normalized_sources if normalized_sources else ["nyt"]
                f.write(f"[fetch_all] Final normalized_sources: {sources}\n")

            if not sources:
                f.write(f"[fetch_all] Sources still empty - fallback to NYT\n")
                sources = ["nyt"]  # Fallback to NYT

            f.write(f"[fetch_all] Using sources: {sources}\n")
        logger.info(f"🔄 Starting article fetch from sources: {sources} (last {days_back} day(s))...")

        tasks = []

        # Add NYT if requested
        with open(debug_path, "a") as f:
            f.write(f"[fetch_all] Building tasks list:\n")
            f.write(f"[fetch_all] 'nyt' in {sources} = {'nyt' in sources}\n")
        if "nyt" in sources:
            with open(debug_path, "a") as f:
                f.write(f"[fetch_all] Adding NYT fetcher\n")
            tasks.append(("nyt", self.nyt_fetcher.fetch(days_back=days_back)))
            logger.info("Added NYT fetcher")

        # Add Bloomberg if requested and configured
        with open(debug_path, "a") as f:
            f.write(f"[fetch_all] 'bloomberg' in {sources} = {'bloomberg' in sources}\n")
        if "bloomberg" in sources:
            if self.bloomberg_fetcher:
                with open(debug_path, "a") as f:
                    f.write(f"[fetch_all] Adding Bloomberg fetcher\n")
                tasks.append(("bloomberg", self.bloomberg_fetcher.fetch(days_back=days_back)))
                logger.info("Added Bloomberg fetcher")
            else:
                logger.warning("Bloomberg requested but requires paid subscription (not configured)")

        # Add Washington Post if requested (always available)
        with open(debug_path, "a") as f:
            f.write(f"[fetch_all] 'washingtonpost' in {sources} = {'washingtonpost' in sources}\n")
        if "washingtonpost" in sources:
            with open(debug_path, "a") as f:
                f.write(f"[fetch_all] Adding Washington Post fetcher\n")
            tasks.append(("washingtonpost", self.washingtonpost_fetcher.fetch(days_back=days_back)))
            logger.info("Added Washington Post fetcher (RSS)")

        with open(debug_path, "a") as f:
            f.write(f"[fetch_all] Final tasks: {len(tasks)} fetchers\n")

        # Run all fetches concurrently
        articles = []
        if tasks:
            source_names = [t[0] for t in tasks]
            fetch_tasks = [t[1] for t in tasks]
            results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            for i, (source_name, result) in enumerate(zip(source_names, results)):
                if isinstance(result, Exception):
                    logger.error(f"❌ Error in {source_name} fetch: {result}")
                elif result:
                    logger.info(f"✅ {source_name.upper()}: {len(result)} articles")
                    articles.extend(result)
                else:
                    logger.warning(f"⚠️  {source_name.upper()}: No articles fetched")

        # Remove duplicates by URL
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)

        with open(debug_path, "a") as f:
            f.write(f"[fetch_all] Total before dedup: {len(articles)}\n")
            f.write(f"[fetch_all] Total after dedup: {len(unique_articles)}\n")

            # Show breakdown by source
            source_breakdown = {}
            for article in unique_articles:
                source = article.source
                source_breakdown[source] = source_breakdown.get(source, 0) + 1
            f.write(f"[fetch_all] Breakdown by source: {source_breakdown}\n")
            f.write(f"[fetch_all] Returning {len(unique_articles)} articles\n")

        logger.info(f"Total articles fetched: {len(unique_articles)} from {sources}")

        self.articles_cache = unique_articles
        return unique_articles

    def get_cached_articles(self) -> List[ArticleCreate]:
        """Get last fetched articles from cache"""
        return self.articles_cache

    def clear_cache(self):
        """Clear articles cache"""
        self.articles_cache = []
        logger.info("🗑️  Articles cache cleared")
