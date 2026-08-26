
import json
import math
import re

from blogboard.graph.state import BlogState
from blogboard.services.llm import LLMAgentService
from blogboard.config.settings import app_settings
from blogboard.services.prompt_manager import prompt_manager
from .prompts import NEWS_GENERATION_PROMPT


def _read_time(text: str) -> str:
    WORDS_PER_MINUTE = 200
    return f"{math.ceil(len(text.split()) / WORDS_PER_MINUTE)} min"


def _clean_json_response(raw: str) -> str:
    """
    Remove Markdown code fences if the LLM returns JSON inside ```json ...```.
    """
    raw = raw.strip()

    raw = re.sub(
        r"^```json\s*",
        "",
        raw,
        flags=re.IGNORECASE | re.MULTILINE
    )

    raw = re.sub(
        r"^```\s*$",
        "",
        raw,
        flags=re.MULTILINE
    )

    return raw.strip()


def _extract_news_topic(news_summary: str, date: str) -> str:
    """
    Ask the LLM to identify a useful headline/topic from the researched
    news context.

    This does NOT determine the tutorial domain. It only identifies the
    main topic of today's AI news article.
    """

    if not news_summary:
        return f"Latest AI News — {date}"

    llm_service = LLMAgentService(temperature=0.2)

    topic_prompt = f"""
You are an AI technology news editor.

Today's date:
{date}

Below is live research collected about recent AI developments:

--- NEWS RESEARCH ---
{news_summary}
--- END NEWS RESEARCH ---

Identify the single most important and coherent topic/development
that should be used as the focus of today's AI news article.

Return ONLY valid JSON in this exact format:

{{
    "topic": "A concise article topic or headline focus"
}}

Rules:
- Base the topic only on the supplied research.
- Do not invent events or developments.
- Prefer the most significant recent development.
- Keep the topic concise.
- Do not include Markdown.
"""

    response = llm_service.llm.invoke(topic_prompt)
    raw = _clean_json_response(response.content)

    try:
        data = json.loads(raw)
        topic = data.get("topic")

        if topic and isinstance(topic, str):
            return topic.strip()

    except json.JSONDecodeError:
        print("  [WARN] Could not parse topic-selection JSON.")

    # Safe fallback
    return f"Latest AI Developments — {date}"


def news_node(state: BlogState) -> BlogState:
    print("  => [NewsAgent] Running...")

    # ------------------------------------------------------------------
    # NewsAgent always owns the AI News category.
    # Tutorial domains such as ML, DL, NLP, CV, GenAI and Statistics
    # are selected later by the TutorialAgent.
    # ------------------------------------------------------------------
    domain = "ainews"

    date = state.get("date", "")
    existing_news_data = state.get("news_data", "")
    existing_topic = state.get("topic")

    tags_config = app_settings.tags.model_dump()
    cat_label = tags_config.get(domain, {}).get("label", domain)

    # ------------------------------------------------------------------
    # DRY RUN
    # ------------------------------------------------------------------
    if state.get("dry_run"):
        print("  [DRY RUN] Skipping News Research & Generation.")

        topic = existing_topic or f"Latest AI News — {date}"

        return {
            **state,
            "domain": domain,
            "article_type": "ainews",
            "topic": topic,
            "news_data": "Dry run news research context.",
            "content": f"# {topic}\n\nDry run AI News text.",
            "read_time": "1 min",
        }

    # ------------------------------------------------------------------
    # STEP 1: RESEARCH
    #
    # If news_data already exists, reuse it.
    #
    # This is important when Validator rejects the article and the graph
    # sends the state back to NewsAgent. We don't want to perform a new
    # web search every revision.
    # ------------------------------------------------------------------
    news_summary = existing_news_data

    if news_summary:
        print("  [AGENT] Existing news research found. Reusing it.")

    else:
        print("  [AGENT] Researching the web for today's AI news...")

        llm_service = LLMAgentService()

        system_prompt = """
You are an AI news research agent.

Use the available search tools to find the most important recent AI news.

IMPORTANT:
- Use at most 2 search calls total.
- Return at most 3 news stories.
- For each story give only:
  1. Title
  2. Source
  3. Date
  4. 2-3 sentence summary
  5. URL
- Do not reproduce full articles.
- Do not include long search results.
- Keep the final research response under 1500 tokens.
- Do not invent information.
- Do not rely on unsupported claims.

This research will be passed to another LLM that writes the final article.
"""
        research_agent = llm_service.get_news_agent(
            system_prompt=system_prompt
        )

        response = research_agent.invoke(
            {
                "messages": [
                    (
                        "user",
                        f"Research the most important recent AI news "
                        f"for {date}."
                    )
                ]
            }
        )

        news_summary = response["messages"][-1].content

        print(
            f"  [AGENT] Formulated research context "
            f"({len(news_summary)} chars)."
        )

    # ------------------------------------------------------------------
    # STEP 2: SELECT TODAY'S NEWS TOPIC
    #
    # Only select a topic when we don't already have one.
    #
    # During validator revisions, the existing topic is preserved.
    # ------------------------------------------------------------------
    topic = existing_topic

    if not topic:
        print("  [AGENT] Selecting today's main news topic...")

        topic = _extract_news_topic(
            news_summary=news_summary,
            date=date
        )

        print(f"  [AGENT] Selected News Topic: {topic}")

    else:
        print(f"  [AGENT] Existing News Topic: {topic}")

    # ------------------------------------------------------------------
    # STEP 3: GENERATE NEWS ARTICLE
    # ------------------------------------------------------------------
    print("  [AGENT] Drafting the news blog...")

    validator_feedback = ""

    if state.get("validator_feedback"):
        validator_feedback = (
            "CRITICAL FEEDBACK FROM PREVIOUS DRAFT. "
            "You must fix these issues:\n"
            f"{state.get('validator_feedback')}"
        )

    prompt = prompt_manager.get_prompt(
        prompt_name="News_Generation_Prompt",
        fallback_prompt=NEWS_GENERATION_PROMPT,
        cat_label=cat_label,
        topic=topic,
        news_context=news_summary,
        validator_feedback=validator_feedback,
    )

    # Lower temperature for factual news synthesis.
    llm_service_gen = LLMAgentService(temperature=0.4)

    res_gen = llm_service_gen.llm.invoke(prompt)
    print("\n========== RAW NEWS MODEL OUTPUT ==========")
    print(res_gen.content)
    print("========== END RAW OUTPUT ==========\n")

    content = res_gen.content.strip()
    rt = _read_time(content)

    print(
        f"  [AGENT] Generated "
        f"{len(content.split())} words. "
        f"Read time: {rt}"
    )

    # ------------------------------------------------------------------
    # STEP 4: RETURN STATE
    #
    # news_data is deliberately preserved because TutorialAgent will
    # use this context to choose a related tutorial topic/domain.
    # ------------------------------------------------------------------
    return {
        **state,
        "domain": domain,
        "article_type": "ainews",
        "topic": topic,
        "news_data": news_summary,
        "content": content,
        "read_time": rt,
    }


