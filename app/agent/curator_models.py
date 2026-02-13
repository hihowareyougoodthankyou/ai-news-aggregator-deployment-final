"""Pydantic models for the curator agent"""

from pydantic import BaseModel, Field
from typing import List


class UserProfile(BaseModel):
    """User profile defining interests and preferences for curation"""
    name: str = Field(..., description="User identifier or name")
    email: str = Field(..., description="Email address to send digest to")
    interests: List[str] = Field(..., description="Topics and areas of interest")
    focus_areas: List[str] = Field(default_factory=list, description="Specific focus areas within interests")
    exclude_topics: List[str] = Field(default_factory=list, description="Topics to deprioritize or exclude")


class DigestItem(BaseModel):
    """Digest item for curation input"""
    digest_id: int
    title: str
    summary: str
    url: str
    source: str


class RankedArticle(BaseModel):
    """A digest article with relevance score and rank"""
    title: str = Field(..., description="Article title")
    digest_id: int = Field(..., description="ID of the digest in the database")
    rank: int = Field(..., description="Rank position (1 = most relevant)")
    score: float = Field(..., ge=0, le=1, description="Relevance score 0-1")
    relevance_reason: str = Field(default="", description="Brief explanation of why it's relevant")


class CuratorResult(BaseModel):
    """Result of curator ranking - ordered list of ranked articles"""
    ranked_articles: List[RankedArticle] = Field(..., description="Articles ranked by relevance to user")
    total_processed: int = Field(..., description="Total number of articles considered")
