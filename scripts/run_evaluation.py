from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from support_intelligence.ai import build_issue_priority_table, build_theme_summaries
from support_intelligence.config import RAW_DATA_DIR
from support_intelligence.evaluation import run_evaluation_artifacts


def _load_csv(name: str) -> pd.DataFrame:
    path = RAW_DATA_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset file: {path}")
    return pd.read_csv(path)


def main() -> None:
    accounts = _load_csv("accounts")
    tickets = _load_csv("tickets")
    ticket_messages = _load_csv("ticket_messages")
    feature_requests = _load_csv("feature_requests")
    theme_summaries = build_theme_summaries(tickets, ticket_messages, accounts)
    priority_table = build_issue_priority_table(tickets, accounts, feature_requests)
    results = run_evaluation_artifacts(tickets, ticket_messages, theme_summaries, priority_table)
    print(f"Evaluation completed. Macro-F1: {results['metrics']['macro_f1']:.4f}")


if __name__ == "__main__":
    main()

