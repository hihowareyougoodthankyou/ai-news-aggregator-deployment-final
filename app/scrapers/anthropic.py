"""Anthropic blog scraper for multiple RSS feeds"""

import feedparser
from trafilatura import extract
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel


class BlogPost(BaseModel):
    """Model representing a blog post."""
    title: str
    url: str
    description: str
    published_at: datetime
    category: Optional[str] = None
    content: Optional[str] = None
    source_name: str


class AnthropicScraper:
    """Scraper for fetching blog posts from Anthropic's RSS feeds."""
    
    # Anthropic RSS feed URLs
    RSS_FEEDS = {
        'news': 'https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml',
        'engineering': 'https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml',
        'research': 'https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml'
    }
    
    def __init__(self, verbose: bool = False):
        """
        Initialize Anthropic scraper.
        
        Args:
            verbose: Whether to print progress and error messages (default: False)
        """
        self.verbose = verbose
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _scrape_article_content(self, url: str) -> Optional[str]:
        """
        Scrape full article content from a blog post URL.
        
        Args:
            url: URL of the blog post
        
        Returns:
            Full article content as text, or None if unable to scrape
        """
        try:
            # Fetch the page
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            # Extract content using trafilatura
            content = extract(
                response.text,
                include_comments=False,
                include_tables=False,
                favor_recall=True
            )
            
            if not content:
                if self.verbose:
                    print(f"Warning: Could not extract content from {url}")
                return None
            
            return content
        
        except requests.RequestException as e:
            if self.verbose:
                print(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            if self.verbose:
                print(f"Error scraping content from {url}: {e}")
            return None
    
    def _parse_feed(
        self,
        rss_url: str,
        feed_name: str,
        hours_back: int,
        include_content: bool
    ) -> List[BlogPost]:
        """
        Parse a single RSS feed and return blog posts.
        
        Args:
            rss_url: URL of the RSS feed
            feed_name: Name of the feed (for source_name)
            hours_back: Number of hours to look back
            include_content: Whether to scrape full content
        
        Returns:
            List of BlogPost objects
        """
        posts = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        
        # Note: feed.bozo can be True even if parsing succeeded (minor issues)
        # Common issue: GitHub raw URLs serve XML as text/plain, but feedparser handles it fine
        # Only show warning if it's a real error (not just content-type mismatch)
        if feed.bozo:
            # Check if it's just a content-type issue (non-fatal)
            bozo_exception = feed.bozo_exception
            if bozo_exception and hasattr(bozo_exception, '__class__'):
                exception_name = bozo_exception.__class__.__name__
                # NonXMLContentType is harmless - feedparser still parses correctly
                if exception_name != 'NonXMLContentType':
                    if self.verbose:
                        print(f"Warning: RSS feed {feed_name} has parsing issues: {bozo_exception}")
                elif self.verbose:
                    # Optionally show that we're ignoring the harmless content-type warning
                    pass  # Suppress NonXMLContentType warnings as they're harmless
        
        if not feed.entries:
            if self.verbose:
                print(f"No entries found in RSS feed {feed_name}")
            return posts
        
        # Process each blog post entry
        for entry in feed.entries:
            # Extract post data first
            title = entry.get('title', 'Untitled')
            url = entry.get('link', '')
            description = entry.get('description', '')
            category = None
            
            # Parse published date
            published_time = entry.get('published_parsed')
            if published_time:
                published_dt = datetime(*published_time[:6], tzinfo=timezone.utc)
            else:
                # Skip entries without published dates (they're likely not actual posts)
                # Some RSS feeds have category/header entries without dates
                if self.verbose:
                    print(f"Skipping entry '{title[:50]}...' - no published date")
                continue
            
            # Filter by time (only posts from specified time window)
            if published_dt < cutoff_time:
                if self.verbose:
                    print(f"Skipping post '{title[:50]}...' - published {published_dt} (cutoff: {cutoff_time})")
                continue
            
            # Extract category if available
            if 'tags' in entry and entry.tags:
                category = entry.tags[0].get('term', None)
            elif 'category' in entry:
                category = entry.category
            
            # Build source name with feed type
            source_name = f"Anthropic {feed_name.title()}"
            
            # Build post data
            post_data = {
                'title': title,
                'url': url,
                'description': description,
                'published_at': published_dt,
                'category': category,
                'content': None,
                'source_name': source_name
            }
            
            # Scrape full content if requested
            if include_content and url:
                content = self._scrape_article_content(url)
                post_data['content'] = content
            
            post = BlogPost(**post_data)
            posts.append(post)
        
        return posts
    
    def get_latest_posts(
        self,
        hours_back: int = 24,
        include_content: bool = True,
        feed_types: Optional[List[str]] = None
    ) -> List[BlogPost]:
        """
        Fetch latest blog posts from Anthropic RSS feeds.
        
        Args:
            hours_back: Number of hours to look back for posts (default: 24)
            include_content: Whether to scrape full article content (default: True)
            feed_types: List of feed types to scrape. Options: 'news', 'engineering', 'research'.
                       If None, scrapes all feeds (default: None)
        
        Returns:
            List of BlogPost objects with:
            - title: Post title
            - url: Post URL
            - description: Post description/summary
            - published_at: Published datetime
            - category: Post category (if available)
            - content: Full article content (if include_content=True)
            - source_name: Name of the source (e.g., "Anthropic News", "Anthropic Engineering")
        """
        all_posts = []
        
        # Determine which feeds to scrape
        if feed_types is None:
            feeds_to_scrape = self.RSS_FEEDS.items()
        else:
            feeds_to_scrape = [(ft, self.RSS_FEEDS[ft]) 
                              for ft in feed_types if ft in self.RSS_FEEDS]
        
        # Scrape each feed
        for feed_name, rss_url in feeds_to_scrape:
            if self.verbose:
                print(f"Scraping {feed_name} feed...")
            posts = self._parse_feed(rss_url, feed_name, hours_back, include_content)
            if self.verbose:
                print(f"Found {len(posts)} posts from {feed_name}")
            all_posts.extend(posts)
        
        # Sort by published date (newest first)
        all_posts.sort(key=lambda x: x.published_at, reverse=True)
        
        return all_posts


if __name__ == "__main__":
    scraper = AnthropicScraper() 
    # Get posts from all feeds
    latest_posts = scraper.get_latest_posts(hours_back=168, include_content=True)
    print(latest_posts)