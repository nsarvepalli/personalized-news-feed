from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ArticleBase(BaseModel):
    title: str
    description: str
    url: str
    source: str
    category: str
    published_at: datetime
    image_url: Optional[str] = None
    authors: Optional[List[str]] = None
    content: Optional[str] = None
    article_type: Optional[str] = "News"  # News, Editorial, Opinion, Analysis


class ArticleCreate(ArticleBase):
    source_id: str


class ArticleResponse(ArticleBase):
    id: int
    source_id: str
    fetched_at: datetime

    class Config:
        from_attributes = True


class SummaryBase(BaseModel):
    summary_text: str
    summary_length: str = "1-min read"
    relevance_score: float = 0.0
    interest_tags: List[str] = []


class SummaryCreate(SummaryBase):
    article_id: int


class SummaryResponse(SummaryBase):
    id: int
    article_id: int
    created_at: datetime
    model_used: str
    article: ArticleResponse

    class Config:
        from_attributes = True


class UserPreferenceBase(BaseModel):
    interests: List[str]
    age_range: str = "25-35"
    demographic: str = "International Masters Student in USA"
    keywords_to_exclude: List[str] = []
    preferred_sources: List[str] = ["nyt", "bloomberg", "washingtonpost"]


class UserPreferenceCreate(UserPreferenceBase):
    pass


class UserPreferenceResponse(UserPreferenceBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class DigestBase(BaseModel):
    digest_type: str  # "morning" or "evening"
    summaries_count: int
    digest_content: dict


class DigestCreate(DigestBase):
    pass


class DigestResponse(DigestBase):
    id: int
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True
