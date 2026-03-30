from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from .models import Paper, TrendSignal

STOPWORDS = {
    "the",
    "a",
    "an",
    "for",
    "with",
    "from",
    "and",
    "or",
    "to",
    "in",
    "of",
    "on",
    "via",
    "using",
    "towards",
    "based",
    "through",
    "by",
    "is",
    "are",
    "at",
}


@dataclass
class TrendResult:
    signals: List[TrendSignal]
    possible_breakthrough_points: List[str]
    yearly_topic_distribution: Dict[int, List[Tuple[str, int]]]


class TrendAnalyzer:
    def __init__(self, min_token_len: int = 4) -> None:
        self.min_token_len = min_token_len

    def _tokenize(self, text: str) -> List[str]:
        normalized = (
            text.lower()
            .replace("/", " ")
            .replace("-", " ")
            .replace("(", " ")
            .replace(")", " ")
            .replace(",", " ")
            .replace(".", " ")
            .replace(":", " ")
            .replace(";", " ")
        )
        tokens = [t.strip() for t in normalized.split()]
        return [t for t in tokens if len(t) >= self.min_token_len and t not in STOPWORDS]

    def _paper_tokens(self, paper: Paper) -> List[str]:
        return self._tokenize(f"{paper.title} {paper.abstract}")

    def analyze(self, papers: Sequence[Paper], top_k: int = 12) -> TrendResult:
        if not papers:
            return TrendResult(signals=[], possible_breakthrough_points=[], yearly_topic_distribution={})

        latest_year = max(p.year for p in papers)
        prev_year = latest_year - 1

        recent_counter: Counter = Counter()
        prev_counter: Counter = Counter()
        yearly_counter: Dict[int, Counter] = defaultdict(Counter)

        for p in papers:
            token_counter = Counter(self._paper_tokens(p))
            for t, c in token_counter.items():
                yearly_counter[p.year][t] += c
                if p.year == latest_year:
                    recent_counter[t] += c
                if p.year == prev_year:
                    prev_counter[t] += c

        candidates = set(recent_counter.keys()) | set(prev_counter.keys())
        signals: List[TrendSignal] = []
        for token in candidates:
            r = float(recent_counter.get(token, 0))
            pv = float(prev_counter.get(token, 0))
            if r < 3:
                continue
            growth = (r + 1.0) / (pv + 1.0)
            signals.append(
                TrendSignal(
                    keyword=token,
                    recent_score=r,
                    previous_score=pv,
                    growth=growth,
                )
            )

        signals.sort(key=lambda s: (s.growth, s.recent_score), reverse=True)
        top_signals = signals[:top_k]

        yearly_topic_distribution = {
            y: yearly_counter[y].most_common(8) for y in sorted(yearly_counter.keys())
        }

        breakthroughs = [
            f"{s.keyword}: 最近一年热度 {int(s.recent_score)}，同比增长 {s.growth:.2f}x"
            for s in top_signals[:6]
        ]

        return TrendResult(
            signals=top_signals,
            possible_breakthrough_points=breakthroughs,
            yearly_topic_distribution=yearly_topic_distribution,
        )
