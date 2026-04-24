from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from support_intelligence.ai import enrich_tickets_with_ai
from support_intelligence.config import RAW_DATA_DIR, ensure_project_directories
from support_intelligence.data_simulation import build_dataset, save_dataset


def main() -> None:
    ensure_project_directories()
    bundle = build_dataset(random_seed=42, n_accounts=320)
    enriched_tickets, _ = enrich_tickets_with_ai(
        bundle.tables["tickets"],
        bundle.tables["ticket_messages"],
        bundle.tables["accounts"],
    )
    bundle.tables["tickets"] = enriched_tickets.drop(
        columns=["arr_exposure_component", "severity_component", "csat_component", "resolution_component", "risk_component"],
        errors="ignore",
    )
    save_dataset(bundle)
    (RAW_DATA_DIR / "simulation_assumptions.json").write_text(
        json.dumps(bundle.assumptions, indent=2),
        encoding="utf-8",
    )
    ticket_count = len(bundle.tables["tickets"])
    account_count = bundle.tables["accounts"]["account_id"].nunique()
    print(f"Generated {ticket_count} tickets across {account_count} accounts.")


if __name__ == "__main__":
    main()
