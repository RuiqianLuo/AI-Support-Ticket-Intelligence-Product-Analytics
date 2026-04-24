from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables"


st.set_page_config(
    page_title="AI Support Ticket Intelligence",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #e0f2fe 0%, #f8fafc 35%, #fefce8 100%);
    }
    h1, h2, h3 {
        font-family: "Aptos Display", "Trebuchet MS", sans-serif;
        letter-spacing: -0.02em;
        color: #0f172a;
    }
    .metric-card {
        background: rgba(255,255,255,0.86);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_table(name: str) -> pd.DataFrame:
    path = TABLE_DIR / f"{name}.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


executive = load_table("executive_kpis")
category_trends = load_table("category_monthly_trends")
segment_summary = load_table("segment_summary")
experiment_summary = load_table("experiment_summary")
priority_ranking = load_table("priority_ranking")
top_themes = load_table("top_recurring_themes")
recommendations = load_table("recommendations")
feature_request_trends = load_table("feature_request_trends")

st.title("AI Support Ticket Intelligence & Product Analytics")
st.caption(
    "A local portfolio app for support demand analysis, AI-assisted triage, and product prioritization."
)

page = st.sidebar.radio(
    "View",
    [
        "Executive Overview",
        "Issue Trends",
        "Segment Analysis",
        "Product Prioritization",
        "Experiment Analysis",
    ],
)

if page == "Executive Overview" and not executive.empty:
    row = executive.iloc[0]
    cols = st.columns(5)
    metrics = [
        ("Ticket Volume", f"{int(row['ticket_volume']):,}"),
        ("Avg Resolution", f"{row['avg_resolution_time_hours']:.1f}h"),
        ("Avg CSAT", f"{row['avg_csat']:.2f}"),
        ("Escalation Rate", f"{row['escalation_rate']:.1%}"),
        ("Churn-Risk Rate", f"{row['churn_risk_ticket_rate']:.1%}"),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(f"<div class='metric-card'><strong>{label}</strong><br><span style='font-size:1.7rem'>{value}</span></div>", unsafe_allow_html=True)
    overview_chart = px.line(
        category_trends.groupby("month", as_index=False)["ticket_count"].sum(),
        x="month",
        y="ticket_count",
        title="Monthly Support Demand",
        markers=True,
        color_discrete_sequence=["#0f766e"],
    )
    st.plotly_chart(overview_chart, use_container_width=True)
    st.subheader("Top Recommendations")
    for recommendation in recommendations["recommendation"].head(5).tolist():
        st.write(f"- {recommendation}")

if page == "Issue Trends" and not category_trends.empty:
    issue_filter = st.multiselect(
        "Issue categories",
        options=sorted(category_trends["issue_category"].unique().tolist()),
        default=sorted(category_trends["issue_category"].unique().tolist())[:5],
    )
    filtered = category_trends[category_trends["issue_category"].isin(issue_filter)]
    trend_chart = px.line(
        filtered,
        x="month",
        y="ticket_count",
        color="issue_category",
        markers=True,
        title="Category Trends Over Time",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    st.plotly_chart(trend_chart, use_container_width=True)
    if not top_themes.empty:
        st.subheader("Recurring AI-Detected Themes")
        st.dataframe(
            top_themes[
                ["week_start", "plan_tier", "region", "ai_predicted_category", "ai_detected_theme", "ticket_count", "summary"]
            ].head(15),
            use_container_width=True,
            hide_index=True,
        )

if page == "Segment Analysis" and not segment_summary.empty:
    metric = st.selectbox(
        "Metric",
        ["ticket_count", "avg_csat", "avg_resolution_time_hours", "escalation_rate", "churn_risk_ticket_rate"],
    )
    segment_chart = px.bar(
        segment_summary,
        x="plan_tier",
        y=metric,
        color="region",
        hover_data=["arr_band"],
        title=f"Segment Comparison: {metric.replace('_', ' ').title()}",
        barmode="group",
    )
    st.plotly_chart(segment_chart, use_container_width=True)
    st.dataframe(segment_summary.head(25), use_container_width=True, hide_index=True)

if page == "Product Prioritization" and not priority_ranking.empty:
    scatter = px.scatter(
        priority_ranking.head(30),
        x="arr_exposure_score",
        y="csat_impact_score",
        size="ticket_count",
        color="ai_predicted_category",
        hover_name="ai_detected_theme",
        title="Issue Prioritization Matrix",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    st.plotly_chart(scatter, use_container_width=True)
    st.dataframe(
        priority_ranking[
            [
                "ai_predicted_category",
                "ai_detected_theme",
                "ticket_count",
                "top_affected_segment",
                "primary_region",
                "priority_score",
                "recommended_action",
            ]
        ].head(20),
        use_container_width=True,
        hide_index=True,
    )
    if not feature_request_trends.empty:
        st.subheader("Feature Request Momentum")
        request_chart = px.bar(
            feature_request_trends.groupby("request_theme", as_index=False)["request_count"].sum().sort_values("request_count", ascending=False).head(10),
            x="request_theme",
            y="request_count",
            title="Top Feature Request Themes",
            color_discrete_sequence=["#f97316"],
        )
        st.plotly_chart(request_chart, use_container_width=True)

if page == "Experiment Analysis" and not experiment_summary.empty:
    cols = st.columns(2)
    with cols[0]:
        csat_chart = px.bar(
            experiment_summary,
            x="experiment_variant",
            y="avg_csat",
            title="Average CSAT by Variant",
            color="experiment_variant",
            color_discrete_sequence=["#334155", "#0ea5e9", "#f97316"],
        )
        st.plotly_chart(csat_chart, use_container_width=True)
    with cols[1]:
        resolution_chart = px.bar(
            experiment_summary,
            x="experiment_variant",
            y="avg_resolution_time_hours",
            title="Average Resolution Time by Variant",
            color="experiment_variant",
            color_discrete_sequence=["#334155", "#0ea5e9", "#f97316"],
        )
        st.plotly_chart(resolution_chart, use_container_width=True)
    st.dataframe(experiment_summary, use_container_width=True, hide_index=True)

