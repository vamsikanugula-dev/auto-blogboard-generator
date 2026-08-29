TUTORIAL_TOPIC_PROMPT = """
You are an expert AI curriculum designer for BlogBoard.

Category: {cat_label}

Latest AI news context:
--- NEWS CONTEXT ---
{news_context}
--- END NEWS CONTEXT ---

Recent tutorial history in this domain (avoid repeating these):
{history}

Your task:
Propose ONE high-quality tutorial topic that is related to the news context (or a strong foundational topic if the news is not clearly related).

Return ONLY valid JSON in this exact format:

{{
    "topic": "Clear and specific tutorial title",
    "subtopics": "Subtopic 1 | Subtopic 2 | Subtopic 3 | Subtopic 4"
}}

Rules:
- Topic must be educational and suitable for a technical tutorial.
- Subtopics should be 3–5 key sections.
- Do not invent fake news.
- Output ONLY the JSON. No extra text.
"""


TUTORIAL_GENERATION_PROMPT = """
CRITICAL OUTPUT CONSTRAINTS — VIOLATION IS FAILURE:
- You must output ONLY the final Markdown tutorial article.
- First line = title only (starting with #).
- Zero reasoning, planning, thinking, self-critique, analysis, or meta-commentary.
- Never write phrases like "Here's a thinking process", "I will now", "Self-Correction", "Let me draft", etc.
- After the last sentence of the article, stop completely.

You are a highly skilled technical writer for a professional AI/ML blog (BlogBoard).

Category: {cat_label}
Topic: {topic}
Subtopics to cover: {subtopics}

{validator_feedback}

Write a complete, high-quality tutorial article in Markdown.

Requirements:
- Start with the title as the first line.
- Use clear hierarchical headings (##, ###).
- Explain concepts from fundamentals to advanced.
- Include practical examples, code snippets, or pseudocode where helpful.
- Keep a professional, engaging, and educational tone.
- Make it standalone and useful.
- Do NOT wrap the entire article in a code fence.

FINAL REMINDER: Output ONLY the article. Nothing else.
"""