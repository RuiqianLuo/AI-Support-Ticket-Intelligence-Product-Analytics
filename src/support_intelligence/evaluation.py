from __future__ import annotations

import json

import pandas as pd

from .ai import (
    build_prioritization_sanity_checks,
    build_summarization_review_sheet,
    evaluate_classifier_holdout,
)
from .config import EVALUATION_DIR, ensure_project_directories
from .utils import export_dataframe


def run_evaluation_artifacts(
    tickets: pd.DataFrame,
    messages: pd.DataFrame,
    theme_summaries: pd.DataFrame,
    priority_table: pd.DataFrame,
) -> dict[str, object]:
    ensure_project_directories()
    classifier_eval = evaluate_classifier_holdout(tickets, messages)
    metrics = classifier_eval["metrics"]
    confusion_df = classifier_eval["confusion"]
    prediction_df = classifier_eval["predictions"]
    summarization_sheet = build_summarization_review_sheet(theme_summaries)
    prioritization_checks = build_prioritization_sanity_checks(priority_table)

    export_dataframe(confusion_df, EVALUATION_DIR / "classification_confusion_matrix.csv", index=True)
    export_dataframe(prediction_df, EVALUATION_DIR / "classification_predictions_sample.csv", index=False)
    export_dataframe(summarization_sheet, EVALUATION_DIR / "summarization_review_sheet.csv", index=False)
    export_dataframe(prioritization_checks, EVALUATION_DIR / "prioritization_sanity_checks.csv", index=False)
    (EVALUATION_DIR / "classification_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    report = "\n".join(
        [
            "# Evaluation Snapshot",
            "",
            "## Classification",
            f"- Accuracy: {metrics['accuracy']:.4f}",
            f"- Macro precision: {metrics['macro_precision']:.4f}",
            f"- Macro recall: {metrics['macro_recall']:.4f}",
            f"- Macro F1: {metrics['macro_f1']:.4f}",
            "",
            "## Summarization Review Design",
            "- Review sheet scores summaries on coverage, specificity, and actionability using a 1-5 proxy rubric.",
            "- Human reviewers can replace the proxy scores with analyst judgments during portfolio demos.",
            "",
            "## Prioritization Checks",
            f"- Checks passed: {int(prioritization_checks['result'].sum())} / {len(prioritization_checks)}",
            "- Current checks validate ARR weighting, enterprise pain surfacing, and correlation with churn pressure.",
            "",
            "## Known Limitations",
            "- The classifier is trained on synthetic text, so production accuracy would likely be lower.",
            "- Theme summaries are templated and should be paired with analyst review for executive use.",
            "- Prioritization is decision support rather than an automatic roadmap allocator.",
        ]
    )
    (EVALUATION_DIR / "evaluation_report.md").write_text(report, encoding="utf-8")
    return {"metrics": metrics}

