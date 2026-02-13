"""Processor for generating digest emails"""

import re
from app.database.database import get_db
from app.database.repository import DigestRepository
from app.agent.curator import CuratorAgent
from app.agent.curator_models import UserProfile, DigestItem
from app.agent.email_agent import EmailAgent, EmailArticle


def run_digest_email(
    user_profile: UserProfile,
        hours_back: int = 48,
        fallback_hours: int = 168,
    max_articles: int = 25
) -> str:
    """
    Run curator, then generate digest email for a user.
    Only includes articles/videos published in the last hours_back.
    
    Args:
        user_profile: User profile with interests
        hours_back: Hours to look back for articles (default 24)
        fallback_hours: If 0 in hours_back, try this window (default 168 = 1 week)
        max_articles: Max articles to send to curator (avoids token/rate limits)
    
    Returns:
        HTML body string for the email
    """
    db = next(get_db())
    
    try:
        digest_tuples = DigestRepository.get_recent(db, hours_back=hours_back)
        if not digest_tuples and fallback_hours and fallback_hours != hours_back:
            digest_tuples = DigestRepository.get_recent(db, hours_back=fallback_hours)
        
        if not digest_tuples:
            return EmailAgent().generate(user_profile, [])
        
        digest_tuples = digest_tuples[:max_articles]
        digest_items = [
            DigestItem(
                digest_id=d.id,
                title=d.title,
                summary=d.summary,
                url=d.url,
                source=source_name
            )
            for d, source_name in digest_tuples
        ]
        
        curator = CuratorAgent(verbose=False)
        result = curator.rank(digest_items, user_profile)
        
        if not result or not result.ranked_articles:
            return EmailAgent().generate(user_profile, [])
        
        digest_map = {d.id: (d, sn) for d, sn in digest_tuples}
        articles = []
        for ranked in result.ranked_articles:
            if ranked.digest_id in digest_map:
                digest, source_name = digest_map[ranked.digest_id]
                articles.append(EmailArticle(
                    title=ranked.title,
                    summary=digest.summary,
                    url=digest.url,
                    source=source_name
                ))
        
        return EmailAgent().generate(user_profile, articles)
    
    finally:
        db.close()


def _html_to_plain(html: str) -> str:
    """Strip HTML tags for terminal output"""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|h[1-6])>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&#x27;", "'", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
