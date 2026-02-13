"""Summarization agent using Groq with Llama 3.3 70B"""

import os
import json
from typing import Optional
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

from app.agent.prompts import SUMMARY_SYSTEM_PROMPT, SUMMARY_USER_TEMPLATE

load_dotenv()

class DigestEntry(BaseModel):
    """Structured output for digest entry"""
    digest_title: str
    summary: str


class SummarizerAgent:
    """Agent for summarizing articles using Groq Llama 3.3 70B"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize summarizer agent.
        
        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def _truncate_content(self, content: Optional[str], max_chars: int = 12000) -> str:
        """
        Truncate content to fit within model context limits.
        
        Args:
            content: Full content to truncate
            max_chars: Maximum characters to include
        
        Returns:
            Truncated content
        """
        if not content:
            return "(No content available)"
        if len(content) <= max_chars:
            return content
        return content[:max_chars] + "\n\n[Content truncated for length...]"
    
    def summarize(
        self,
        title: str,
        url: str,
        source_name: str,
        content: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[DigestEntry]:
        """
        Generate a digest entry (title + summary) for an article.
        
        Args:
            title: Original article title
            url: Article URL
            source_name: Name of the source
            content: Full article content or transcript
            description: Article description (fallback if no content)
        
        Returns:
            DigestEntry with digest_title and summary, or None on failure
        """
        # Use content if available, otherwise description
        text_content = content if content else description or "(No content available)"
        text_content = self._truncate_content(text_content)
        
        user_message = SUMMARY_USER_TEMPLATE.format(
            title=title,
            source_name=source_name,
            url=url,
            content=text_content
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"}
            )
            
            content_str = response.choices[0].message.content
            if not content_str:
                if self.verbose:
                    print("Empty response from Groq")
                return None
            
            result = json.loads(content_str)
            # Extract fields (handle various key formats)
            digest_title = result.get("digest_title")
            summary = result.get("summary")
            if not digest_title or not summary:
                if self.verbose:
                    print(f"Missing required fields in response: {result.keys()}")
                return None
            return DigestEntry(digest_title=digest_title, summary=summary)
        
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            if self.verbose:
                print(f"Error summarizing article: {e}")
            return None