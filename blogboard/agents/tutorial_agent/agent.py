
import json
import re
import math
import random

from blogboard.graph.state import BlogState
from blogboard.services.llm import LLMAgentService
from blogboard.config.settings import app_settings
from blogboard.services.prompt_manager import prompt_manager
from .prompts import TUTORIAL_TOPIC_PROMPT, TUTORIAL_GENERATION_PROMPT


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

TUTORIAL_DOMAINS = [
    "ml",
    "dl",
    "statistics",
    "nlp",
    "cv",
    "genai",
]


# ---------------------------------------------------------
# Utility
# ---------------------------------------------------------

def _read_time(text: str) -> str:
    WORDS_PER_MINUTE = 200
    return f"{math.ceil(len(text.split()) / WORDS_PER_MINUTE)} min"


def _clean_json_response(raw: str) -> str:
    """
    Remove markdown JSON fences if the LLM returns them.
    """

    raw = raw.strip()

    raw = re.sub(
        r"^```json\s*",
        "",
        raw,
        flags=re.IGNORECASE
    )

    raw = re.sub(
        r"^```\s*",
        "",
        raw
    )

    raw = re.sub(
        r"```\s*$",
        "",
        raw
    )

    return raw.strip()


# ---------------------------------------------------------
# News -> Tutorial Domain Selection
# ---------------------------------------------------------

def _choose_domain_from_news(news_data: str) -> str:
    """
    Determine which tutorial domain best matches the latest news.

    If the news does not clearly belong to one of the supported
    tutorial domains, randomly select a domain.

    ainews is deliberately excluded because it belongs to the
    News Agent.
    """

    # Safety fallback
    if not news_data or not news_data.strip():
        selected = random.choice(TUTORIAL_DOMAINS)

        print(
            f"  [AGENT] No news context available. "
            f"Randomly selected domain: {selected}"
        )

        return selected

    print("  [AGENT] Analyzing news context for tutorial domain...")

    domain_labels = {
        "ml": "Machine Learning",
        "dl": "Deep Learning",
        "statistics": "Statistics for AI",
        "nlp": "Natural Language Processing",
        "cv": "Computer Vision",
        "genai": "Generative AI",
    }

    domain_list = "\n".join(
        f"- {domain}: {label}"
        for domain, label in domain_labels.items()
    )

    classification_prompt = f"""
You are a domain classification expert for an AI educational blog.

Analyze the following latest AI news context.

Your job is to determine whether the news clearly maps to one
of the supported tutorial domains.

Supported tutorial domains:

{domain_list}

IMPORTANT:
- Do NOT select "ainews".
- Select a domain only when the news has a meaningful connection
  to that domain.
- If the news does not clearly belong to any supported domain,
  return "none".
- Do not force a category just because one is loosely related.

Return ONLY valid JSON in exactly this format:

{{
    "domain": "ml"
}}

or:

{{
    "domain": "none"
}}

NEWS CONTEXT:
----------------
{news_data[:12000]}
----------------
"""

    try:
        llm_service = LLMAgentService(temperature=0.0)

        response = llm_service.llm.invoke(
            classification_prompt
        )

        raw = _clean_json_response(response.content)

        data = json.loads(raw)

        selected_domain = data.get("domain", "none")

        if selected_domain in TUTORIAL_DOMAINS:
            print(
                f"  [AGENT] News matched tutorial domain: "
                f"{selected_domain}"
            )

            return selected_domain

    except Exception as e:
        print(
            f"  [WARN] Domain classification failed: {e}"
        )

    # -----------------------------------------------------
    # Random fallback
    # -----------------------------------------------------

    selected_domain = random.choice(TUTORIAL_DOMAINS)

    print(
        f"  [AGENT] No clear domain found. "
        f"Randomly selected domain: {selected_domain}"
    )

    return selected_domain


# ---------------------------------------------------------
# Main Tutorial Agent
# ---------------------------------------------------------

def tutorial_node(state: BlogState) -> BlogState:
    print("  => [TutorialAgent] Running...")

    storage = None

    # -----------------------------------------------------
    # Determine whether this is the first Tutorial pass
    # or a revision.
    #
    # After News Agent:
    #     domain == "ainews"
    #
    # After Tutorial Agent:
    #     domain == selected tutorial domain
    #
    # Therefore we can safely use "ainews" to identify
    # that we are entering the Tutorial stage for the
    # first time.
    # -----------------------------------------------------

    is_first_tutorial_pass = state.get("domain") == "ainews"

    # -----------------------------------------------------
    # Step 1: Select Tutorial Domain
    # -----------------------------------------------------

    if is_first_tutorial_pass:

        news_data = state.get("news_data", "")

        # Choose domain from today's news.
        target_domain = _choose_domain_from_news(
            news_data
        )

        tags_config = app_settings.tags.model_dump()

        cat_label = tags_config.get(
            target_domain,
            {}
        ).get(
            "label",
            target_domain
        )

        print(
            f"  [AGENT] Tutorial domain selected: "
            f"{target_domain}"
        )

        # -------------------------------------------------
        # Get previous articles from this domain.
        #
        # This helps avoid generating the exact same
        # tutorial topic repeatedly.
        # -------------------------------------------------

        from blogboard.services.storage import (
            SupabaseStorageService
        )

        storage = SupabaseStorageService()

        recent_history = storage.get_recent_history(
            target_domain,
            limit=3
        )

        history_str = "No recent history found."

        if recent_history:
            history_str = "\n---\n".join(
                [
                    (
                        f"Title: {item['title']}\n"
                        f"Topic: {item['topic']}\n"
                        f"Subtopics: {item['subtopics']}"
                    )
                    for item in recent_history
                ]
            )

        # -------------------------------------------------
        # Generate a tutorial topic related to today's news.
        # -------------------------------------------------

        topic_prompt = f"""
You are the topic-selection component of an AI educational
blog generation system.

Today's AI news context:

----------------
{news_data[:12000]}
----------------

The selected tutorial domain is:

{cat_label}

Previous tutorials in this domain:

----------------
{history_str}
----------------

Generate ONE educational tutorial topic that:

1. Is meaningfully related to today's AI news.
2. Belongs to the selected domain.
3. Teaches an underlying technical concept.
4. Is not simply a summary of the news.
5. Does not duplicate the previous tutorials.
6. Is suitable for a technical AI/ML blog.

Return ONLY valid JSON:

{{
    "topic": "Tutorial topic",
    "subtopics": "Subtopic 1, Subtopic 2, Subtopic 3, Subtopic 4"
}}
"""

        try:
            llm_service = LLMAgentService(
                temperature=0.8
            )

            response = llm_service.llm.invoke(
                topic_prompt
            )

            raw = _clean_json_response(
                response.content
            )

            topic_data = json.loads(raw)

            topic = topic_data.get(
                "topic",
                f"Emerging Concepts in {cat_label}"
            )

            subtopics = topic_data.get(
                "subtopics",
                ""
            )

        except Exception as e:
            print(
                f"  [WARN] Topic generation failed: {e}"
            )

            topic = (
                f"Emerging Concepts in "
                f"{cat_label}"
            )

            subtopics = ""

        print(
            f"  [AGENT] Picked Tutorial Topic: "
            f"{topic}"
        )

    else:
        # -------------------------------------------------
        # Revision pass.
        #
        # Keep the already-selected tutorial domain/topic.
        # Do NOT randomly choose a new domain again.
        # -------------------------------------------------

        target_domain = state.get(
            "domain",
            random.choice(TUTORIAL_DOMAINS)
        )

        topic = state.get(
            "topic",
            "Advanced AI Concepts"
        )

        subtopics = state.get(
            "subtopics",
            ""
        )

        tags_config = app_settings.tags.model_dump()

        cat_label = tags_config.get(
            target_domain,
            {}
        ).get(
            "label",
            target_domain
        )

        print(
            f"  [AGENT] Revising tutorial in domain: "
            f"{target_domain}"
        )

        print(
            f"  [AGENT] Keeping tutorial topic: "
            f"{topic}"
        )

    # -----------------------------------------------------
    # Step 2: Dry Run
    # -----------------------------------------------------

    if state.get("dry_run"):

        print(
            "  [DRY RUN] Skipping LLM Generation."
        )

        return {
            **state,
            "domain": target_domain,
            "article_type": "tutorial",
            "topic": topic,
            "subtopics": subtopics,
            "content": (
                f"# {topic}\n\n"
                "Dry run tutorial text."
            ),
            "read_time": "1 min"
        }

    # -----------------------------------------------------
    # Step 3: Validator Feedback
    # -----------------------------------------------------

    validator_feedback = ""

    if state.get("validator_feedback"):

        validator_feedback = (
            "CRITICAL FEEDBACK FROM PREVIOUS DRAFT. "
            "You must fix these issues:\n"
            f"{state.get('validator_feedback')}"
        )

    # -----------------------------------------------------
    # Step 4: Tutorial Content Generation
    # -----------------------------------------------------

    # We keep using your existing prompt manager here.
    #
    # The selected domain, topic and subtopics are supplied
    # exactly as before.

    generation_prompt = prompt_manager.get_prompt(
        prompt_name="Tutorial_Generation_Prompt",
        fallback_prompt=TUTORIAL_GENERATION_PROMPT,
        cat_label=cat_label,
        topic=topic,
        subtopics=subtopics,
        validator_feedback=validator_feedback
    )

    llm_service_gen = LLMAgentService(
        temperature=0.6
    )

    res_gen = llm_service_gen.llm.invoke(
        generation_prompt
    )

    content = res_gen.content.strip()

    rt = _read_time(content)

    print(
        f"  [AGENT] Generated "
        f"{len(content.split())} words. "
        f"Read time: {rt}"
    )

    # -----------------------------------------------------
    # Step 5: Return Updated State
    # -----------------------------------------------------

    return {
        **state,
        "domain": target_domain,
        "article_type": "tutorial",
        "topic": topic,
        "subtopics": subtopics,
        "content": content,
        "read_time": rt
    }

