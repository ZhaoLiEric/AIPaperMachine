from __future__ import annotations

from typing import List, Sequence

from .analyzer import TrendResult
from .models import Paper


class PaperSummarizer:
    def summarize_one(self, paper: Paper, lang: str = "zh") -> str:
        if lang == "zh":
            return (
                f"《{paper.title}》发表于 {paper.venue} {paper.year}。"
                f"核心问题是：{paper.abstract[:110]}..."
                f"引用数约 {paper.citation_count}。"
            )
        return (
            f"{paper.title} ({paper.venue} {paper.year}) studies: "
            f"{paper.abstract[:140]}... citations={paper.citation_count}."
        )

    def summarize_top_papers(self, papers: Sequence[Paper], top_n: int = 10, lang: str = "zh") -> List[str]:
        ordered = sorted(papers, key=lambda p: p.citation_count, reverse=True)
        return [self.summarize_one(p, lang=lang) for p in ordered[:top_n]]


class ReportComposer:
    def compose(
        self,
        domain: str,
        keywords: str,
        papers: Sequence[Paper],
        trend_result: TrendResult,
        paper_summaries: Sequence[str],
        lang: str = "zh",
    ) -> str:
        if lang != "zh":
            return self._compose_en(domain, keywords, papers, trend_result, paper_summaries)

        lines: List[str] = []
        lines.append("# 科研新趋势分析报告")
        lines.append("")
        lines.append(f"- 研究领域: {domain}")
        lines.append(f"- 查询关键词: {keywords}")
        lines.append(f"- 样本论文数: {len(papers)}")
        lines.append("")

        lines.append("## 1) 可能的新趋势")
        if trend_result.signals:
            for idx, s in enumerate(trend_result.signals, start=1):
                lines.append(
                    f"{idx}. `{s.keyword}` - 最新热度 {s.recent_score:.0f}, 前一年 {s.previous_score:.0f}, 增长 {s.growth:.2f}x"
                )
        else:
            lines.append("- 暂未检测到显著趋势信号（样本可能过少）。")
        lines.append("")

        lines.append("## 2) 可能的突破点")
        if trend_result.possible_breakthrough_points:
            for bp in trend_result.possible_breakthrough_points:
                lines.append(f"- {bp}")
        else:
            lines.append("- 无明显突破点，建议扩大年份或关键词范围。")
        lines.append("")

        lines.append("## 3) 顶会论文年度主题分布")
        for year, topics in trend_result.yearly_topic_distribution.items():
            topic_str = "，".join([f"{t}({c})" for t, c in topics])
            lines.append(f"- {year}: {topic_str}")
        lines.append("")

        lines.append("## 4) 顶会论文摘要式总结")
        for idx, s in enumerate(paper_summaries, start=1):
            lines.append(f"{idx}. {s}")
        lines.append("")

        lines.append("## 5) 建议下一步")
        lines.append("- 对增长最快的3个关键词做更细粒度子方向拆解（方法、任务、数据集）。")
        lines.append("- 按机构和作者网络分析，寻找潜在合作团队与未饱和赛道。")
        lines.append("- 对突破点做可复现实验基线，验证是否具备工程转化价值。")
        return "\n".join(lines)

    def _compose_en(
        self,
        domain: str,
        keywords: str,
        papers: Sequence[Paper],
        trend_result: TrendResult,
        paper_summaries: Sequence[str],
    ) -> str:
        lines: List[str] = []
        lines.append("# Research Trend Analysis Report")
        lines.append("")
        lines.append(f"- Domain: {domain}")
        lines.append(f"- Keywords: {keywords}")
        lines.append(f"- Number of papers: {len(papers)}")
        lines.append("")
        lines.append("## Emerging trends")
        for s in trend_result.signals:
            lines.append(
                f"- {s.keyword}: recent={s.recent_score:.0f}, previous={s.previous_score:.0f}, growth={s.growth:.2f}x"
            )
        lines.append("")
        lines.append("## Candidate breakthroughs")
        for bp in trend_result.possible_breakthrough_points:
            lines.append(f"- {bp}")
        lines.append("")
        lines.append("## Paper summaries")
        for s in paper_summaries:
            lines.append(f"- {s}")
        return "\n".join(lines)
