"""Orchestrates all scrapers (YouTube, OpenAI, Anthropic)"""

from typing import List, Dict, Any
from app.scrapers.youtube import YouTubeScraper, ChannelVideo
from app.scrapers.blog import BlogScraper, BlogPost
from app.scrapers.anthropic import AnthropicScraper
from app.config import YOUTUBE_CHANNEL_IDS, OPENAI_RSS_URL
from app.database.database import get_db
from app.database.repository import ArticleRepository


def run_all_scrapers(
    hours_back: int = 24,
    include_content: bool = True,
    verbose: bool = False,
    save_to_db: bool = True
) -> Dict[str, List[Any]]:
    """
    Run all scrapers and collect results, optionally saving to database.
    """
    results = {
        'youtube': [],
        'openai': [],
        'anthropic': [],
        'saved': {
            'youtube': 0,
            'openai': 0,
            'anthropic': 0
        }
    }
    
    db = next(get_db()) if save_to_db else None
    
    try:
        if YOUTUBE_CHANNEL_IDS:
            if verbose:
                print(f"Scraping {len(YOUTUBE_CHANNEL_IDS)} YouTube channel(s)...")
            youtube_scraper = YouTubeScraper(verbose=verbose)
            youtube_videos = youtube_scraper.get_latest_videos(
                YOUTUBE_CHANNEL_IDS,
                hours_back=hours_back,
                include_transcript=include_content
            )
            results['youtube'] = youtube_videos
            if verbose:
                print(f"Found {len(youtube_videos)} YouTube video(s)")
            
            if save_to_db and db:
                saved_count = 0
                for video in youtube_videos:
                    article = ArticleRepository.create_from_youtube_video(
                        db, "YouTube", video
                    )
                    if article:
                        saved_count += 1
                results['saved']['youtube'] = saved_count
                if verbose:
                    print(f"Saved {saved_count} YouTube video(s) to database")
        else:
            if verbose:
                print("No YouTube channels configured, skipping YouTube scraper")
        
        if verbose:
            print("Scraping OpenAI blog...")
        openai_scraper = BlogScraper(verbose=verbose)
        openai_posts = openai_scraper.get_latest_posts(
            OPENAI_RSS_URL,
            hours_back=hours_back,
            include_content=include_content,
            source_name="OpenAI Blog"
        )
        results['openai'] = openai_posts
        if verbose:
            print(f"Found {len(openai_posts)} OpenAI post(s)")
        
        if save_to_db and db:
            saved_count = 0
            for post in openai_posts:
                article = ArticleRepository.create_from_blog_post(
                    db, "OpenAI Blog", post
                )
                if article:
                    saved_count += 1
            results['saved']['openai'] = saved_count
            if verbose:
                print(f"Saved {saved_count} OpenAI post(s) to database")
        
        if verbose:
            print("Scraping Anthropic blogs...")
        anthropic_scraper = AnthropicScraper(verbose=verbose)
        anthropic_posts = anthropic_scraper.get_latest_posts(
            hours_back=hours_back,
            include_content=include_content
        )
        results['anthropic'] = anthropic_posts
        if verbose:
            print(f"Found {len(anthropic_posts)} Anthropic post(s)")
        
        if save_to_db and db:
            saved_count = 0
            for post in anthropic_posts:
                article = ArticleRepository.create_from_blog_post(
                    db, post.source_name, post
                )
                if article:
                    saved_count += 1
            results['saved']['anthropic'] = saved_count
            if verbose:
                print(f"Saved {saved_count} Anthropic post(s) to database")
    
    finally:
        if db:
            db.close()
    
    return results
