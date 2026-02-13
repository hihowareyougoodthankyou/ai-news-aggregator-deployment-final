"""Test user profiles for curator agent"""

import os
from dotenv import load_dotenv

from app.agent.curator_models import UserProfile

load_dotenv()


# User 1: AI researcher focused on LLMs and safety
USER_RESEARCHER = UserProfile(
    name="AI Researcher",
    email=os.getenv("EMAIL_RECIPIENT", "recipient@example.com"),
    interests=[
        "large language models",
        "AI safety and alignment",
        "model capabilities",
        "research papers",
        "machine learning"
    ],
    focus_areas=[
        "model scaling",
        "safety evaluation",
        "interpretability"
    ],
    exclude_topics=["marketing", "product announcements"]
)

# User 2: Product builder interested in AI tooling (uncomment to test)
# USER_BUILDER = UserProfile(
#     name="Product Builder",
#     email=os.getenv("EMAIL_RECIPIENT", "recipient@example.com"),
#     interests=[
#         "AI APIs",
#         "developer tools",
#         "SDKs and integrations",
#         "product launches",
#         "coding assistants"
#     ],
#     focus_areas=[
#         "Claude API",
#         "GPT models",
#         "agent frameworks",
#         "Xcode"
#     ],
#     exclude_topics=[]
# )

# User 3: Business/enterprise focus (uncomment to test)
# USER_ENTERPRISE = UserProfile(
#     name="Enterprise User",
#     email=os.getenv("EMAIL_RECIPIENT", "recipient@example.com"),
#     interests=[
#         "enterprise AI",
#         "partnerships",
#         "deployments",
#         "compliance",
#         "governance"
#     ],
#     focus_areas=[
#         "government",
#         "financial services",
#         "healthcare",
#         "education"
#     ],
#     exclude_topics=[]
# )
