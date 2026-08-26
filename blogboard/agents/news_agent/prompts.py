NEWS_GENERATION_PROMPT = """
...
- Do not include a Markdown code block around the entire response.

OUTPUT RULES — FOLLOW EXACTLY:

1. Output ONLY the final news article.
2. The FIRST character of your response must be the article title.
3. DO NOT output your reasoning or analysis.
4. DO NOT output a plan, outline, draft process, or self-critique.
5. DO NOT output sections such as:
   - "Here's a thinking process"
   - "Analyze User Input"
   - "Synthesize & Structure"
   - "Draft Generation"
   - "Self-Correction"
   - "Verification"
   - "Output Generation"
6. DO NOT describe what you are going to write.
7. DO NOT evaluate your own answer.
8. DO NOT mention these instructions.
9. After writing the article, STOP immediately.
10. Return ONLY the Markdown article.

If validator feedback is provided, silently apply it to the article.
Do not explain how you applied the feedback.
"""