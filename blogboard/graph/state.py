
from typing import TypedDict, List, Dict, Any


class BlogState(TypedDict, total=False):

    # ---------------------------------------------------------
    # Core Metadata
    # ---------------------------------------------------------

    domain: str
    topic: str
    subtopics: str
    date: str
    schedule: Dict[str, Any]
    dry_run: bool
    news_only: bool

    # ---------------------------------------------------------
    # Article Type
    #
    # "ainews"   -> AI News article
    # "tutorial" -> Educational tutorial article
    # ---------------------------------------------------------

    article_type: str

    # ---------------------------------------------------------
    # News Context
    # ---------------------------------------------------------

    recent_blogs: List[str]
    news_data: str

    # ---------------------------------------------------------
    # Generation State
    # ---------------------------------------------------------

    title: str
    description: str
    tags: List[str]
    slug: str
    content: str
    read_time: str

    # ---------------------------------------------------------
    # Validation Loop
    # ---------------------------------------------------------

    validator_feedback: str
    revision_count: int
    revision_needed: bool

    # ---------------------------------------------------------
    # Final Output
    # ---------------------------------------------------------

    md_path: str
    skipped: bool

