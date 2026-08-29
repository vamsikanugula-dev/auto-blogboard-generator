import re
import json
from typing import Optional, Any


def strip_thinking(text: str) -> str:
    if not text:
        return ""

    # Remove <think>...</think> blocks (important for Qwen3 and similar models)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove other common thinking patterns
    patterns = [
        r"(?i)here's a thinking process:.*?(?=\n#|\Z)",
        r"(?i)thinking process:.*?(?=\n#|\Z)",
        r"(?i)self-correction.*?(?=\n#|\Z)",
        r"(?i)let me (think|draft|plan|analyze).*?(?=\n#|\Z)",
        r"(?i)i will now.*?(?=\n#|\Z)",
        r"(?i)output matches the final response\..*",
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.DOTALL)

    # Keep only from the first real Markdown title
    lines = text.strip().splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            start = i
            break
    text = "\n".join(lines[start:]).strip()

    return text


def try_parse_json_from_llm(text: str) -> Optional[dict[str, Any]]:
    """
    Try to extract and parse a JSON object from LLM output.
    Handles cases where the model adds extra text or markdown.
    """
    if not text:
        return None

    # First try direct parse
    try:
        return json.loads(text.strip())
    except Exception:
        pass

    # Try to find a JSON block
    # Look for content between { and }
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    # Try removing markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None