"""Processor for generating daily digest from articles"""

from typing import Dict, Any, List
from app.database.database import get_db
from app.database.repository import ArticleRepository, DigestRepository
from app.agent.summarizer import SummarizerAgent, DigestEntry


def process_daily_digest(
    verbose: bool = False,
    limit: int = None,
    skip_existing: bool = True
) -> Dict[str, Any]:
    """
    Process all articles in the database and create digest entries.
    
    For each article:
    - Fetches full context (title, url, content, description, source)
    - Uses Groq/Llama to generate 2-3 sentence summary
    - Saves to digest table with link to article
    
    Args:
        verbose: Whether to print progress messages
        limit: Maximum number of articles to process (None for all)
        skip_existing: Skip articles that already have a digest
    
    Returns:
        Dictionary with:
        - processed: Number of articles processed
        - created: Number of new digest entries created
        - skipped: Number skipped (already had digest)
        - failed: Number that failed to summarize
        - digests: List of created digest entries
    """
    results = {
        "processed": 0,
        "created": 0,
        "skipped": 0,
        "failed": 0,
        "digests": []
    }
    
    db = next(get_db())
    
    try:
        # Get all articles from database
        articles = ArticleRepository.get_all(db, limit=limit)
        
        if verbose:
            print(f"Found {len(articles)} articles to process")
        
        agent = SummarizerAgent(verbose=verbose)
        
        for article in articles:
            results["processed"] += 1
            
            # Skip if digest already exists
            if skip_existing:
                existing = DigestRepository.get_by_article(db, article.id)
                if existing:
                    results["skipped"] += 1
                    if verbose:
                        print(f"Skipping article {article.id} (already has digest)")
                    continue
            
            # Build context for summarization
            source_name = article.source_name
            content = article.content or article.description
            
            if not content:
                if verbose:
                    print(f"Skipping article {article.id} (no content)")
                results["skipped"] += 1
                continue
            
            # Generate summary using agent
            digest_entry = agent.summarize(
                title=article.title,
                url=article.url,
                source_name=source_name,
                content=article.content,
                description=article.description
            )
            
            if not digest_entry:
                results["failed"] += 1
                if verbose:
                    print(f"Failed to summarize article {article.id}")
                continue
            
            # Save to database
            digest = DigestRepository.create(
                db,
                article_id=article.id,
                title=digest_entry.digest_title,
                url=article.url,
                summary=digest_entry.summary
            )
            
            if digest:
                results["created"] += 1
                results["digests"].append({
                    "title": digest_entry.digest_title,
                    "url": article.url,
                    "summary": digest_entry.summary,
                    "source": source_name
                })
                if verbose:
                    print(f"Created digest for article {article.id}: {digest_entry.digest_title[:50]}...")
    
    finally:
        db.close()
    
    return results