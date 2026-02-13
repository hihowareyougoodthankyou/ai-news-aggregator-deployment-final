"""SQLAlchemy database models"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Article(Base):
    """Article model - represents an article/video from a source"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source (stored as string: YouTube, OpenAI Blog, Anthropic News, etc.)
    source_name = Column(String(255), nullable=False, index=True)
    
    # Article metadata
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Full article content or transcript
    
    # Dates
    published_at = Column(DateTime, nullable=False, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Additional metadata
    category = Column(String(255), nullable=True)
    video_id = Column(String(100), nullable=True)  # For YouTube videos
    channel_id = Column(String(100), nullable=True)  # For YouTube videos
    
    # Relationship to digests
    digests = relationship("Digest", back_populates="article", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source='{self.source_name}')>"


class Digest(Base):
    """Digest model - summarized article for daily digest"""
    __tablename__ = "digests"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    
    # Digest content
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    summary = Column(Text, nullable=False)  # 2-3 sentence summary
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to article
    article = relationship("Article", back_populates="digests")
    
    def __repr__(self):
        return f"<Digest(id={self.id}, title='{self.title[:50]}...', article_id={self.article_id})>"
