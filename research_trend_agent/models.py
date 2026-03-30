from dataclasses import dataclass
from typing import List


@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: str
    authors: List[str]
    year: int
    venue: str
    citation_count: int
    url: str


@dataclass
class TrendSignal:
    keyword: str
    recent_score: float
    previous_score: float
    growth: float
