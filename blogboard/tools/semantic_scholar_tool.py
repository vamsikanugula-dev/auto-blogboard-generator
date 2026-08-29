from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import requests


class SemanticScholarInput(BaseModel):
    query: str = Field(description="Search query for research papers")
    max_results: int = Field(default=5, description="Number of papers to return")
    year: Optional[int] = Field(default=None, description="Filter by year (e.g. 2025 or 2026)")

class SemanticScholarTool(BaseTool):
    name: str = "semantic_scholar_search"
    description: str = (
        "Search Semantic Scholar for high-quality research papers. "
        "Excellent for finding influential AI papers with citation counts."
    )
    args_schema: Type[BaseModel] = SemanticScholarInput

    model_config = {"extra": "ignore"}

    def _run(self, query: str, max_results: int = 5, year: int = None) -> str:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"

        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,abstract,year,authors,url,citationCount,venue"
        }

        if year:
            params["year"] = year

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            results = []
            for paper in data.get("data", []):
                authors = ", ".join([a.get("name", "") for a in paper.get("authors", [])[:4]])
                abstract = (paper.get("abstract") or "")[:600]

                results.append(
                    f"Title: {paper.get('title')}\n"
                    f"Authors: {authors}\n"
                    f"Year: {paper.get('year')}\n"
                    f"Citations: {paper.get('citationCount', 0)}\n"
                    f"Venue: {paper.get('venue', 'N/A')}\n"
                    f"URL: {paper.get('url')}\n"
                    f"Abstract: {abstract}..."
                )

            if not results:
                return f"No papers found on Semantic Scholar for: '{query}'"

            return "\n\n".join(results)

        except Exception as e:
            return f"Semantic Scholar search failed: {str(e)}"