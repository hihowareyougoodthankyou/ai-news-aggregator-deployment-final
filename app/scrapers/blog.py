"""Blog scraper using RSS feeds and content extraction"""

import feedparser
from trafilatura import fetch_url, extract
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


class BlogScraper:
    """Scraper for fetching blog posts from RSS feeds."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize blog scraper.
        
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
    
    def get_latest_posts(
        self,
        rss_url: str,
        hours_back: int = 24,
        include_content: bool = True,
        source_name: str = "Blog"
    ) -> List[BlogPost]:
        """
        Fetch latest blog posts from an RSS feed.
        
        Args:
            rss_url: URL of the RSS feed
            hours_back: Number of hours to look back for posts (default: 24)
            include_content: Whether to scrape full article content (default: True)
            source_name: Name of the blog source (default: "Blog")
        
        Returns:
            List of BlogPost objects with:
            - title: Post title
            - url: Post URL
            - description: Post description/summary
            - published_at: Published datetime
            - category: Post category (if available)
            - content: Full article content (if include_content=True)
            - source_name: Name of the source
        """
        posts = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        
        if feed.bozo:
            if self.verbose:
                print(f"Warning: Error parsing RSS feed: {feed.bozo_exception}")
            return posts
        
        if not feed.entries:
            if self.verbose:
                print(f"No entries found in RSS feed")
            return posts
        
        # Process each blog post entry
        for entry in feed.entries:
            # Parse published date
            published_time = entry.get('published_parsed')
            if published_time:
                published_dt = datetime(*published_time[:6], tzinfo=timezone.utc)
            else:
                # Fallback to current time if parsing fails
                published_dt = datetime.now(timezone.utc)
            
            # Filter by time (only posts from specified time window)
            if published_dt < cutoff_time:
                continue
            
            # Extract post data
            title = entry.get('title', 'Untitled')
            url = entry.get('link', '')
            description = entry.get('description', '')
            category = None
            
            # Extract category if available
            if 'tags' in entry and entry.tags:
                category = entry.tags[0].get('term', None)
            elif 'category' in entry:
                category = entry.category
            
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


if __name__ == "__main__":
     scraper = BlogScraper(verbose=False)
     rss_url = "https://openai.com/news/rss.xml"
     latest_posts = scraper.get_latest_posts(rss_url, hours_back=168, source_name="OpenAI Blog")
     for post in latest_posts:
         print(post.title)
         print(post.url)
         print (post.content)
