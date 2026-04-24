from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from support_intelligence.ai import build_issue_priority_table, build_theme_summaries, enrich_tickets_with_ai
from support_intelligence.data_simulation import build_dataset


def test_dataset_shapes_and_required_tables() -> None:
    bundle = build_dataset(random_seed=7, n_accounts=45)
    expected_tables = {
        "accounts",
        "users",
        "tickets",
        "ticket_messages",
        "product_usage",
        "feature_requests",
        "experiments",
        "monthly_account_metrics",
    }
    assert set(bundle.tables) == expected_tables
    assert len(bundle.tables["tickets"]) > 500
    assert len(bundle.tables["ticket_messages"]) > len(bundle.tables["tickets"])


def test_ai_enrichment_and_priority_outputs() -> None:
    bundle = build_dataset(random_seed=11, n_accounts=50)
    enriched_tickets, _ = enrich_tickets_with_ai(
        bundle.tables["tickets"], bundle.tables["ticket_messages"], bundle.tables["accounts"]
    )
    assert enriched_tickets["ai_predicted_category"].notna().all()
    assert enriched_tickets["ai_priority_score"].between(0, 100).all()
    theme_summaries = build_theme_summaries(
        enriched_tickets, bundle.tables["ticket_messages"], bundle.tables["accounts"]
    )
    priority_table = build_issue_priority_table(
        enriched_tickets, bundle.tables["accounts"], bundle.tables["feature_requests"]
    )
    assert not theme_summaries.empty
    assert not priority_table.empty
    assert priority_table["priority_score"].max() <= 100
