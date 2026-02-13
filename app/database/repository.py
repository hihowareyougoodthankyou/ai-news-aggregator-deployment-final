"""Repository for database CRUD operations"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime

from app.database.models import Article, Digest
from app.scrapers.youtube import ChannelVideo
from app.scrapers.blog import BlogPost


class ArticleRepository:
    """Repository for Article operations"""
    
    @staticmethod
    def create_from_youtube_video(
        db: Session,
        source_name: str,
        video: ChannelVideo
    ) -> Optional[Article]:
        """
        Create article from YouTube video.
        
        Args:
            db: Database session
            source_name: Name of the source (e.g., "YouTube")
            video: ChannelVideo object
        
        Returns:
            Created Article object or None if already exists
        """
        # Check if article already exists
        existing = db.query(Article).filter(Article.url == video.url).first()
        if existing:
            return None
        
        article = Article(
            source_name=source_name,
            title=video.title,
            url=video.url,
            description=video.description,
            content=video.transcript,
            published_at=video.published_at,
            category=None,
            video_id=video.video_id,
            channel_id=video.channel_id
        )
        
        db.add(article)
        try:
            db.commit()
            db.refresh(article)
            return article
        except IntegrityError:
            db.rollback()
            return None
    
    @staticmethod
    def create_from_blog_post(
        db: Session,
        source_name: str,
        post: BlogPost
    ) -> Optional[Article]:
        """
        Create article from blog post.
        
        Args:
            db: Database session
            source_name: Name of the source (e.g., "OpenAI Blog")
            post: BlogPost object
        
        Returns:
            Created Article object or None if already exists
        """
        # Check if article already exists
        existing = db.query(Article).filter(Article.url == post.url).first()
        if existing:
            return None
        
        article = Article(
            source_name=source_name,
            title=post.title,
            url=post.url,
            description=post.description,
            content=post.content,
            published_at=post.published_at,
            category=post.category
        )
        
        db.add(article)
        try:
            db.commit()
            db.refresh(article)
            return article
        except IntegrityError:
            db.rollback()
            return None
    
    @staticmethod
    def get_by_source(
        db: Session,
        source_name: str,
        limit: Optional[int] = None
    ) -> List[Article]:
        """
        Get articles by source name.
        
        Args:
            db: Database session
            source_name: Name of the source
            limit: Maximum number of articles to return
        
        Returns:
            List of Article objects
        """
        query = db.query(Article).filter(Article.source_name == source_name)
        query = query.order_by(Article.published_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_recent(
        db: Session,
        hours_back: int = 24,
        limit: Optional[int] = None
    ) -> List[Article]:
        """
        Get recent articles within specified time window.
        
        Args:
            db: Database session
            hours_back: Number of hours to look back
            limit: Maximum number of articles to return
        
        Returns:
            List of Article objects
        """
        from datetime import timedelta, timezone
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        query = db.query(Article).filter(Article.published_at >= cutoff_time)
        query = query.order_by(Article.published_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def count_by_source(db: Session, source_name: str) -> int:
        """
        Count articles by source name.
        
        Args:
            db: Database session
            source_name: Name of the source
        
        Returns:
            Number of articles
        """
        return db.query(Article).filter(Article.source_name == source_name).count()
    
    @staticmethod
    def get_all(db: Session, limit: Optional[int] = None) -> List[Article]:
        """
        Get all articles from the database.
        
        Args:
            db: Database session
            limit: Maximum number of articles to return (None for all)
        
        Returns:
            List of Article objects ordered by published_at desc
        """
        query = db.query(Article).order_by(Article.published_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()


class DigestRepository:
    """Repository for Digest operations"""
    
    @staticmethod
    def create(
        db: Session,
        article_id: int,
        title: str,
        url: str,
        summary: str
    ) -> Optional[Digest]:
        """
        Create a digest entry for an article.
        
        Args:
            db: Database session
            article_id: Article ID
            title: Digest title
            url: Article URL
            summary: 2-3 sentence summary
        
        Returns:
            Created Digest object or None
        """
        # Check if digest already exists for this article
        existing = db.query(Digest).filter(Digest.article_id == article_id).first()
        if existing:
            return None
        
        digest = Digest(
            article_id=article_id,
            title=title,
            url=url,
            summary=summary
        )
        
        db.add(digest)
        try:
            db.commit()
            db.refresh(digest)
            return digest
        except IntegrityError:
            db.rollback()
            return None
    
    @staticmethod
    def get_by_article(db: Session, article_id: int) -> Optional[Digest]:
        """
        Get digest for an article.
        
        Args:
            db: Database session
            article_id: Article ID
        
        Returns:
            Digest object or None
        """
        return db.query(Digest).filter(Digest.article_id == article_id).first()
    
    @staticmethod
    def get_all(db: Session, limit: Optional[int] = None) -> List[Digest]:
        """
        Get all digests.
        
        Args:
            db: Database session
            limit: Maximum number to return
        
        Returns:
            List of Digest objects
        """
        query = db.query(Digest).order_by(Digest.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_recent(
        db: Session,
        hours_back: int = 24,
        limit: Optional[int] = None
    ) -> List[tuple]:
        """
        Get digests created in the last N hours (from today's scrape/summarize run).
        
        Args:
            db: Database session
            hours_back: Number of hours to look back
            limit: Maximum number to return
        
        Returns:
            List of tuples (digest, source_name) for easy processing
        """
        from datetime import timedelta, timezone
        from sqlalchemy.orm import joinedload
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        query = (
            db.query(Digest)
            .options(joinedload(Digest.article))
            .filter(Digest.created_at >= cutoff_time)
            .order_by(Digest.created_at.desc())
        )
        if limit:
            query = query.limit(limit)
        
        digests = query.all()
        return [(d, d.article.source_name if d.article else "Unknown") for d in digests]
