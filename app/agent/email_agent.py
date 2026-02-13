"""Email agent for generating daily digest emails"""

import os
from datetime import datetime, timezone
from typing import List
from groq import Groq
from dotenv import load_dotenv

from app.agent.curator_models import UserProfile
from app.agent.email_prompts import EMAIL_TEASER_SYSTEM_PROMPT, EMAIL_TEASER_USER_TEMPLATE

load_dotenv()


def _ordinal(n: int) -> str:
    """Return ordinal suffix for n (e.g. 1 -> 'st', 2 -> 'nd', 9 -> 'th')"""
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _format_date(dt: datetime) -> str:
    """Format as '9th December 2025'"""
    day = dt.day
    return f"{day}{_ordinal(day)} {dt.strftime('%B %Y')}"


class EmailArticle:
    """Article to include in digest email"""
    def __init__(self, title: str, summary: str, url: str, source: str):
        self.title = title
        self.summary = summary
        self.url = url
        self.source = source


class EmailAgent:
    """Agent for generating digest emails with personalized intro and formatted articles"""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def _generate_teaser(
        self,
        user_profile: UserProfile,
        articles: List[EmailArticle]
    ) -> str:
        """Generate teaser paragraph based on today's articles"""
        if not articles:
            return "There's nothing new in your digest today. Check back tomorrow."
        
        article_titles = "\n".join(f"- {a.title}" for a in articles[:20])
        if len(articles) > 20:
            article_titles += f"\n... and {len(articles) - 20} more"
        
        user_message = EMAIL_TEASER_USER_TEMPLATE.format(
            interests=", ".join(user_profile.interests),
            article_titles=article_titles
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EMAIL_TEASER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ]
            )
            teaser = response.choices[0].message.content
            return teaser.strip() if teaser else "Curated based on your interests."
        except Exception:
            return "Curated based on your interests."
    
    def _get_intro(
        self,
        user_profile: UserProfile,
        articles: List[EmailArticle]
    ) -> str:
        """Build full intro: greeting + date + teaser + sign-off"""
        today = datetime.now(timezone.utc)
        date_str = _format_date(today)
        teaser = self._generate_teaser(user_profile, articles)
        sep = ". " if not articles else ", "
        return (
            f"Hi there, hope you're doing well. Your daily digest is here for {date_str}{sep}"
            f"{teaser} Have a good day!!"
        )
    
    def _build_html_email(
        self,
        intro: str,
        articles: List[EmailArticle]
    ) -> str:
        """Build HTML email with intro and article blocks"""
        article_blocks = []
        for a in articles:
            article_blocks.append(f"""
<div style="margin-bottom: 28px; padding-bottom: 24px; border-bottom: 1px solid #e5e7eb;">
  <h2 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; color: #111827; line-height: 1.4;">
    <a href="{a.url}" style="color: #111827; text-decoration: none;">{self._escape_html(a.title)}</a>
  </h2>
  <p style="margin: 0 0 8px 0; font-size: 12px; color: #6b7280;">{self._escape_html(a.source)}</p>
  <p style="margin: 0 0 12px 0; font-size: 15px; color: #374151; line-height: 1.6;">{self._escape_html(a.summary)}</p>
  <a href="{a.url}" style="font-size: 14px; color: #2563eb; text-decoration: none; font-weight: 500;">Read more →</a>
</div>""")
        
        articles_html = "\n".join(article_blocks)
        
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Daily Digest</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f9fafb; color: #111827;">
  <div style="max-width: 600px; margin: 0 auto; padding: 40px 24px;">
    <div style="margin-bottom: 32px;">
      <p style="margin: 0; font-size: 16px; color: #374151; line-height: 1.6;">
        {self._escape_html(intro)}
      </p>
    </div>

    <div style="margin-top: 32px;">
      {articles_html if articles else '<p style="color: #6b7280;">Nothing new in your digest today.</p>'}
    </div>

    <div style="margin-top: 40px; padding-top: 24px; border-top: 1px solid #e5e7eb; font-size: 13px; color: #9ca3af;">
      You're receiving this because you're subscribed to the AI News Digest. Curated for you based on your interests.
    </div>
  </div>
</body>
</html>"""
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML entities"""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
    
    def generate(
        self,
        user_profile: UserProfile,
        articles: List[EmailArticle]
    ) -> str:
        """
        Generate digest email HTML body.
        
        Args:
            user_profile: User profile for personalization
            articles: Ranked articles (title, summary, url, source) in display order
        
        Returns:
            HTML body string
        """
        intro = self._get_intro(user_profile, articles)
        return self._build_html_email(intro, articles)
