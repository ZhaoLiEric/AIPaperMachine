from __future__ import annotations

import time
from typing import List

import requests

from .models import Paper


class SemanticScholarProvider:
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout

    def search(
        self,
        query: str,
        venue: str,
        year_from: int,
        limit: int,
    ) -> List[Paper]:
        params = {
            "query": f"{query} venue:{venue}",
            "fields": "title,abstract,authors,year,venue,citationCount,url",
            "limit": min(limit, 100),
            "year": f"{year_from}-",
            "sort": "citationCount:desc",
        }
        response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json().get("data", [])

        papers: List[Paper] = []
        for item in data:
            title = (item.get("title") or "").strip()
            abstract = (item.get("abstract") or "").strip()
            year = item.get("year")
            if not title or not abstract or not year:
                continue
            authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
            papers.append(
                Paper(
                    paper_id=item.get("paperId", ""),
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    year=int(year),
                    venue=item.get("venue") or venue,
                    citation_count=int(item.get("citationCount") or 0),
                    url=item.get("url") or "",
                )
            )
        return papers

    def batch_search(
        self,
        query: str,
        venues: List[str],
        year_from: int,
        per_venue_limit: int,
    ) -> List[Paper]:
        all_papers: List[Paper] = []
        for venue in venues:
            try:
                all_papers.extend(
                    self.search(
                        query=query,
                        venue=venue,
                        year_from=year_from,
                        limit=per_venue_limit,
                    )
                )
                time.sleep(0.2)
            except requests.RequestException:
                continue

        unique = {}
        for p in all_papers:
            key = p.paper_id or f"{p.title}-{p.year}"
            if key not in unique:
                unique[key] = p
        return list(unique.values())
