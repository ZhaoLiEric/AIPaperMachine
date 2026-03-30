# Research Trend Agent

一个可直接运行的科研趋势发现 Agent（Python），支持：

- 查询特定领域的顶会论文（通过 Semantic Scholar API）
- 自动提取近年热点关键词趋势
- 生成“可能突破点”建议
- 输出顶会论文摘要式总结

## 1. 安装

```bash
pip install -r requirements.txt
```

## 2. 快速运行

```bash
python main.py --domain llm --keywords "multimodal agent planning" --years-back 3
```

运行后默认在 `outputs/` 下生成：

- `trend_report.md`：趋势报告
- `papers.jsonl`：论文结构化数据
- `run_meta.txt`：运行元信息

## 3. 参数说明

- `--domain`：领域（`llm` / `nlp` / `cv` / `ml` / `security` / `systems`）
- `--keywords`：检索关键词
- `--years-back`：回溯年数（默认 3）
- `--per-conference-limit`：每个会议抓取上限（默认 25）
- `--max-papers-in-report`：用于生成报告的最大论文数量（默认 20）
- `--language`：报告语言（`zh` 或 `en`）
- `--conferences`：手动指定会议，逗号分隔（可覆盖默认会议）
- `--output-dir`：输出目录（默认 `outputs`）

## 4. 示例

### 示例A：NLP方向

```bash
python main.py --domain nlp --keywords "reasoning chain of thought" --years-back 4
```

### 示例B：自定义会议

```bash
python main.py --domain ml --keywords "efficient finetuning" --conferences "NeurIPS,ICML,ICLR" --output-dir "outputs_finetune"
```

## 5. 注意事项

- 该版本使用公开 API，受网络和限流影响。
- 趋势分析是关键词统计信号，不等于严格因果结论。
- 若要更高精度，可后续接入：
  - 论文全文解析
  - 引文网络分析
  - 大模型深度总结与对比评估
