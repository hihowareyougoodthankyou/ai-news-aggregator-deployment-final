"""Processor for running curator agent on digest articles"""

from typing import Optional
from app.database.database import get_db
from app.database.repository import DigestRepository
from app.agent.curator import CuratorAgent
from app.agent.curator_models import UserProfile, DigestItem, CuratorResult


def run_curator(
    user_profile: UserProfile,
    hours_back: int = 24,
    verbose: bool = False
) -> Optional[CuratorResult]:
    """
    Fetch digests from last 24 hours and rank them for a user.
    
    Args:
        user_profile: User profile with interests
        hours_back: Hours to look back for digests
        verbose: Whether to print progress
    
    Returns:
        CuratorResult with ranked articles, or None on failure
    """
    db = next(get_db())
    
    try:
        # Get digests from last 24 hours
        digest_tuples = DigestRepository.get_recent(db, hours_back=hours_back)
        
        if not digest_tuples:
            if verbose:
                print(f"No digests found in the last {hours_back} hours")
            return CuratorResult(ranked_articles=[], total_processed=0)
        
        # Convert to DigestItem for curator
        digest_items = []
        for digest, source_name in digest_tuples:
            digest_items.append(DigestItem(
                digest_id=digest.id,
                title=digest.title,
                summary=digest.summary,
                url=digest.url,
                source=source_name
            ))
        
        if verbose:
            print(f"Found {len(digest_items)} digests to rank for {user_profile.name}")
        
        # Run curator
        agent = CuratorAgent(verbose=verbose)
        result = agent.rank(digest_items, user_profile)
        
        return result
    
    finally:
        db.close()


def get_ranked_digests_with_details(
    result: CuratorResult,
    db_session
) -> list:
    """
    Enrich ranked result with full digest details for display.
    
    Args:
        result: CuratorResult from run_curator
        db_session: Database session
    
    Returns:
        List of dicts with rank, score, digest details
    """
    from app.database.models import Digest
    
    enriched = []
    for ranked in result.ranked_articles:
        digest = db_session.query(Digest).filter(Digest.id == ranked.digest_id).first()
        if digest:
            enriched.append({
                "rank": ranked.rank,
                "score": ranked.score,
                "relevance_reason": ranked.relevance_reason,
                "title": digest.title,
                "url": digest.url,
                "summary": digest.summary,
                "digest_id": digest.id
            })
    return enriched


def main():
    """Main entry point for curator processor"""
    from app.agent.user_profiles import USER_RESEARCHER
    
    print("Running curator for AI Researcher...")
    
    result = run_curator(
        user_profile=USER_RESEARCHER,
        hours_back=24,
        verbose=True
    )
    
    if result:
        print(f"\nCurator complete!")
        print(f"Total processed: {result.total_processed}")
        print(f"Ranked articles: {len(result.ranked_articles)}")
        print("\nTop 5 ranked:")
        for i, r in enumerate(result.ranked_articles[:5], 1):
            print(f"\n{i}. Title: {r.title} | Score: {r.score:.2f} | Rank: {r.rank}")
            print(f"   Reason: {r.relevance_reason}")
    else:
        print("Curator failed or no digests returned")
    
    return result


if __name__ == "__main__":
    main()
