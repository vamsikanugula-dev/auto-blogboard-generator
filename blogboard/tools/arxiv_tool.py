from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import requests
import feedparser
from datetime import datetime, timedelta


class ArxivSearchInput(BaseModel):
    query: str = Field(description="Search query for arXiv papers (e.g. 'mixture of experts LLM')")
    max_results: int = Field(default=5, description="Maximum number of papers to return")
    days: int = Field(default=30, description="Only return papers from the last N days")


class ArxivSearchTool(BaseTool):
    name: str = "arxiv_search"
    description: str = (
        "Search for the latest research papers on arXiv. "
        "Best for technical AI breakthroughs, new architectures, and academic results."
    )
    args_schema: Type[BaseModel] = ArxivSearchInput

    model_config = {"extra": "ignore"}

    def _run(self, query: str, max_results: int = 5, days: int = 30) -> str:
        # arXiv API
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }

        try:
            response = requests.get(base_url, params=params, timeout=15)
            response.raise_for_status()

            feed = feedparser.parse(response.text)
            results = []

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            for entry in feed.entries:
                published = datetime(*entry.published_parsed[:6])
                if published < cutoff_date:
                    continue

                authors = ", ".join([a.name for a in entry.authors[:4]])
                if len(entry.authors) > 4:
                    authors += " et al."

                summary = entry.summary.replace("\n", " ")[:600]

                results.append(
                    f"Title: {entry.title}\n"
                    f"Authors: {authors}\n"
                    f"Published: {published.strftime('%Y-%m-%d')}\n"
                    f"URL: {entry.link}\n"
                    f"Abstract: {summary}..."
                )

            if not results:
                return f"No recent papers found on arXiv for query: '{query}'"

            return "\n\n".join(results)

        except Exception as e:
            return f"arXiv search failed: {str(e)}"