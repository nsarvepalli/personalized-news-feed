#!/usr/bin/env python
"""
CUSTOMIZED TEST SCRIPT - Test your three news sources
Tests NYT API, Bloomberg login, and Washington Post scraping
"""

import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from config import get_settings
from services.news_fetcher import NYTFetcher, WashingtonPostFetcher, BloombergFetcher

# Setup logging to see all details
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
settings = get_settings()


async def test_nyt():
    """Test NYT fetcher - should always work"""
    print("\n" + "="*70)
    print("🧪 TEST 1: NEW YORK TIMES (API)")
    print("="*70)

    if not settings.nyt_api_key:
        print("❌ NYT_API_KEY not in .env")
        return

    try:
        fetcher = NYTFetcher(settings.nyt_api_key)
        articles = await fetcher.fetch(days_back=1)

        if articles:
            print(f"✅ SUCCESS: {len(articles)} articles fetched")
            for i, article in enumerate(articles[:3], 1):
                print(f"   {i}. {article.title[:70]}")
                print(f"      URL: {article.url[:70]}")
        else:
            print("❌ No articles returned - check API key validity")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_washpo():
    """Test Washington Post fetcher - scraping method"""
    print("\n" + "="*70)
    print("🧪 TEST 2: WASHINGTON POST (WEB SCRAPING)")
    print("="*70)

    try:
        fetcher = WashingtonPostFetcher()
        articles = await fetcher.fetch(days_back=1)

        if articles:
            print(f"✅ SUCCESS: {len(articles)} articles scraped")
            for i, article in enumerate(articles[:3], 1):
                print(f"   {i}. {article.title[:70]}")
                print(f"      URL: {article.url[:70]}")
        else:
            print("⚠️  No articles found - Washington Post may require subscription headers")
            print("   This is expected if site blocks non-subscriber access")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_bloomberg():
    """Test Bloomberg fetcher - requires login"""
    print("\n" + "="*70)
    print("🧪 TEST 3: BLOOMBERG (SELENIUM LOGIN + SCRAPING)")
    print("="*70)
    print("⏳ This may take 20-40 seconds (includes browser automation)...\n")

    if not settings.bloomberg_enabled:
        print("❌ BLOOMBERG_ENABLED=false in .env")
        return

    if not settings.bloomberg_email or not settings.bloomberg_password:
        print("❌ Missing Bloomberg credentials:")
        print("   - BLOOMBERG_EMAIL not set")
        print("   - BLOOMBERG_PASSWORD not set")
        return

    print(f"📧 Email: {settings.bloomberg_email[:20]}...")
    print("🔑 Password: ****** (configured)")
    print("\nStarting login sequence...\n")

    try:
        fetcher = BloombergFetcher(settings.bloomberg_email, settings.bloomberg_password)
        articles = await fetcher.fetch(days_back=1)

        if articles:
            print(f"\n✅ SUCCESS: {len(articles)} articles fetched")
            for i, article in enumerate(articles[:3], 1):
                print(f"   {i}. {article.title[:70]}")
                print(f"      URL: {article.url[:70]}")
        else:
            print("\n❌ No articles returned - Check errors above:")
            print("   1. Login failed? Check credentials")
            print("   2. Page structure changed? Bloomberg updates selectors often")
            print("   3. Blocked by Bloomberg? Check if IP is whitelisted")
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def main():
    print("\n" + "="*70)
    print("📰 PERSONALIZED NEWS FEED - FETCHER VALIDATION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # Test each source
    await test_nyt()
    await test_washpo()
    await test_bloomberg()

    print("\n" + "="*70)
    print("✅ TESTING COMPLETE")
    print("="*70)
    print("\n📋 SUMMARY & NEXT STEPS:\n")
    print("✅ NYT working?  → Ignore Bloomberg/WashPo if they fail, NYT is reliable")
    print("✅ WashPo working?  → Great! May need subscription headers if blocked")
    print("✅ Bloomberg working?  → Excellent! Selenium login successful")
    print("\nIf any source fails:")
    print("  1. Check the detailed logs above for specific error messages")
    print("  2. Review .env file for correct credentials")
    print("  3. Bloomberg may require 2FA to be disabled")
    print("  4. Washington Post may block IP - try with VPN")
    print("\n➡️  Next: Run 'streamlit run frontend/app.py' to test the app\n")


if __name__ == "__main__":
    asyncio.run(main())
