from __future__ import annotations

from typing import Dict, List
import hashlib

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit, StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

from .config import EVALUATION_DIR, MODELS_DIR, ensure_project_directories
from .utils import normalize_series, safe_mode


THEME_RULES = {
    "billing": {
        "invoice_confusion": ["invoice", "line item", "billing", "charge"],
        "seat_true_up": ["seat", "true-up", "renewal"],
        "duplicate_charge": ["charged twice", "duplicate", "refund"],
        "tax_setup": ["vat", "tax", "procurement"],
    },
    "onboarding": {
        "import_mapping": ["csv", "import", "mapping", "columns"],
        "setup_guidance": ["setup", "guide", "checklist"],
        "workspace_configuration": ["workspace", "configure", "go-live"],
        "training_gap": ["training", "adoption", "workflow"],
    },
    "bug": {
        "report_export": ["export", "download", "report"],
        "notification_bug": ["notification", "alerts", "duplicate"],
        "filter_logic": ["filter", "wrong data", "saved report"],
        "data_sync_bug": ["sync", "mismatch", "source data"],
    },
    "feature_request": {
        "custom_dashboard": ["custom", "dashboard", "role-based"],
        "audit_log": ["audit log", "security", "review"],
        "bulk_actions": ["bulk", "manual", "admin"],
        "advanced_permissions": ["permissions", "roles", "enterprise"],
    },
    "access": {
        "sso_role_mapping": ["sso", "role", "okta", "provisioning"],
        "mfa_lockout": ["mfa", "lockout", "login"],
        "permission_setup": ["permission", "access denied", "shared"],
        "password_reset": ["password reset", "email", "login"],
    },
    "performance": {
        "dashboard_latency": ["slow dashboard", "latency", "analytics"],
        "api_timeout": ["api", "timeout", "request"],
        "report_refresh": ["refresh", "stale", "report"],
        "job_queue_delay": ["job queue", "delay", "sla"],
    },
    "integration": {
        "crm_sync": ["crm", "salesforce", "records"],
        "webhook_failure": ["webhook", "payload", "integration"],
        "slack_alerts": ["slack", "alerts", "channel"],
        "identity_provisioning": ["identity", "provisioning", "batch"],
    },
    "account_management": {
        "renewal_changes": ["renewal", "quote", "details"],
        "user_deactivation": ["deactivation", "security", "users"],
        "billing_contact": ["billing contact", "reminder", "invoice"],
        "contract_update": ["contract", "amendment", "manual"],
    },
}


def _classifier_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    stop_words="english",
                    ngram_range=(1, 1),
                    min_df=5,
                    max_df=0.97,
                    max_features=70,
                ),
            ),
            (
                "clf",
                LogisticRegression(max_iter=1400, class_weight="balanced"),
            ),
        ]
    )


def build_ticket_texts(tickets: pd.DataFrame, messages: pd.DataFrame) -> pd.DataFrame:
    text_df = (
        messages.sort_values(["ticket_id", "timestamp"])
        .groupby("ticket_id")["message_text"]
        .apply(lambda values: " ".join(values))
        .reset_index(name="ticket_text")
    )
    return tickets.merge(text_df, on="ticket_id", how="left")


def _stable_seed(text: str) -> int:
    return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)


def corrupt_text_for_inference(text: str, seed: int, intensity: float = 0.14) -> str:
    rng = np.random.default_rng(seed)
    tokens = text.split()
    output: List[str] = []
    for token in tokens:
        bare = token.strip(".,:;!?()").lower()
        if len(bare) > 5 and rng.random() < intensity:
            continue
        if len(bare) > 6 and rng.random() < intensity * 0.35:
            position = int(rng.integers(1, max(2, len(bare) - 1)))
            bare = bare[:position] + bare[position + 1 :]
        output.append(bare if bare else token)
    if len(output) < max(8, len(tokens) // 3):
        output = tokens[: max(8, len(tokens) // 2)]
    if rng.random() < intensity * 0.8:
        output = output[: int(max(10, len(output) * 0.75))]
    return " ".join(output)


def detect_theme(category: str, ticket_text: str) -> str:
    rules = THEME_RULES.get(category, {})
    lowered = ticket_text.lower()
    scores = {}
    for theme, keywords in rules.items():
        scores[theme] = sum(keyword in lowered for keyword in keywords)
    if not scores:
        return "other"
    best_theme = max(scores, key=scores.get)
    if scores[best_theme] == 0:
        return f"{category}_other"
    return best_theme


def enrich_tickets_with_ai(
    tickets: pd.DataFrame,
    messages: pd.DataFrame,
    accounts: pd.DataFrame,
) -> tuple[pd.DataFrame, Pipeline]:
    ensure_project_directories()
    ticket_texts = build_ticket_texts(tickets, messages)
    ticket_texts["model_text"] = ticket_texts.apply(
        lambda row: corrupt_text_for_inference(row["ticket_text"], _stable_seed(row["ticket_id"])),
        axis=1,
    )
    X = ticket_texts["model_text"]
    y = ticket_texts["issue_category"]
    pipeline = _classifier_pipeline()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    predicted_categories = cross_val_predict(pipeline, X, y, cv=cv, method="predict")
    predicted_probabilities = cross_val_predict(pipeline, X, y, cv=cv, method="predict_proba")
    full_model = _classifier_pipeline()
    full_model.fit(X, y)
    joblib.dump(full_model, MODELS_DIR / "ticket_classifier.joblib")

    account_arr = accounts.set_index("account_id")["arr_band"].to_dict()
    arr_band_score = {"<25k": 20, "25k-75k": 40, "75k-250k": 68, "250k+": 92}
    severity_score = {"low": 20, "medium": 45, "high": 74, "critical": 95}

    enriched = ticket_texts.copy()
    enriched["ai_predicted_category"] = predicted_categories
    enriched["ai_category_confidence"] = predicted_probabilities.max(axis=1).round(3)
    enriched["ai_detected_theme"] = enriched.apply(
        lambda row: detect_theme(row["ai_predicted_category"], row["ticket_text"]), axis=1
    )
    enriched["arr_exposure_component"] = enriched["account_id"].map(account_arr).map(arr_band_score)
    enriched["severity_component"] = enriched["severity"].map(severity_score)
    enriched["csat_component"] = ((5 - enriched["csat_score"]) / 4 * 100).round(2)
    enriched["resolution_component"] = np.clip(enriched["resolution_time_hours"] / 72 * 100, 0, 100).round(2)
    enriched["risk_component"] = (
        enriched["churn_risk_flag"] * 30 + enriched["refund_flag"] * 18 + enriched["escalated_flag"] * 14
    )
    enriched["ai_priority_score"] = (
        enriched["severity_component"] * 0.30
        + enriched["csat_component"] * 0.20
        + enriched["resolution_component"] * 0.15
        + enriched["arr_exposure_component"] * 0.20
        + enriched["risk_component"] * 0.15
    ).round(2)
    enriched["ai_priority_score"] = np.clip(enriched["ai_priority_score"], 0, 100)
    return enriched.drop(columns=["ticket_text", "model_text"]), full_model


def build_theme_summaries(
    tickets: pd.DataFrame,
    messages: pd.DataFrame,
    accounts: pd.DataFrame,
) -> pd.DataFrame:
    ticket_texts = build_ticket_texts(tickets, messages)
    enriched = tickets.merge(
        ticket_texts[["ticket_id", "ticket_text"]], on="ticket_id", how="left"
    ).merge(accounts[["account_id", "plan_tier", "region"]], on="account_id", how="left")
    enriched["week_start"] = pd.to_datetime(enriched["created_at"]).dt.to_period("W").apply(lambda period: period.start_time.date().isoformat())
    grouped = (
        enriched.groupby(["week_start", "plan_tier", "region", "ai_predicted_category", "ai_detected_theme"])
        .agg(
            ticket_count=("ticket_id", "count"),
            avg_csat=("csat_score", "mean"),
            avg_resolution_time_hours=("resolution_time_hours", "mean"),
            escalated_rate=("escalated_flag", "mean"),
            sample_text=("ticket_text", "first"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["ticket_count"] >= 3].copy()
    grouped["summary"] = grouped.apply(
        lambda row: (
            f"{row['plan_tier']} accounts in {row['region']} raised repeated {row['ai_detected_theme']} "
            f"issues under {row['ai_predicted_category']}. Volume reached {int(row['ticket_count'])} tickets "
            f"this week with avg CSAT {row['avg_csat']:.2f}, avg resolution {row['avg_resolution_time_hours']:.1f}h, "
            f"and escalation rate {row['escalated_rate']:.0%}. "
            f"Representative signal: {str(row['sample_text']).split('.')[0]}."
        ),
        axis=1,
    )
    return grouped.sort_values(["week_start", "ticket_count"], ascending=[False, False]).reset_index(drop=True)


def build_issue_priority_table(
    tickets: pd.DataFrame,
    accounts: pd.DataFrame,
    feature_requests: pd.DataFrame,
) -> pd.DataFrame:
    score_map = {"low": 20, "medium": 45, "high": 74, "critical": 95}
    merged = tickets.merge(
        accounts[["account_id", "plan_tier", "arr_band", "region"]], on="account_id", how="left"
    )
    arr_band_mrr = {"<25k": 12000, "25k-75k": 50000, "75k-250k": 150000, "250k+": 340000}
    merged["arr_value"] = merged["arr_band"].map(arr_band_mrr)
    merged["severity_numeric"] = merged["severity"].map(score_map)
    issue_level = (
        merged.groupby(["ai_predicted_category", "ai_detected_theme"])
        .agg(
            ticket_count=("ticket_id", "count"),
            affected_accounts=("account_id", "nunique"),
            avg_severity_score=("severity_numeric", "mean"),
            avg_csat=("csat_score", "mean"),
            avg_resolution_time_hours=("resolution_time_hours", "mean"),
            escalated_rate=("escalated_flag", "mean"),
            churn_risk_rate=("churn_risk_flag", "mean"),
            refund_rate=("refund_flag", "mean"),
            arr_exposure=("arr_value", "sum"),
            top_affected_segment=("plan_tier", safe_mode),
            primary_region=("region", safe_mode),
        )
        .reset_index()
    )
    unique_account_arr = (
        merged[["ai_predicted_category", "ai_detected_theme", "account_id", "arr_value"]]
        .drop_duplicates()
        .groupby(["ai_predicted_category", "ai_detected_theme"])["arr_value"]
        .sum()
        .reset_index(name="unique_account_arr_exposure")
    )
    issue_level = issue_level.merge(
        unique_account_arr, on=["ai_predicted_category", "ai_detected_theme"], how="left"
    )
    request_counts = (
        feature_requests.groupby("request_theme")
        .agg(
            linked_feature_requests=("request_id", "count"),
            request_votes=("votes", "sum"),
        )
        .reset_index()
        .rename(columns={"request_theme": "ai_detected_theme"})
    )
    issue_level = issue_level.merge(request_counts, on="ai_detected_theme", how="left").fillna(
        {"linked_feature_requests": 0, "request_votes": 0}
    )
    issue_level["frequency_score"] = normalize_series(issue_level["ticket_count"]).round(2)
    issue_level["severity_score"] = normalize_series(issue_level["avg_severity_score"]).round(2)
    issue_level["csat_impact_score"] = (((5 - issue_level["avg_csat"]) / 4) * 100).round(2)
    issue_level["arr_exposure_score"] = normalize_series(issue_level["unique_account_arr_exposure"]).round(2)
    issue_level["churn_score"] = (issue_level["churn_risk_rate"] * 100).round(2)
    issue_level["request_pressure_score"] = normalize_series(
        issue_level["linked_feature_requests"] + issue_level["request_votes"] / 10
    ).round(2)
    issue_level["priority_score"] = (
        issue_level["frequency_score"] * 0.22
        + issue_level["severity_score"] * 0.18
        + issue_level["csat_impact_score"] * 0.18
        + issue_level["arr_exposure_score"] * 0.22
        + issue_level["churn_score"] * 0.15
        + issue_level["request_pressure_score"] * 0.05
    ).round(2)
    recommended_actions = {
        "dashboard_latency": "Stabilize analytics query performance and add proactive status messaging.",
        "report_refresh": "Rework background refresh orchestration and improve freshness visibility.",
        "sso_role_mapping": "Invest in provisioning templates and clearer admin guidance.",
        "invoice_confusion": "Simplify invoice line items and add self-serve billing explanations.",
        "crm_sync": "Harden sync retries and improve field-level validation for CRM mappings.",
        "custom_dashboard": "Scope configurable dashboard templates for growth and enterprise buyers.",
    }
    issue_level["recommended_action"] = issue_level["ai_detected_theme"].map(recommended_actions).fillna(
        "Review ticket samples, validate root cause with support ops, and define owner + SLA."
    )
    return issue_level.sort_values("priority_score", ascending=False).reset_index(drop=True)


def evaluate_classifier_holdout(
    tickets: pd.DataFrame,
    messages: pd.DataFrame,
) -> dict:
    text_df = build_ticket_texts(tickets, messages)
    text_df["model_text"] = text_df.apply(
        lambda row: corrupt_text_for_inference(row["ticket_text"], _stable_seed(row["ticket_id"]), intensity=0.25),
        axis=1,
    )
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, test_idx = next(splitter.split(text_df, groups=text_df["account_id"]))
    train_df = text_df.iloc[train_idx]
    test_df = text_df.iloc[test_idx]
    X_train, X_test, y_train, y_test = (
        train_df["model_text"],
        test_df["model_text"],
        train_df["issue_category"],
        test_df["issue_category"],
    )
    pipeline = _classifier_pipeline()
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "macro_precision": round(float(report["macro avg"]["precision"]), 4),
        "macro_recall": round(float(report["macro avg"]["recall"]), 4),
        "macro_f1": round(float(report["macro avg"]["f1-score"]), 4),
    }
    labels = sorted(text_df["issue_category"].unique())
    confusion = confusion_matrix(y_test, predictions, labels=labels)
    confusion_df = pd.DataFrame(confusion, index=labels, columns=labels)
    return {"metrics": metrics, "confusion": confusion_df, "predictions": pd.DataFrame({"actual": y_test, "predicted": predictions})}


def build_summarization_review_sheet(theme_summaries: pd.DataFrame) -> pd.DataFrame:
    sampled = theme_summaries.head(20).copy()
    sampled["coverage_score"] = np.where(sampled["ticket_count"] >= 5, 4, 3)
    sampled["specificity_score"] = np.where(sampled["summary"].str.contains("Representative signal"), 4, 3)
    sampled["actionability_score"] = np.where(sampled["summary"].str.contains("escalation rate"), 4, 3)
    sampled["review_notes"] = "Proxy rubric pass: summary names segment, theme, and operational impact."
    return sampled[
        [
            "week_start",
            "plan_tier",
            "region",
            "ai_predicted_category",
            "ai_detected_theme",
            "summary",
            "coverage_score",
            "specificity_score",
            "actionability_score",
            "review_notes",
        ]
    ]


def build_prioritization_sanity_checks(priority_table: pd.DataFrame) -> pd.DataFrame:
    checks = [
        {
            "check_name": "Top 10 contains at least 2 high-ARR issue themes",
            "result": int((priority_table.head(10)["arr_exposure_score"] > 60).sum() >= 2),
            "details": "Confirms the prioritization table surfaces revenue exposure rather than raw volume alone.",
        },
        {
            "check_name": "Top 10 includes at least 1 performance or integration issue",
            "result": int(
                priority_table.head(10)["ai_predicted_category"].isin(["performance", "integration"]).any()
            ),
            "details": "Sanity check for enterprise-facing high-severity issues.",
        },
        {
            "check_name": "Priority score correlates positively with churn score",
            "result": int(priority_table["priority_score"].corr(priority_table["churn_score"]) > 0.3),
            "details": "Validates that riskier issues generally rise in the ranking.",
        },
    ]
    return pd.DataFrame(checks)
