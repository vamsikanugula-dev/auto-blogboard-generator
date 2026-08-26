
TUTORIAL_TOPIC_PROMPT = """
You are an expert content strategist for a technical AI/ML blog.

Today's AI news context:
{news_context}

Selected Tutorial Domain:
{cat_label}

Recent History of articles published in this domain:
{history}

Your task is to select ONE exciting, technically valuable tutorial topic.

Follow these rules carefully:

1. If today's AI news has a meaningful technical connection to the selected
   tutorial domain, create a tutorial that teaches an underlying technical
   concept related to that news.

2. Do NOT simply summarize or rewrite the news article.
   The tutorial must teach a deeper technical concept.

3. If the selected domain was chosen randomly because the news did not have
   a meaningful connection to any tutorial domain, create an independent,
   high-quality tutorial topic appropriate for the selected domain.

4. The topic must belong clearly to the selected domain.

5. Do not duplicate or closely repeat any topic from the recent history.

6. Prefer technically useful topics that help readers understand concepts,
   algorithms, architectures, methods, or practical techniques.

7. Return ONLY valid JSON.

Return exactly:

{{
  "topic": "The title of the new tutorial topic",
  "subtopics": "A comma-separated list of 3-4 subtopics to cover"
}}
"""


TUTORIAL_GENERATION_PROMPT = """
You are a highly skilled technical writer for a professional AI/ML blog.

Domain/Category:
{cat_label}

Topic:
{topic}

Subtopics to cover:
{subtopics}

{validator_feedback}

Write a comprehensive, technically accurate, highly engaging tutorial
blog post in Markdown format.

The article should:

- Clearly explain the core technical concepts.
- Build understanding from fundamentals to more advanced ideas where
  appropriate.
- Use appropriate Markdown headings and subheadings.
- Include examples, equations, pseudocode, or code when they genuinely
  improve understanding.
- Maintain a professional technical-writing style.
- Avoid unsupported factual claims.
- Do not simply repeat a news article.
- Focus primarily on teaching the technical concept represented by the topic.
- Make the article useful as a standalone tutorial.

Do not include a Markdown code block around the entire response.

IMPORTANT:
Return ONLY the final article.
Do NOT output reasoning, analysis, planning, thinking process, or self-correction.
Do NOT include "Here's a thinking process" or similar text.
Start directly with the article title.
"""
