"""YouTube scraper using RSS feeds and transcript API"""

import feedparser
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable


class ChannelVideo(BaseModel):
    title: str
    url: str
    channel_id: str
    channel_name: str
    published_at: datetime
    description: str
    video_id: str
    transcript: Optional[str] = None
    
class YouTubeScraper:
    """Scraper for fetching YouTube videos and transcripts from channels."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize YouTube scraper.
        
        Args:
            verbose: Whether to print progress and error messages (default: False)
        """
        self.verbose = verbose
        self.transcript_api = YouTubeTranscriptApi()
    
    def extract_channel_id(self, channel_input: str) -> Optional[str]:
        """
        Extract YouTube channel ID from input.
        Supports:
        - Channel ID: UC... (direct, 24 characters)
        - Channel URL: https://www.youtube.com/channel/UC...
        
        Args:
            channel_input: Channel ID or channel URL
        
        Returns:
            Channel ID or None if unable to extract
        """
        # If it's already a channel ID (starts with UC and is 24 chars)
        if channel_input.startswith('UC') and len(channel_input) == 24:
            return channel_input
        
        # Extract from URL
        if 'youtube.com/channel/' in channel_input:
            parsed = urlparse(channel_input)
            if '/channel/' in parsed.path:
                channel_id = parsed.path.split('/channel/')[-1].split('/')[0]
                # Validate it's a proper channel ID
                if channel_id.startswith('UC') and len(channel_id) == 24:
                    return channel_id
        
        return None
    
    def _get_rss_feed_url(self, channel_id: str) -> str:
        """
        Generate YouTube RSS feed URL from channel ID.
        
        Args:
            channel_id: YouTube channel ID
        
        Returns:
            RSS feed URL
        """
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    
    def _extract_video_id(self, video_url: str) -> Optional[str]:
        """
        Extract YouTube video ID from various URL formats.
        
        Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        
        Args:
            video_url: YouTube video URL
        
        Returns:
            Video ID or None if unable to extract
        """
        if 'youtu.be/' in video_url:
            return video_url.split('youtu.be/')[-1].split('?')[0].split('/')[0]
        
        parsed = urlparse(video_url)
        
        if 'youtube.com/watch' in video_url:
            params = parse_qs(parsed.query)
            return params.get('v', [None])[0]
        
        if 'youtube.com/embed/' in video_url:
            return parsed.path.split('/embed/')[-1].split('/')[0]
        
        return None
    
    def get_transcript(self, video_id: str, languages: List[str] = None) -> Optional[str]:
        """
        Fetch transcript for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            languages: Preferred languages (default: ['en'])
        
        Returns:
            Transcript text as a single string, or None if unavailable
        """
        if languages is None:
            languages = ['en']
        
        try:
            # Fetch transcript using the new API
            fetched_transcript = self.transcript_api.fetch(video_id, languages=languages)
            
            # The FetchedTranscript object is iterable and contains snippets
            # Each snippet has .text, .start, and .duration properties
            transcript_text = ' '.join([snippet.text for snippet in fetched_transcript])
            return transcript_text
        
        except TranscriptsDisabled:
            if self.verbose:
                print(f"Transcripts are disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            # Try to find any available transcript
            try:
                # List all available transcripts
                transcript_list = self.transcript_api.list(video_id)
                # Try to find any transcript (preferring English)
                transcript = transcript_list.find_transcript(['en'])
                # Fetch the transcript
                fetched_transcript = transcript.fetch()
                # Extract text from snippets
                transcript_text = ' '.join([snippet.text for snippet in fetched_transcript])
                return transcript_text
            except Exception:
                if self.verbose:
                    print(f"Could not fetch any transcript for video {video_id}")
                return None
        except VideoUnavailable:
            if self.verbose:
                print(f"Video {video_id} is unavailable")
            return None
        except Exception:
            if self.verbose:
                print(f"Error fetching transcript for video {video_id}")
            return None
    
    def get_latest_videos(
        self,
        channel_ids: List[str],
        hours_back: int = 24,
        include_transcript: bool = True
    ) -> List[ChannelVideo]:
        """
        Fetch latest videos from YouTube channels using RSS feeds.
        
        Args:
            channel_ids: List of channel IDs (UC... format) or channel URLs
            hours_back: Number of hours to look back for videos (default: 24)
            include_transcript: Whether to fetch transcripts for videos (default: True)
        
        Returns:
            List of video dictionaries with:
            - title: Video title
            - url: Video URL
            - channel_id: Channel ID
            - channel_name: Channel name
            - published_at: Published datetime
            - description: Video description
            - video_id: YouTube video ID
            - transcript: Video transcript (if include_transcript=True)
        """
        videos = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        for channel_input in channel_ids:
            # Extract and normalize channel ID
            channel_id = self.extract_channel_id(channel_input)
            if not channel_id:
                if self.verbose:
                    print(f"Warning: Could not extract channel ID from '{channel_input}', skipping")
                continue
            
            # Get RSS feed URL
            rss_url = self._get_rss_feed_url(channel_id)
            
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if feed.bozo:
                if self.verbose:
                    print(f"Warning: Error parsing RSS feed for {channel_id}: {feed.bozo_exception}")
                continue
            
            if not feed.entries:
                if self.verbose:
                    print(f"No entries found in RSS feed for {channel_id}")
                continue
            
            # Extract channel name from feed
            channel_name = feed.feed.get('title', 'Unknown Channel')
            
            # Process each video entry
            for entry in feed.entries:
                # Parse published date
                published_time = entry.get('published_parsed')
                if published_time:
                    published_dt = datetime(*published_time[:6], tzinfo=timezone.utc)
                else:
                    # Fallback to current time if parsing fails
                    published_dt = datetime.now(timezone.utc)
                
                # Filter by time (only videos from specified time window)
                if published_dt < cutoff_time:
                    continue
                
                # Extract video URL and ID
                video_url = entry.link
                video_id = self._extract_video_id(video_url)
                
                if not video_id:
                    if self.verbose:
                        print(f"Warning: Could not extract video ID from {video_url}")
                    continue
                
                # Build video data
                video_data = {
                    'title': entry.get('title', 'Untitled'),
                    'url': video_url,
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'published_at': published_dt,
                    'description': entry.get('summary', ''),
                    'video_id': video_id,
                    'transcript': None
                }
                
                # Fetch transcript if requested
                if include_transcript:
                    transcript = self.get_transcript(video_id)
                    video_data['transcript'] = transcript
                
                video = ChannelVideo(**video_data)
                videos.append(video)
        
        return videos


if __name__ == "__main__":
    scraper = YouTubeScraper(verbose=False)
    channel_id = [scraper.extract_channel_id("https://www.youtube.com/channel/UCT3EznhW_CNFcfOlyDNTLLw")]
    latest_videos= scraper.get_latest_videos(channel_id, hours_back=40)
    print(latest_videos)
