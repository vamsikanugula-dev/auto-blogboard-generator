import math
import random

from blogboard.graph.state import BlogState
from blogboard.services.llm import LLMAgentService
from blogboard.config.settings import app_settings
from blogboard.services.prompt_manager import prompt_manager
from blogboard.services.llm_output import (
    strip_thinking,
    try_parse_json_from_llm,
)
from .prompts import TUTORIAL_TOPIC_PROMPT, TUTORIAL_GENERATION_PROMPT

# Import the research tools
from blogboard.tools.arxiv_tool import ArxivSearchTool
from blogboard.tools.semantic_scholar_tool import SemanticScholarTool


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


def _research_topic(topic: str, cat_label: str) -> str:
    """
    Perform lightweight research using arXiv + Semantic Scholar
    to enrich the tutorial with real papers and techniques.
    """
    print(f"  [AGENT] Researching papers for topic: {topic}")

    research_context = []

    try:
        arxiv_tool = ArxivSearchTool()
        arxiv_result = arxiv_tool._run(
            query=topic,
            max_results=4,
            days=120
        )
        if arxiv_result and "No recent papers" not in arxiv_result:
            research_context.append("=== arXiv Papers ===\n" + arxiv_result)
    except Exception as e:
        print(f"  [WARN] arXiv research failed: {e}")

    try:
        ss_tool = SemanticScholarTool()
        ss_result = ss_tool._run(
            query=topic,
            max_results=4
        )
        if ss_result and "No papers found" not in ss_result:
            research_context.append("=== Semantic Scholar Papers ===\n" + ss_result)
    except Exception as e:
        print(f"  [WARN] Semantic Scholar research failed: {e}")

    if not research_context:
        return "No additional research papers found."

    combined = "\n\n".join(research_context)
    # Limit size so we don't blow the context window
    return combined[:6000]


# ---------------------------------------------------------
# News -> Tutorial Domain Selection
# ---------------------------------------------------------

def _choose_domain_from_news(news_data: str) -> str:
    if not news_data or not news_data.strip():
        selected = random.choice(TUTORIAL_DOMAINS)
        print(f"  [AGENT] No news context available. Randomly selected domain: {selected}")
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
        f"- {domain}: {label}" for domain, label in domain_labels.items()
    )

    classification_prompt = f"""
You are a domain classification expert for an AI educational blog.

Analyze the following latest AI news context.

Supported tutorial domains:

{domain_list}

IMPORTANT:
- Do NOT select "ainews".
- Select a domain only when the news has a meaningful connection to that domain.
- If the news does not clearly belong to any supported domain, return "none".

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
        response = llm_service.llm.invoke(classification_prompt)
        data = try_parse_json_from_llm(response.content)

        if data:
            selected_domain = data.get("domain", "none")
            if selected_domain in TUTORIAL_DOMAINS:
                print(f"  [AGENT] News matched tutorial domain: {selected_domain}")
                return selected_domain

    except Exception as e:
        print(f"  [WARN] Domain classification failed: {e}")

    selected_domain = random.choice(TUTORIAL_DOMAINS)
    print(f"  [AGENT] No clear domain found. Randomly selected domain: {selected_domain}")
    return selected_domain


# ---------------------------------------------------------
# Main Tutorial Agent
# ---------------------------------------------------------

def tutorial_node(state: BlogState) -> BlogState:
    print("  => [TutorialAgent] Running...")

    is_first_tutorial_pass = state.get("domain") == "ainews"

    # -----------------------------------------------------
    # Step 1: Select Tutorial Domain + Topic
    # -----------------------------------------------------
    if is_first_tutorial_pass:
        news_data = state.get("news_data", "")

        target_domain = _choose_domain_from_news(news_data)

        tags_config = app_settings.tags.model_dump()
        cat_label = tags_config.get(target_domain, {}).get("label", target_domain)

        print(f"  [AGENT] Tutorial domain selected: {target_domain}")

        from blogboard.services.storage import SupabaseStorageService
        storage = SupabaseStorageService()

        recent_history = storage.get_recent_history(target_domain, limit=3)

        history_str = "No recent history found."
        if recent_history:
            history_str = "\n---\n".join(
                [
                    f"Title: {item['title']}\nTopic: {item['topic']}\nSubtopics: {item['subtopics']}"
                    for item in recent_history
                ]
            )

        topic_prompt = prompt_manager.get_prompt(
            prompt_name="Tutorial_Topic_Prompt",
            fallback_prompt=TUTORIAL_TOPIC_PROMPT,
            news_context=news_data[:12000],
            cat_label=cat_label,
            history=history_str,
        )

        try:
            llm_service = LLMAgentService(temperature=0.7)
            response = llm_service.llm.invoke(topic_prompt)
            topic_data = try_parse_json_from_llm(response.content)

            if not topic_data:
                raise ValueError("Topic generation returned invalid JSON.")

            topic = topic_data.get("topic", f"Emerging Concepts in {cat_label}")
            subtopics = topic_data.get("subtopics", "")

        except Exception as e:
            print(f"  [WARN] Topic generation failed: {e}")
            topic = f"Emerging Concepts in {cat_label}"
            subtopics = ""

        print(f"  [AGENT] Picked Tutorial Topic: {topic}")

    else:
        # Revision pass
        target_domain = state.get("domain", random.choice(TUTORIAL_DOMAINS))
        topic = state.get("topic", "Advanced AI Concepts")
        subtopics = state.get("subtopics", "")

        tags_config = app_settings.tags.model_dump()
        cat_label = tags_config.get(target_domain, {}).get("label", target_domain)

        print(f"  [AGENT] Revising tutorial in domain: {target_domain}")
        print(f"  [AGENT] Keeping tutorial topic: {topic}")

    # -----------------------------------------------------
    # Step 2: Dry Run
    # -----------------------------------------------------
    if state.get("dry_run"):
        print("  [DRY RUN] Skipping LLM Generation.")
        return {
            **state,
            "domain": target_domain,
            "article_type": "tutorial",
            "topic": topic,
            "subtopics": subtopics,
            "content": f"# {topic}\n\nDry run tutorial text.",
            "read_time": "1 min",
            "revision_count": 0 if is_first_tutorial_pass else state.get("revision_count", 0),
        }

    # -----------------------------------------------------
    # Step 3: Research papers for richer content
    # -----------------------------------------------------
    research_context = _research_topic(topic, cat_label)

    # -----------------------------------------------------
    # Step 4: Validator Feedback
    # -----------------------------------------------------
    validator_feedback = ""
    if state.get("validator_feedback"):
        validator_feedback = (
            "CRITICAL FEEDBACK FROM PREVIOUS DRAFT. "
            "You must fix these issues:\n"
            f"{state.get('validator_feedback')}"
        )

    # -----------------------------------------------------
    # Step 5: Tutorial Content Generation
    # -----------------------------------------------------
    generation_prompt = prompt_manager.get_prompt(
        prompt_name="Tutorial_Generation_Prompt",
        fallback_prompt=TUTORIAL_GENERATION_PROMPT,
        cat_label=cat_label,
        topic=topic,
        subtopics=subtopics,
        validator_feedback=validator_feedback,
    )

    # Inject research into the prompt
    full_generation_prompt = f"""
{generation_prompt}

--- RESEARCH CONTEXT (use this to make the tutorial more concrete and up-to-date) ---
{research_context}
--- END RESEARCH CONTEXT ---

Important:
- Use the research papers to add real techniques, paper names, and concrete examples where relevant.
- Do not invent papers.
- Still output ONLY the final clean Markdown tutorial.
"""

    llm_service_gen = LLMAgentService(temperature=0.45)

    res_gen = llm_service_gen.llm.invoke(full_generation_prompt)
    content = strip_thinking(res_gen.content)

    # ========== HARD FORMAT GUARD ==========
    bad_signals = [
        "here's a thinking process",
        "thinking process:",
        "self-correction",
        "i will now write",
        "let me draft",
        "output matches the final response",
        "proceeds.",
        "self-critique",
        "<think>",
    ]

    content_lower = content.lower()
    is_bad = (
        any(sig in content_lower for sig in bad_signals)
        or not content.strip().startswith("#")
        or len(content.split()) < 60
    )

    if is_bad:
        print("  [WARN] Detected thinking/planning text or weak content. Forcing clean rewrite...")

        strict_prompt = f"""
You must output ONLY the final Markdown tutorial article.
- First line must start with #
- Absolutely no <think> tags
- No reasoning, planning, or commentary
- Write a complete, high-quality technical tutorial

Category: {cat_label}
Topic: {topic}
Subtopics: {subtopics}

Research context:
{research_context[:3000]}

{validator_feedback}

Write the complete tutorial now:
"""
        res_retry = llm_service_gen.llm.invoke(strict_prompt)
        content = strip_thinking(res_retry.content)

        # Final safety net
        if not content.strip().startswith("#") or len(content.split()) < 40:
            print("  [ERROR] Rewrite also failed. Using emergency fallback.")
            content = f"""# {topic}

## Introduction
This tutorial covers key concepts in {cat_label}.

## Main Concepts
{subtopics}

## Conclusion
Further exploration of these topics is recommended for practical applications.
"""
    # =======================================

    rt = _read_time(content)

    print(f"  [AGENT] Generated {len(content.split())} words. Read time: {rt}")

    # -----------------------------------------------------
    # Step 6: Return Updated State
    # -----------------------------------------------------
    return {
        **state,
        "domain": target_domain,
        "article_type": "tutorial",
        "topic": topic,
        "subtopics": subtopics,
        "content": content,
        "read_time": rt,
        "revision_count": 0 if is_first_tutorial_pass else state.get("revision_count", 0),
    }