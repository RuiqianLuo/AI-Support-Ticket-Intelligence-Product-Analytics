from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .config import DB_PATH, FIGURES_DIR, SQL_DIR, SQL_OUTPUT_DIR, TABLES_DIR, ensure_project_directories
from .utils import export_dataframe


def build_dashboard_tables(
    accounts: pd.DataFrame,
    tickets: pd.DataFrame,
    feature_requests: pd.DataFrame,
    theme_summaries: pd.DataFrame,
    priority_table: pd.DataFrame,
    monthly_account_metrics: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    tickets = tickets.copy()
    tickets["month"] = pd.to_datetime(tickets["created_at"]).dt.to_period("M").dt.to_timestamp().dt.date.astype(str)
    executive = pd.DataFrame(
        [
            {
                "ticket_volume": int(len(tickets)),
                "avg_resolution_time_hours": round(float(tickets["resolution_time_hours"].mean()), 2),
                "avg_csat": round(float(tickets["csat_score"].mean()), 2),
                "escalation_rate": round(float(tickets["escalated_flag"].mean()), 4),
                "churn_risk_ticket_rate": round(float(tickets["churn_risk_flag"].mean()), 4),
                "refund_rate": round(float(tickets["refund_flag"].mean()), 4),
                "accounts_covered": int(accounts["account_id"].nunique()),
            }
        ]
    )
    category_monthly_trends = (
        tickets.groupby(["month", "issue_category"])
        .agg(
            ticket_count=("ticket_id", "count"),
            avg_csat=("csat_score", "mean"),
            avg_resolution_time_hours=("resolution_time_hours", "mean"),
        )
        .reset_index()
    )
    segment_summary = (
        tickets.merge(accounts[["account_id", "plan_tier", "arr_band", "region"]], on="account_id", how="left")
        .groupby(["plan_tier", "arr_band", "region"])
        .agg(
            ticket_count=("ticket_id", "count"),
            avg_csat=("csat_score", "mean"),
            avg_resolution_time_hours=("resolution_time_hours", "mean"),
            escalation_rate=("escalated_flag", "mean"),
            churn_risk_ticket_rate=("churn_risk_flag", "mean"),
        )
        .reset_index()
        .sort_values("ticket_count", ascending=False)
    )
    experiment_summary = (
        tickets.groupby("experiment_variant")
        .agg(
            ticket_count=("ticket_id", "count"),
            avg_resolution_time_hours=("resolution_time_hours", "mean"),
            avg_csat=("csat_score", "mean"),
            escalation_rate=("escalated_flag", "mean"),
            churn_risk_ticket_rate=("churn_risk_flag", "mean"),
        )
        .reset_index()
        .sort_values("avg_csat", ascending=False)
    )
    feature_request_trends = (
        feature_requests.assign(month=pd.to_datetime(feature_requests["created_at"]).dt.to_period("M").dt.to_timestamp().dt.date.astype(str))
        .groupby(["month", "request_theme"])
        .agg(
            request_count=("request_id", "count"),
            total_votes=("votes", "sum"),
            estimated_revenue_impact=("estimated_revenue_impact", "sum"),
        )
        .reset_index()
    )
    monthly_metrics_summary = (
        monthly_account_metrics.groupby("month")
        .agg(
            avg_mrr=("mrr", "mean"),
            avg_renewal_risk_score=("renewal_risk_score", "mean"),
            expansion_accounts=("expansion_flag", "sum"),
            contraction_accounts=("contraction_flag", "sum"),
        )
        .reset_index()
    )
    recommendations = priority_table.head(5).copy()
    recommendations["recommendation"] = (
        recommendations["ai_predicted_category"].str.replace("_", " ").str.title()
        + " / "
        + recommendations["ai_detected_theme"].str.replace("_", " ")
        + ": "
        + recommendations["recommended_action"]
    )
    top_themes = theme_summaries.sort_values("ticket_count", ascending=False).head(20)
    return {
        "executive_kpis": executive,
        "category_monthly_trends": category_monthly_trends,
        "segment_summary": segment_summary,
        "experiment_summary": experiment_summary,
        "feature_request_trends": feature_request_trends,
        "monthly_metrics_summary": monthly_metrics_summary,
        "priority_ranking": priority_table,
        "top_recurring_themes": top_themes,
        "recommendations": recommendations,
    }


def save_dashboard_tables(tables: dict[str, pd.DataFrame]) -> None:
    ensure_project_directories()
    for name, dataframe in tables.items():
        export_dataframe(dataframe, TABLES_DIR / f"{name}.csv")


def create_figures(tables: dict[str, pd.DataFrame]) -> None:
    ensure_project_directories()
    plt.style.use("seaborn-v0_8-whitegrid")

    trend = tables["category_monthly_trends"].pivot_table(
        index="month", columns="issue_category", values="ticket_count", fill_value=0
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    trend.plot(ax=ax, linewidth=2.2)
    ax.set_title("Ticket Volume Trends by Issue Category")
    ax.set_xlabel("Month")
    ax.set_ylabel("Ticket Count")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "ticket_volume_trends.png", dpi=180)
    plt.close(fig)

    priority = tables["priority_ranking"].head(10).sort_values("priority_score")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(priority["ai_detected_theme"], priority["priority_score"], color="#0f766e")
    ax.set_title("Top Prioritized Product Pain Points")
    ax.set_xlabel("Priority Score")
    ax.set_ylabel("Detected Theme")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "priority_ranking.png", dpi=180)
    plt.close(fig)

    experiment = tables["experiment_summary"]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(experiment["experiment_variant"], experiment["avg_csat"], color=["#334155", "#0ea5e9", "#f97316"])
    ax.set_title("Experiment Variant Comparison: Average CSAT")
    ax.set_ylabel("Average CSAT")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "experiment_csat.png", dpi=180)
    plt.close(fig)

    segment = tables["segment_summary"].groupby("plan_tier").agg(
        churn_risk_ticket_rate=("churn_risk_ticket_rate", "mean"),
        escalation_rate=("escalation_rate", "mean"),
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    segment.plot(kind="bar", ax=ax)
    ax.set_title("Support Risk by Plan Tier")
    ax.set_ylabel("Rate")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "segment_risk.png", dpi=180)
    plt.close(fig)


def execute_sql_reports(db_path: Path | str = DB_PATH) -> dict[str, pd.DataFrame]:
    ensure_project_directories()
    outputs: dict[str, pd.DataFrame] = {}
    connection = sqlite3.connect(str(db_path))
    try:
        for sql_file in sorted(SQL_DIR.glob("*.sql")):
            query = sql_file.read_text(encoding="utf-8")
            dataframe = pd.read_sql_query(query, connection)
            export_dataframe(dataframe, SQL_OUTPUT_DIR / f"{sql_file.stem}.csv")
            outputs[sql_file.stem] = dataframe
    finally:
        connection.close()
    return outputs


def save_analysis_manifest(tables: dict[str, pd.DataFrame], sql_outputs: dict[str, pd.DataFrame]) -> None:
    manifest = {
        "dashboard_tables": {name: len(df) for name, df in tables.items()},
        "sql_outputs": {name: len(df) for name, df in sql_outputs.items()},
    }
    (TABLES_DIR / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

