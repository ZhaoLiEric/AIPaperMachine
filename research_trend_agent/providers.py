from __future__ import annotations

import os
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple

import requests

from .models import Paper

# S2 API Key
DEFAULT_S2_API_KEY = "R6PVFB70Ih5JoDZEnE7ai9bABfzpk1vV7fHPunHE"

# 会议缩写 -> 可能出现在 venue 字段的关键词（小写匹配）
VENUE_ALIASES = {
    "NeurIPS": ["neurips", "neural information processing", "advances in neural"],
    "ICML": ["icml", "international conference on machine learning"],
    "ICLR": ["iclr", "international conference on learning representations"],
    "ACL": ["acl", "association for computational linguistics"],
    "EMNLP": ["emnlp", "empirical methods in natural language"],
    "NAACL": ["naacl", "north american chapter"],
    "COLING": ["coling", "computational linguistics"],
    "EACL": ["eacl", "european chapter"],
    "CVPR": ["cvpr", "computer vision and pattern recognition"],
    "ICCV": ["iccv", "international conference on computer vision"],
    "ECCV": ["eccv", "european conference on computer vision"],
    "AAAI": ["aaai", "association for the advancement of artificial intelligence"],
    "IJCAI": ["ijcai", "international joint conference on artificial intelligence"],
    "KDD": ["kdd", "knowledge discovery and data mining"],
    "IEEE S&P": ["ieee s&p", "ieee symposium on security", "security and privacy"],
    "USENIX Security": ["usenix security"],
    "CCS": ["ccs", "computer and communications security"],
    "NDSS": ["ndss", "network and distributed system security"],
    "OSDI": ["osdi", "operating systems design and implementation"],
    "SOSP": ["sosp", "symposium on operating systems"],
    "NSDI": ["nsdi", "networked systems design and implementation"],
    "USENIX ATC": ["usenix atc", "usenix annual technical"],
}


def _venue_matches(venue_str: str, target: str) -> bool:
    """判断论文的 venue 字段是否匹配目标会议（模糊匹配）。"""
    v = venue_str.lower()
    aliases = VENUE_ALIASES.get(target, [target.lower()])
    return any(alias in v for alias in aliases)


class SemanticScholarProvider:
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30) -> None:
        self.timeout = timeout
        key = api_key or os.environ.get("S2_API_KEY") or DEFAULT_S2_API_KEY
        self.headers = {"x-api-key": key} if key else {}

    def _get(self, params: dict) -> list:
        """带限流重试的 GET 请求，遇到 429 自动等待后重试。"""
        for attempt in range(4):
            try:
                response = requests.get(
                    self.BASE_URL, params=params,
                    headers=self.headers, timeout=self.timeout
                )
                if response.status_code == 429:
                    wait = 15 * (attempt + 1)
                    print(f"        [S2 限流] 等待 {wait}s 后重试...", flush=True)
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return response.json().get("data", [])
            except requests.RequestException as e:
                print(f"        [S2 请求错误] {e}", flush=True)
                break
        return []

    def search(
        self,
        query: str,
        venue: str,
        year_from: int,
        limit: int,
    ) -> List[Paper]:
        """搜索指定会议的论文。使用全库搜索再按 venue 模糊过滤。"""
        collected: List[Paper] = []
        offset = 0
        batch = 100  # 每次取 100 条（API 上限）
        max_pages = 3  # 最多翻 3 页，避免过多请求

        while len(collected) < limit and offset < batch * max_pages:
            params = {
                "query": query,
                "fields": "title,abstract,authors,year,venue,citationCount,url",
                "limit": batch,
                "offset": offset,
                "year": f"{year_from}-",
            }
            data = self._get(params)
            if not data:
                break

            for item in data:
                title = (item.get("title") or "").strip()
                abstract = (item.get("abstract") or "").strip()
                year = item.get("year")
                item_venue = (item.get("venue") or "").strip()

                if not title or not abstract or not year:
                    continue
                if not _venue_matches(item_venue, venue):
                    continue

                authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
                collected.append(
                    Paper(
                        paper_id=item.get("paperId", ""),
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        year=int(year),
                        venue=item_venue or venue,
                        citation_count=int(item.get("citationCount") or 0),
                        url=item.get("url") or "",
                    )
                )
                if len(collected) >= limit:
                    break

            offset += batch
            time.sleep(1.5)  # 每次翻页等 1.5s，避免限流

        return collected

    def batch_search(
        self,
        query: str,
        venues: List[str],
        year_from: int,
        per_venue_limit: int,
    ) -> List[Paper]:
        all_papers: List[Paper] = []
        print("      [数据源] Semantic Scholar API (with key)", flush=True)
        for venue in venues:
            print(f"      正在搜索会议: {venue} ...", flush=True)
            papers = self.search(
                query=query,
                venue=venue,
                year_from=year_from,
                limit=per_venue_limit,
            )
            print(f"        -> 找到 {len(papers)} 篇", flush=True)
            all_papers.extend(papers)
            time.sleep(1.1)

        # 会议过滤结果不足时，补充全量搜索
        if len(all_papers) < 5:
            print("      [兜底] 会议过滤结果不足，改为全量关键词搜索...", flush=True)
            params = {
                "query": query,
                "fields": "title,abstract,authors,year,venue,citationCount,url",
                "limit": min(per_venue_limit * 3, 100),
                "year": f"{year_from}-",
            }
            data = self._get(params)
            for item in data:
                title = (item.get("title") or "").strip()
                abstract = (item.get("abstract") or "").strip()
                year = item.get("year")
                if not title or not abstract or not year:
                    continue
                authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
                all_papers.append(Paper(
                    paper_id=item.get("paperId", ""),
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    year=int(year),
                    venue=(item.get("venue") or "Semantic Scholar").strip(),
                    citation_count=int(item.get("citationCount") or 0),
                    url=item.get("url") or "",
                ))
            print(f"        -> 全量搜索补充 {len(all_papers)} 篇", flush=True)

        unique = {}
        for p in all_papers:
            key = p.paper_id or f"{p.title}-{p.year}"
            if key not in unique:
                unique[key] = p
        return list(unique.values())


# ---------------------------------------------------------------------------
# arXiv Provider（备用，完全免费无需 key）
# ---------------------------------------------------------------------------
class ArXivProvider:
    BASE_URL = "http://export.arxiv.org/api/query"
    NS = "http://www.w3.org/2005/Atom"

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def _fetch(self, query: str, start: int, max_results: int) -> list:
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        url = self.BASE_URL + "?" + urllib.parse.urlencode(params)
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        return root.findall(f"{{{self.NS}}}entry")

    def search_no_venue_filter(
        self,
        query: str,
        year_from: int,
        limit: int,
        venue_label: str = "arXiv preprint",
    ) -> List[Paper]:
        terms = query.strip().split()
        phrase = " ".join(terms)
        arxiv_query = f'ti:"{phrase}" OR abs:"{phrase}"'
        collected: List[Paper] = []
        start = 0
        batch = 100
        while len(collected) < limit and start < limit * 2:
            try:
                entries = self._fetch(arxiv_query, start=start, max_results=min(batch, 200))
            except Exception as e:
                print(f"        [arXiv] 请求失败: {e}", flush=True)
                break
            if not entries:
                break
            ns = self.NS
            for entry in entries:
                title_el = entry.find(f"{{{ns}}}title")
                abstract_el = entry.find(f"{{{ns}}}summary")
                published_el = entry.find(f"{{{ns}}}published")
                id_el = entry.find(f"{{{ns}}}id")
                title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""
                abstract = (abstract_el.text or "").strip().replace("\n", " ") if abstract_el is not None else ""
                year = int(published_el.text[:4]) if published_el is not None else 0
                url = (id_el.text or "").strip() if id_el is not None else ""
                paper_id = url.split("/abs/")[-1] if "/abs/" in url else url
                if not title or not abstract or year < year_from:
                    continue
                authors = []
                for author_el in entry.findall(f"{{{ns}}}author"):
                    name_el = author_el.find(f"{{{ns}}}name")
                    if name_el is not None and name_el.text:
                        authors.append(name_el.text.strip())
                collected.append(Paper(
                    paper_id=paper_id,
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    year=year,
                    venue=venue_label,
                    citation_count=0,
                    url=url,
                ))
                if len(collected) >= limit:
                    break
            start += batch
            time.sleep(3)
        return collected


# ---------------------------------------------------------------------------
# HybridProvider：agent.py 统一使用此类
# ---------------------------------------------------------------------------
class HybridProvider:
    """
    主力使用 Semantic Scholar（带 API key），结果不足时用 arXiv 补充。
    对外接口与原 SemanticScholarProvider.batch_search 完全兼容。
    """

    def __init__(self) -> None:
        self.s2 = SemanticScholarProvider()
        self.arxiv = ArXivProvider()

    def batch_search(
        self,
        query: str,
        venues: List[str],
        year_from: int,
        per_venue_limit: int,
    ) -> List[Paper]:
        all_papers = self.s2.batch_search(
            query=query,
            venues=venues,
            year_from=year_from,
            per_venue_limit=per_venue_limit,
        )

        if len(all_papers) < 5:
            print("      [备用] S2 结果不足，切换到 arXiv 全量搜索...", flush=True)
            fallback = self.arxiv.search_no_venue_filter(
                query=query,
                year_from=year_from,
                limit=per_venue_limit * len(venues),
            )
            print(f"        -> arXiv 找到 {len(fallback)} 篇", flush=True)
            all_papers.extend(fallback)

        unique: dict = {}
        for p in all_papers:
            key = p.paper_id or f"{p.title}-{p.year}"
            if key not in unique:
                unique[key] = p
        return list(unique.values())
