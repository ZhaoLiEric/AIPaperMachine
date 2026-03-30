import sys
print("Python version:", sys.version)
print("Step 1: import config...")
try:
    from research_trend_agent.config import AgentConfig, TOP_CONFERENCES
    print("  OK - config imported")
except Exception as e:
    print("  FAIL:", e)
    import traceback; traceback.print_exc()
    sys.exit(1)

print("Step 2: import models...")
try:
    from research_trend_agent.models import Paper, TrendSignal
    print("  OK - models imported")
except Exception as e:
    print("  FAIL:", e)
    import traceback; traceback.print_exc()
    sys.exit(1)

print("Step 3: import providers...")
try:
    from research_trend_agent.providers import SemanticScholarProvider
    print("  OK - providers imported")
except Exception as e:
    print("  FAIL:", e)
    import traceback; traceback.print_exc()
    sys.exit(1)

print("Step 4: import analyzer...")
try:
    from research_trend_agent.analyzer import TrendAnalyzer
    print("  OK - analyzer imported")
except Exception as e:
    print("  FAIL:", e)
    import traceback; traceback.print_exc()
    sys.exit(1)

print("Step 5: import summarizer...")
try:
    from research_trend_agent.summarizer import PaperSummarizer, ReportComposer
    print("  OK - summarizer imported")
except Exception as e:
    print("  FAIL:", e)
    import traceback; traceback.print_exc()
    sys.exit(1)

print("Step 6: import agent...")
try:
    from research_trend_agent.agent import ResearchTrendAgent
    print("  OK - agent imported")
except Exception as e:
    print("  FAIL:", e)
    import traceback; traceback.print_exc()
    sys.exit(1)

print("Step 7: import cli...")
try:
    from research_trend_agent.cli import main
    print("  OK - cli imported")
except Exception as e:
    print("  FAIL:", e)
    import traceback; traceback.print_exc()
    sys.exit(1)

print()
print("All imports OK. Now running main()...")
main()
