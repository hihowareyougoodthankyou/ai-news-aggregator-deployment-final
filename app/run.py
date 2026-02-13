"""
AI News Aggregator - Single entry point for the full pipeline.

Runs: Scrape → Summarize → Curate & Send Email
"""

from app.scraper import run_all_scrapers
from app.processors.digest_processor import process_daily_digest
from app.processors.email_processor import run_digest_email, _html_to_plain
from app.agent.user_profiles import USER_RESEARCHER
from app.email_sender import send_digest_email


def run(
    hours_back: int = 500,
    digest_hours_back: int = 48,
) -> None:
    """
    Run the full pipeline: scrape, summarize, curate, send email.
    """
    def _log(msg: str) -> None:
        print(msg, flush=True)

    from app.database.create_tables import create_tables
    create_tables()

    _log("Pipeline: scraping...")
    run_all_scrapers(
        hours_back=hours_back,
        include_content=True,
        verbose=False,
        save_to_db=True,
    )
    _log("Pipeline: summarizing...")
    process_daily_digest(
        verbose=False,
        limit=None,
        skip_existing=True,
    )
    _log("Pipeline: curating and sending email...")
    user_profile = USER_RESEARCHER
    html_body = run_digest_email(
        user_profile=user_profile,
        hours_back=digest_hours_back,
    )

    plain = _html_to_plain(html_body)
    print(plain, flush=True)

    sent = send_digest_email(
        to_email=user_profile.email,
        html_body=html_body,
        subject=f"Your Daily Digest - {user_profile.name}",
    )

    if sent:
        _log(f"Hey {user_profile.name}, your daily digest has been sent to {user_profile.email}")
    else:
        _log("Failed to send. Check SMTP config in .env")


if __name__ == "__main__":
    run()
