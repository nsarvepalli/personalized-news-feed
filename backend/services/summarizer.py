# Summarizer Service
# Generates 1-min read summaries using OpenAI API (direct HTTP calls)

import logging
import requests
from typing import Tuple, List

logger = logging.getLogger(__name__)


class ArticleSummarizer:
    """Summarizes articles using OpenAI API (direct HTTP)"""

    def __init__(self, api_key: str):
        if not api_key or api_key == "sk-dummy":
            raise ValueError("Valid OpenAI API key is required")
        try:
            self.api_key = api_key
            self.model = "gpt-3.5-turbo"
            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            logger.info(f"✅ ArticleSummarizer initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            raise

    def summarize(
        self,
        title: str,
        description: str,
        content: str = None,
        interests: List[str] = None,
        demographic: str = "International Masters Student in USA, ages 25-35"
    ) -> Tuple[str, List[str]]:
        """
        Summarize an article to 1-min read (~200-250 words)

        Args:
            title: Article title
            description: Article description/lead paragraph
            content: Full article content (optional)
            interests: User interests (business, education, ai, upskilling)
            demographic: Target demographic description

        Returns:
            Tuple[str, List[str]]: (summary_text, extracted_tags)
        """
        try:
            # Combine available text
            article_text = f"Title: {title}\n\n"
            if description:
                article_text += f"Description: {description}\n\n"
            if content:
                article_text += f"Content: {content}"

            # Build interest context for prompt
            interest_str = ", ".join(interests) if interests else "business, education, technology, AI"

            prompt = f"""You are a professional news editor creating summaries for {demographic}.

Article to summarize:
{article_text}

Please create a ONE-MINUTE READ summary (200-250 words) with these requirements:
1. Written for someone interested in: {interest_str}
2. To-the-point, no fluff, actionable insights
3. Highlight key takeaways and impact
4. Professional tone suitable for a busy professional
5. Start with the most important information

Additionally, at the end, provide EXACTLY 3 interest tags from this list:
- business
- education
- ai
- upskilling
- technology
- career
- finance
- innovation
- international
- student-life

Format your response as:
SUMMARY:
[Your summary here]

TAGS:
[tag1, tag2, tag3]"""

            logger.info(f"📝 Summarizing article: {title[:50]}...")

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a concise news summarizer for professional readers."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 400
            }

            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            response_text = data["choices"][0]["message"]["content"]

            # Parse response
            summary_text = ""
            tags = []

            if "SUMMARY:" in response_text and "TAGS:" in response_text:
                summary_section = response_text.split("TAGS:")[0].replace("SUMMARY:", "").strip()
                tags_section = response_text.split("TAGS:")[1].strip()

                summary_text = summary_section
                # Parse tags
                tags_str = tags_section.replace("[", "").replace("]", "")
                tags = [tag.strip().lower() for tag in tags_str.split(",")]
            else:
                summary_text = response_text
                tags = self._extract_tags(response_text)

            logger.info(f"✅ Summary created: {len(summary_text)} characters, Tags: {tags}")

            return summary_text, tags

        except Exception as e:
            logger.error(f"❌ Summarization failed: {e}")
            raise

    def _extract_tags(self, text: str) -> List[str]:
        """Extract tags from text if not explicitly provided"""
        valid_tags = ["business", "education", "ai", "upskilling", "technology", "career", "finance", "innovation", "international", "student-life"]
        found_tags = []

        for tag in valid_tags:
            if tag.lower() in text.lower():
                found_tags.append(tag)

        # Return up to 3 tags
        return found_tags[:3] if found_tags else ["technology"]

    def calculate_relevance_score(
        self,
        article_title: str,
        article_tags: List[str],
        user_interests: List[str]
    ) -> float:
        """
        Calculate relevance score (0-1) based on article tags vs user interests

        Args:
            article_title: Article title
            article_tags: Tags extracted from article
            user_interests: User's interest preferences

        Returns:
            float: Relevance score from 0.0 to 1.0
        """
        try:
            if not user_interests:
                user_interests = ["business", "education", "technology"]

            # Convert to lowercase for comparison
            article_tags_lower = [tag.lower() for tag in article_tags]
            user_interests_lower = [interest.lower() for interest in user_interests]

            # Calculate overlap
            matching_tags = set(article_tags_lower) & set(user_interests_lower)
            max_tags = max(len(article_tags_lower), len(user_interests_lower))

            if max_tags == 0:
                relevance = 0.5  # Default relevance if no tags
            else:
                relevance = len(matching_tags) / max_tags

            logger.info(f"📊 Relevance score for '{article_title[:40]}...': {relevance:.2f}")

            return round(relevance, 2)

        except Exception as e:
            logger.error(f"❌ Relevance calculation failed: {e}")
            return 0.5

    def batch_summarize(
        self,
        articles: List[dict],
        user_interests: List[str] = None
    ) -> List[dict]:
        """
        Summarize multiple articles

        Args:
            articles: List of article dicts with keys: title, description, content
            user_interests: User interest preferences

        Returns:
            List of articles with added 'summary', 'tags', 'relevance_score'
        """
        summarized_articles = []

        for i, article in enumerate(articles, 1):
            try:
                logger.info(f"🔄 Summarizing article {i}/{len(articles)}")

                summary_text, tags = self.summarize(
                    title=article.get("title", ""),
                    description=article.get("description", ""),
                    content=article.get("content"),
                    interests=user_interests
                )

                relevance_score = self.calculate_relevance_score(
                    article_title=article.get("title", ""),
                    article_tags=tags,
                    user_interests=user_interests or ["business", "education", "technology"]
                )

                article["summary"] = summary_text
                article["tags"] = tags
                article["relevance_score"] = relevance_score

                summarized_articles.append(article)

            except Exception as e:
                logger.error(f"❌ Failed to summarize article {i}: {e}")
                continue

        logger.info(f"✅ Batch summarization complete: {len(summarized_articles)}/{len(articles)} articles processed")

        return summarized_articles
