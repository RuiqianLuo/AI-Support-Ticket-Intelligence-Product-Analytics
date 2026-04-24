from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from support_intelligence.ai import build_issue_priority_table, build_theme_summaries
from support_intelligence.analytics import (
    build_dashboard_tables,
    create_figures,
    execute_sql_reports,
    save_analysis_manifest,
    save_dashboard_tables,
)
from support_intelligence.config import RAW_DATA_DIR


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
    monthly_account_metrics = _load_csv("monthly_account_metrics")

    theme_summaries = build_theme_summaries(tickets, ticket_messages, accounts)
    priority_table = build_issue_priority_table(tickets, accounts, feature_requests)
    theme_summaries.to_csv(PROJECT_ROOT / "outputs" / "tables" / "theme_summaries.csv", index=False)
    dashboard_tables = build_dashboard_tables(
        accounts,
        tickets,
        feature_requests,
        theme_summaries,
        priority_table,
        monthly_account_metrics,
    )
    save_dashboard_tables(dashboard_tables)
    create_figures(dashboard_tables)
    sql_outputs = execute_sql_reports()
    save_analysis_manifest(dashboard_tables, sql_outputs)
    print("Analysis outputs generated.")


if __name__ == "__main__":
    main()

