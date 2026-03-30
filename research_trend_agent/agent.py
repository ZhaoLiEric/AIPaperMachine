from __future__ import annotations

import json
import traceback
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .analyzer import TrendAnalyzer
from .config import AgentConfig
from .models import Paper
from .providers import SemanticScholarProvider
from .summarizer import PaperSummarizer, ReportComposer


class ResearchTrendAgent:
    def __init__(self) -> None:
        self.provider = SemanticScholarProvider()
        self.analyzer = TrendAnalyzer()
        self.summarizer = PaperSummarizer()
        self.composer = ReportComposer()

    def run(self, cfg: AgentConfig, output_dir: Path) -> Dict[str, str]:
        now_year = datetime.now().year
        year_from = now_year - cfg.years_back + 1
        conferences = cfg.resolve_conferences()

        print("[1/4] 开始查询论文...")
        print(f"      领域: {cfg.domain}  关键词: {cfg.keywords}")
        print(f"      会议: {', '.join(conferences)}")
        print(f"      年份范围: {year_from} - {now_year}")
        print(f"      每会议最大抓取: {cfg.per_conference_limit} 篇")

        try:
            papers = self.provider.batch_search(
                query=cfg.keywords,
                venues=conferences,
                year_from=year_from,
                per_venue_limit=cfg.per_conference_limit,
            )
        except Exception:
            print("[ERROR] 网络请求失败，详情：")
            traceback.print_exc()
            raise

        print(f"[2/4] 抓取完成，共获得 {len(papers)} 篇论文，开始分析趋势...")
        if not papers:
            print("      警告：未抓到任何论文，请检查网络连接或关键词/会议名称。")

        top_papers = sorted(papers, key=lambda p: p.citation_count, reverse=True)[: cfg.max_papers_in_report]
        print(f"      取引用数最高的 {len(top_papers)} 篇用于分析")

        trend_result = self.analyzer.analyze(top_papers)
        print(f"[3/4] 趋势分析完成，检测到 {len(trend_result.signals)} 个趋势信号，生成报告...")

        paper_summaries = self.summarizer.summarize_top_papers(
            top_papers,
            top_n=min(12, len(top_papers)),
            lang=cfg.language,
        )

        report = self.composer.compose(
            domain=cfg.domain,
            keywords=cfg.keywords,
            papers=top_papers,
            trend_result=trend_result,
            paper_summaries=paper_summaries,
            lang=cfg.language,
        )

        print("[4/4] 报告生成完毕，写入磁盘...")
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "trend_report.md"
        papers_path = output_dir / "papers.jsonl"
        meta_path = output_dir / "run_meta.txt"

        report_path.write_text(report, encoding="utf-8")
        self._write_papers_jsonl(papers_path, top_papers)
        meta_path.write_text(
            self._meta_text(cfg, conferences, year_from, len(top_papers)),
            encoding="utf-8",
        )

        return {
            "report": str(report_path),
            "papers": str(papers_path),
            "meta": str(meta_path),
        }

    def _write_papers_jsonl(self, path: Path, papers: List[Paper]) -> None:
        lines = []
        for p in papers:
            row = {
                "paper_id": p.paper_id,
                "title": p.title,
                "abstract": p.abstract,
                "authors": p.authors,
                "year": p.year,
                "venue": p.venue,
                "citation_count": p.citation_count,
                "url": p.url,
            }
            lines.append(json.dumps(row, ensure_ascii=False))
        path.write_text("\n".join(lines), encoding="utf-8")

    def _meta_text(
        self,
        cfg: AgentConfig,
        conferences: List[str],
        year_from: int,
        paper_count: int,
    ) -> str:
        rows = [
            "Research Trend Agent Run Meta",
            "============================",
            f"generated_at: {datetime.now().isoformat()}",
            f"domain: {cfg.domain}",
            f"keywords: {cfg.keywords}",
            f"years_back: {cfg.years_back}",
            f"year_from: {year_from}",
            f"conferences: {', '.join(conferences)}",
            f"paper_count: {paper_count}",
            f"language: {cfg.language}",
            f"config: {asdict(cfg)}",
        ]
        return "\n".join(rows)
