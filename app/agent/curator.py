"""Curator agent for ranking digest articles by user relevance"""

import os
import json
from typing import List
from groq import Groq
from dotenv import load_dotenv

from app.agent.curator_models import UserProfile, DigestItem, CuratorResult, RankedArticle
from app.agent.curator_prompts import CURATOR_SYSTEM_PROMPT, CURATOR_USER_TEMPLATE

load_dotenv()


class CuratorAgent:
    """Agent for ranking digest articles based on user profile"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize curator agent.
        
        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def _format_digest_items(self, items: List[DigestItem]) -> str:
        """Format digest items for the prompt"""
        lines = []
        for i, item in enumerate(items, 1):
            lines.append(f"[{i}] ID: {item.digest_id}")
            lines.append(f"    Title: {item.title}")
            lines.append(f"    Source: {item.source}")
            lines.append(f"    Summary: {item.summary[:300]}{'...' if len(item.summary) > 300 else ''}")
            lines.append("")
        return "\n".join(lines).strip()
    
    def rank(
        self,
        digest_items: List[DigestItem],
        user_profile: UserProfile
    ) -> CuratorResult:
        """
        Rank digest items by relevance to user profile.
        
        Args:
            digest_items: List of digest items to rank
            user_profile: User's interests and preferences
        
        Returns:
            CuratorResult with ranked articles
        """
        if not digest_items:
            return CuratorResult(ranked_articles=[], total_processed=0)
        
        user_message = CURATOR_USER_TEMPLATE.format(
            user_name=user_profile.name,
            interests=", ".join(user_profile.interests),
            focus_areas=", ".join(user_profile.focus_areas) if user_profile.focus_areas else "None",
            exclude_topics=", ".join(user_profile.exclude_topics) if user_profile.exclude_topics else "None",
            digest_items=self._format_digest_items(digest_items)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": CURATOR_SYSTEM_PROMPT},
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
            ranked_data = result.get("ranked_articles", [])
            total = result.get("total_processed", len(digest_items))
            
            # Map digest_id -> title from our input
            digest_map = {d.digest_id: d.title for d in digest_items}
            
            ranked_articles = []
            for item in ranked_data:
                digest_id = item.get("digest_id")
                if digest_id is None or digest_id not in digest_map:
                    continue
                ranked_articles.append(RankedArticle(
                    title=digest_map[digest_id],
                    digest_id=digest_id,
                    rank=item.get("rank", 0),
                    score=float(item.get("score", 0)),
                    relevance_reason=item.get("relevance_reason", "")
                ))
            
            # Sort by rank to ensure correct order
            ranked_articles.sort(key=lambda x: x.rank)
            
            return CuratorResult(
                ranked_articles=ranked_articles,
                total_processed=total
            )
        
        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            if self.verbose:
                print(f"Error in curator: {e}")
            return None
