import json
import re
from datetime import datetime, timezone, timedelta

from blogboard.graph.state import BlogState
from blogboard.services.llm import LLMAgentService
from blogboard.services.storage import SupabaseStorageService
from blogboard.services.prompt_manager import prompt_manager
from .prompts import VALIDATOR_PROMPT


def _today_ist() -> str:
    """Return today's date in Indian Standard Time."""
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d")


def _make_slug(value: str) -> str:
    """Create a safe URL/storage slug."""
    if not value:
        return "untitled-article"

    slug = value.strip().lower()

    # Remove characters that are not letters, numbers,
    # whitespace, underscores, or hyphens.
    slug = re.sub(r"[^\w\s-]", "", slug)

    # Convert whitespace/underscores into hyphens.
    slug = re.sub(r"[\s_]+", "-", slug)

    # Collapse multiple hyphens.
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens.
    slug = slug.strip("-")

    return slug[:120] or "untitled-article"


def _clean_llm_json(raw: str) -> str:
    """Remove common Markdown code fences around JSON."""
    raw = raw.strip()

    raw = re.sub(
        r"^```(?:json)?\s*",
        "",
        raw,
        flags=re.IGNORECASE
    )

    raw = re.sub(
        r"\s*```$",
        "",
        raw
    )

    return raw.strip()


def validator_node(state: BlogState) -> BlogState:
    print("  => [ValidatorAgent] Running...")

    # ─────────────────────────────────────────────────────────────
    # DRY RUN
    # ─────────────────────────────────────────────────────────────
    if state.get("dry_run"):
        print("  [DRY RUN] Simulating Approval and Metadata Gen.")

        domain = state.get("domain", "ml")
        article_type = state.get("article_type", "blog")
        topic = state.get("topic", "Dry Run Article")

        print(f"  [DRY RUN] Domain       : {domain}")
        print(f"  [DRY RUN] Article Type : {article_type}")

        slug = _make_slug(topic)

        return {
            **state,
            "domain": domain,
            "article_type": article_type,
            "revision_needed": False,
            "title": "Dry Run Generated Title",
            "slug": slug,
            "md_path": f"supabase://blogs/{domain}/{slug}.md",
            "description": "Dry run generic description.",
        }

    # ─────────────────────────────────────────────────────────────
    # READ STATE
    # ─────────────────────────────────────────────────────────────
    current_revision = state.get("revision_count", 0)

    topic = state.get("topic") or "Untitled Article"
    content = state.get("content", "")

    domain = state.get("domain")

    # Read article_type from the state.
    # NewsAgent should have already set this to "ainews".
    article_type = state.get("article_type", "blog")

    date = state.get("date") or _today_ist()

    # ─────────────────────────────────────────────────────────────
    # VALIDATE REQUIRED DOMAIN
    #
    # Validator must NEVER decide the domain.
    # The generation agent is responsible for selecting it.
    # ─────────────────────────────────────────────────────────────
    if not domain:
        print("  [ERROR] No domain found in state.")

        return {
            **state,
            "revision_needed": True,
            "validator_feedback": (
                "Article domain is missing. "
                "The generation agent must provide a valid domain."
            ),
        }

    # ─────────────────────────────────────────────────────────────
    # LOG CURRENT ARTICLE INFORMATION
    # ─────────────────────────────────────────────────────────────
    print(f"  [VALIDATOR] Domain       : {domain}")
    print(f"  [VALIDATOR] Article Type : {article_type}")
    print(f"  [VALIDATOR] Topic        : {topic}")
    print(f"  [VALIDATOR] Date         : {date}")

    # ─────────────────────────────────────────────────────────────
    # VALIDATION PROMPT
    # ─────────────────────────────────────────────────────────────
    prompt = prompt_manager.get_prompt(
        prompt_name="Validator_Prompt",
        fallback_prompt=VALIDATOR_PROMPT,
        topic=topic,
        content=content,
        article_type=article_type,
        domain=domain,
        date=date,
    )

    # ─────────────────────────────────────────────────────────────
    # RUN LLM VALIDATOR
    # ─────────────────────────────────────────────────────────────
    llm_service = LLMAgentService(temperature=0.1)

    res = llm_service.llm.invoke(prompt)

    raw = _clean_llm_json(res.content)

    # ─────────────────────────────────────────────────────────────
    # PARSE VALIDATOR RESPONSE
    # ─────────────────────────────────────────────────────────────
    try:
        data = json.loads(raw)

        approved = bool(data.get("approved", True))

        feedback = str(
            data.get("feedback", "") or ""
        ).strip()

        title = str(
            data.get("title") or topic
        ).strip()

        description = str(
            data.get("description")
            or f"A blog post about {topic}"
        ).strip()

        requested_slug = str(
            data.get("slug") or title
        ).strip()

        slug_value = _make_slug(requested_slug)

    except (json.JSONDecodeError, TypeError, ValueError) as exc:

        print(
            "  [WARN] Validator failed to return valid JSON. "
            f"Using approval fallback. Error: {exc}"
        )

        approved = True
        feedback = ""

        title = (
            topic[:70].strip()
            if topic
            else "Untitled Article"
        )

        description = (
            f"A blog post about {title}"
        )

        slug_value = _make_slug(title)

    # ─────────────────────────────────────────────────────────────
    # REVISION LIMIT
    # ─────────────────────────────────────────────────────────────
    MAX_REVISIONS = 3

    if not approved and current_revision >= MAX_REVISIONS:
        print(
            "  [WARN] Maximum revisions reached. "
            "Forcing approval."
        )

        approved = True

    revision_needed = not approved

    # ─────────────────────────────────────────────────────────────
    # REJECTED ARTICLE
    # ─────────────────────────────────────────────────────────────
    if revision_needed:

        print(
            f"  [AGENT] Draft REJECTED. "
            f"Revision {current_revision + 1}/{MAX_REVISIONS}"
        )

        print(
            f"  [AGENT] Feedback: {feedback}"
        )

        return {
            **state,
            "domain": domain,
            "article_type": article_type,
            "revision_needed": True,
            "validator_feedback": feedback,
            "revision_count": current_revision + 1,
        }

    # ─────────────────────────────────────────────────────────────
    # APPROVED ARTICLE
    # ─────────────────────────────────────────────────────────────
    print(
        "  [AGENT] Draft APPROVED! "
        "Generating Metadata and Saving to Supabase..."
    )

    # ─────────────────────────────────────────────────────────────
    # BUILD STORAGE PATH
    # ─────────────────────────────────────────────────────────────
    md_relative = f"blogs/{domain}/{slug_value}.md"

    storage = SupabaseStorageService()

    # ─────────────────────────────────────────────────────────────
    # SAVE MARKDOWN ARTICLE
    # ─────────────────────────────────────────────────────────────
    storage.put_object(
        md_relative,
        content,
        content_type="text/markdown"
    )

    print(
        f"  [STORAGE] Saved article: {md_relative}"
    )

    # ─────────────────────────────────────────────────────────────
    # LOAD EXISTING ARTICLES FOR THIS DOMAIN
    # ─────────────────────────────────────────────────────────────
    articles = storage.get_articles_json(domain)

    if not isinstance(articles, list):
        articles = []

    # Remove an existing entry with the same ID OR file path.
    # This prevents duplicate registry entries if the same article
    # is regenerated.
    articles = [
        article
        for article in articles
        if (
            article.get("id") != md_relative
            and article.get("file") != md_relative
        )
    ]

    # ─────────────────────────────────────────────────────────────
    # ARTICLE METADATA
    # ─────────────────────────────────────────────────────────────
    article_metadata = {
        "id": md_relative,

        # Existing category/domain
        "category": domain,

        # New article type
        "article_type": article_type,

        "topic": topic,
        "subtopics": state.get("subtopics", ""),
        "title": title,
        "description": description,
        "date": date,
        "tags": [domain],
        "readTime": state.get("read_time", "5 min"),
        "file": md_relative,
    }

    articles.append(article_metadata)

    # ─────────────────────────────────────────────────────────────
    # SORT BY DATE — NEWEST FIRST
    # ─────────────────────────────────────────────────────────────
    articles = sorted(
        articles,
        key=lambda article: article.get("date", ""),
        reverse=True
    )

    # ─────────────────────────────────────────────────────────────
    # SAVE ARTICLES.JSON
    # ─────────────────────────────────────────────────────────────
    storage.save_articles_json(
        domain,
        articles
    )

    print(
        f"  [STORAGE] Updated blogs/{domain}/articles.json"
    )

    # ─────────────────────────────────────────────────────────────
    # RETURN UPDATED STATE
    # ─────────────────────────────────────────────────────────────
    return {
        **state,

        "domain": domain,
        "article_type": article_type,

        "revision_needed": False,
        "validator_feedback": "",

        "title": title,
        "description": description,
        "slug": slug_value,
        "md_path": f"supabase://{md_relative}",
    }