from __future__ import annotations

import argparse
from pathlib import Path

from .agent import ResearchTrendAgent
from .config import AgentConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="发现科研新趋势的Agent")
    parser.add_argument("--domain", required=True, help="领域，例如 llm / nlp / cv / ml / security / systems")
    parser.add_argument("--keywords", required=True, help="查询关键词，例如 'multimodal agent planning'")
    parser.add_argument("--years-back", type=int, default=3, help="回溯年份，默认3")
    parser.add_argument("--per-conference-limit", type=int, default=25, help="每个会最大论文数")
    parser.add_argument("--max-papers-in-report", type=int, default=20, help="报告最大论文数")
    parser.add_argument("--language", default="zh", choices=["zh", "en"], help="输出语言")
    parser.add_argument("--conferences", default="", help="自定义会名，逗号分隔")
    parser.add_argument("--output-dir", default="outputs", help="输出目录")
    return parser


def parse_args() -> argparse.Namespace:
    return build_parser().parse_args()


def main() -> None:
    args = parse_args()
    conferences = [c.strip() for c in args.conferences.split(",") if c.strip()]

    cfg = AgentConfig(
        domain=args.domain,
        keywords=args.keywords,
        years_back=args.years_back,
        per_conference_limit=args.per_conference_limit,
        max_papers_in_report=args.max_papers_in_report,
        language=args.language,
        conferences=conferences,
    )

    try:
        agent = ResearchTrendAgent()
        result = agent.run(cfg, Path(args.output_dir))
        print()
        print("运行完成，产物如下：")
        print(f"  - 报告:      {result['report']}")
        print(f"  - 论文数据:  {result['papers']}")
        print(f"  - 运行元信息:{result['meta']}")
    except Exception as exc:
        import traceback
        print()
        print("[ERROR] 运行失败，详细错误如下：")
        traceback.print_exc()
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
