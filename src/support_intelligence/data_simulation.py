from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .config import DB_PATH, RAW_DATA_DIR, ensure_project_directories
from .utils import clamp, month_starts


ISSUE_CATEGORIES = [
    "billing",
    "onboarding",
    "bug",
    "feature_request",
    "access",
    "performance",
    "integration",
    "account_management",
]

SEVERITY_ORDER = ["low", "medium", "high", "critical"]
PRIORITY_ORDER = ["low", "medium", "high", "urgent"]

PLAN_CONFIG = {
    "SMB": {
        "arr_range": (7000, 45000),
        "seat_range": (8, 55),
        "ticket_rate": 1.95,
        "adoption": 0.54,
        "user_contacts": (2, 7),
        "category_weights": {
            "billing": 0.22,
            "onboarding": 0.19,
            "bug": 0.10,
            "feature_request": 0.12,
            "access": 0.15,
            "performance": 0.07,
            "integration": 0.05,
            "account_management": 0.10,
        },
    },
    "Growth": {
        "arr_range": (45000, 180000),
        "seat_range": (35, 180),
        "ticket_rate": 1.45,
        "adoption": 0.63,
        "user_contacts": (4, 10),
        "category_weights": {
            "billing": 0.08,
            "onboarding": 0.14,
            "bug": 0.17,
            "feature_request": 0.14,
            "access": 0.10,
            "performance": 0.15,
            "integration": 0.12,
            "account_management": 0.10,
        },
    },
    "Enterprise": {
        "arr_range": (180000, 720000),
        "seat_range": (150, 950),
        "ticket_rate": 1.10,
        "adoption": 0.71,
        "user_contacts": (6, 14),
        "category_weights": {
            "billing": 0.05,
            "onboarding": 0.06,
            "bug": 0.14,
            "feature_request": 0.12,
            "access": 0.15,
            "performance": 0.21,
            "integration": 0.19,
            "account_management": 0.08,
        },
    },
}

REGION_COUNTRIES = {
    "North America": ["United States", "Canada"],
    "EMEA": ["United Kingdom", "Germany", "Netherlands", "France"],
    "APAC": ["Singapore", "Australia", "Japan", "India"],
    "LATAM": ["Brazil", "Mexico", "Chile"],
}

COMPANY_PREFIXES = [
    "Blue",
    "North",
    "Signal",
    "Summit",
    "Vista",
    "Atlas",
    "Nimbus",
    "Cobalt",
    "Beacon",
    "Crescent",
    "Harbor",
    "Vertex",
    "Aster",
    "Kite",
    "Orbit",
]
COMPANY_NOUNS = [
    "Metrics",
    "Cloud",
    "Labs",
    "Works",
    "Systems",
    "Logic",
    "Stack",
    "Partners",
    "Ops",
    "Analytics",
    "Insights",
    "Digital",
]
COMPANY_SUFFIXES = ["Inc", "Co", "Group", "HQ", "Solutions", "Platform"]
INDUSTRIES = [
    "SaaS",
    "Fintech",
    "HealthTech",
    "Retail",
    "Logistics",
    "EdTech",
    "Cybersecurity",
    "Manufacturing",
]

THEMES_BY_CATEGORY = {
    "billing": ["invoice_confusion", "seat_true_up", "duplicate_charge", "tax_setup"],
    "onboarding": ["import_mapping", "setup_guidance", "workspace_configuration", "training_gap"],
    "bug": ["report_export", "notification_bug", "filter_logic", "data_sync_bug"],
    "feature_request": ["custom_dashboard", "audit_log", "bulk_actions", "advanced_permissions"],
    "access": ["sso_role_mapping", "mfa_lockout", "permission_setup", "password_reset"],
    "performance": ["dashboard_latency", "api_timeout", "report_refresh", "job_queue_delay"],
    "integration": ["crm_sync", "webhook_failure", "slack_alerts", "identity_provisioning"],
    "account_management": ["renewal_changes", "user_deactivation", "billing_contact", "contract_update"],
}

FEATURE_REQUEST_SEGMENT_THEMES = {
    "SMB": ["invoice_self_serve", "bulk_actions", "setup_templates", "custom_dashboard"],
    "Growth": ["custom_dashboard", "bulk_actions", "workflow_rules", "audit_log"],
    "Enterprise": ["audit_log", "advanced_permissions", "crm_sync", "sso_role_templates"],
}

EXPERIMENTS = [
    {
        "experiment_variant": "control",
        "variant_description": "Business-as-usual support workflow with standard routing.",
        "rollout_date": "2025-07-01",
    },
    {
        "experiment_variant": "ai_triage",
        "variant_description": "AI-assisted queue routing and suggested issue labels for complex tickets.",
        "rollout_date": "2025-11-01",
    },
    {
        "experiment_variant": "guided_onboarding",
        "variant_description": "Guided onboarding checklist and in-app setup support for new admins.",
        "rollout_date": "2025-10-15",
    },
]

THEME_LANGUAGE = {
    "invoice_confusion": {
        "problem": "the invoice does not match what we expected",
        "impact": "finance is blocking approval until the line items make sense",
        "keywords": ["invoice", "charge", "line item", "billing"],
    },
    "seat_true_up": {
        "problem": "the seat true-up charge feels higher than our admin dashboard shows",
        "impact": "our controller asked for a manual explanation before renewal",
        "keywords": ["seat", "true-up", "renewal", "charge"],
    },
    "duplicate_charge": {
        "problem": "we appear to have been charged twice this month",
        "impact": "the customer success lead escalated it internally already",
        "keywords": ["charged twice", "duplicate", "invoice", "refund"],
    },
    "tax_setup": {
        "problem": "our VAT and tax settings are not being applied correctly",
        "impact": "procurement is waiting for a corrected invoice",
        "keywords": ["VAT", "tax", "invoice", "procurement"],
    },
    "import_mapping": {
        "problem": "the CSV import keeps mis-mapping our fields",
        "impact": "our implementation timeline is slipping",
        "keywords": ["CSV", "import", "mapping", "columns"],
    },
    "setup_guidance": {
        "problem": "the initial setup flow leaves our admins unsure what to do next",
        "impact": "new users are waiting on configuration steps",
        "keywords": ["setup", "checklist", "guide", "admin"],
    },
    "workspace_configuration": {
        "problem": "workspace settings are scattered and hard to complete",
        "impact": "go-live is blocked on configuration",
        "keywords": ["workspace", "settings", "configure", "go-live"],
    },
    "training_gap": {
        "problem": "the team still needs onboarding help to use core workflows",
        "impact": "adoption is slower than expected",
        "keywords": ["training", "onboarding", "adoption", "workflow"],
    },
    "report_export": {
        "problem": "scheduled exports are failing when we run larger reports",
        "impact": "ops cannot deliver the weekly packet on time",
        "keywords": ["export", "report", "download", "failed"],
    },
    "notification_bug": {
        "problem": "users keep receiving duplicate notifications",
        "impact": "the support team is fielding repeated complaints",
        "keywords": ["notification", "duplicate", "alerts", "bug"],
    },
    "filter_logic": {
        "problem": "saved report filters are not applying correctly",
        "impact": "the analytics team no longer trusts the view",
        "keywords": ["filter", "logic", "saved report", "wrong data"],
    },
    "data_sync_bug": {
        "problem": "the synced records do not match source data counts",
        "impact": "leadership is questioning product reliability",
        "keywords": ["sync", "records", "source", "mismatch"],
    },
    "custom_dashboard": {
        "problem": "the team wants more flexible dashboards by role",
        "impact": "analysts are rebuilding views outside the product",
        "keywords": ["dashboard", "custom", "role-based", "view"],
    },
    "audit_log": {
        "problem": "admins need a clearer audit log for changes and access reviews",
        "impact": "security reviews are taking too much manual effort",
        "keywords": ["audit log", "security", "changes", "review"],
    },
    "bulk_actions": {
        "problem": "power users want bulk actions for repetitive admin work",
        "impact": "operations tasks still feel too manual",
        "keywords": ["bulk", "actions", "admin", "manual"],
    },
    "advanced_permissions": {
        "problem": "the current permission model is too coarse for large teams",
        "impact": "admins are creating workarounds outside the platform",
        "keywords": ["permissions", "roles", "admin", "enterprise"],
    },
    "sso_role_mapping": {
        "problem": "SSO provisioning is not mapping users to the right roles",
        "impact": "new users cannot access the workflows they need",
        "keywords": ["SSO", "role", "Okta", "provisioning"],
    },
    "mfa_lockout": {
        "problem": "users are getting stuck in the MFA flow",
        "impact": "support volume spikes whenever admins reset accounts",
        "keywords": ["MFA", "lockout", "login", "reset"],
    },
    "permission_setup": {
        "problem": "shared spaces are denying access even after permission changes",
        "impact": "teams cannot collaborate across functions",
        "keywords": ["permission", "access denied", "roles", "shared"],
    },
    "password_reset": {
        "problem": "password reset emails are looping or arriving late",
        "impact": "users cannot get back into the product quickly",
        "keywords": ["password reset", "email", "late", "login"],
    },
    "dashboard_latency": {
        "problem": "the analytics dashboard becomes slow during peak hours",
        "impact": "QBR prep and leadership reviews are delayed",
        "keywords": ["slow dashboard", "latency", "analytics", "peak hours"],
    },
    "api_timeout": {
        "problem": "the API times out on larger requests",
        "impact": "critical downstream workflows are failing",
        "keywords": ["API", "timeout", "request", "failing"],
    },
    "report_refresh": {
        "problem": "report refresh jobs are taking far longer than expected",
        "impact": "daily decision-making is happening on stale data",
        "keywords": ["refresh", "stale", "report", "slow"],
    },
    "job_queue_delay": {
        "problem": "background jobs are stuck in queue and missing SLAs",
        "impact": "customers are escalating to their account teams",
        "keywords": ["job queue", "delay", "SLA", "background"],
    },
    "crm_sync": {
        "problem": "the CRM sync is not updating account records cleanly",
        "impact": "revenue teams are correcting data manually",
        "keywords": ["CRM", "sync", "Salesforce", "records"],
    },
    "webhook_failure": {
        "problem": "webhooks are dropping payloads after recent configuration changes",
        "impact": "customer workflows are breaking downstream",
        "keywords": ["webhook", "payload", "failed", "integration"],
    },
    "slack_alerts": {
        "problem": "Slack alerts are inconsistent across channels",
        "impact": "ops leaders are missing time-sensitive notifications",
        "keywords": ["Slack", "alerts", "channel", "notification"],
    },
    "identity_provisioning": {
        "problem": "identity provisioning is delayed for large user batches",
        "impact": "IT cannot complete rollout on schedule",
        "keywords": ["identity", "provisioning", "batch", "IT"],
    },
    "renewal_changes": {
        "problem": "the team needs support updating renewal and contract details",
        "impact": "commercial conversations are stalling",
        "keywords": ["renewal", "contract", "quote", "details"],
    },
    "user_deactivation": {
        "problem": "bulk user deactivation is slower than expected",
        "impact": "security and HR workflows are delayed",
        "keywords": ["deactivation", "users", "bulk", "security"],
    },
    "billing_contact": {
        "problem": "billing contacts are not updating across invoices and reminders",
        "impact": "collections and customer ops are both involved",
        "keywords": ["billing contact", "invoice", "reminder", "update"],
    },
    "contract_update": {
        "problem": "contract amendments need too many manual support touches",
        "impact": "the account team is spending time on administrative work",
        "keywords": ["contract", "amendment", "support", "manual"],
    },
}


@dataclass
class SimulationBundle:
    tables: Dict[str, pd.DataFrame]
    assumptions: Dict[str, object]


def _weighted_choice(rng: np.random.Generator, weights: Dict[str, float]) -> str:
    labels = list(weights.keys())
    probabilities = np.array(list(weights.values()), dtype=float)
    probabilities = probabilities / probabilities.sum()
    return str(rng.choice(labels, p=probabilities))


def _month_diff(later: pd.Timestamp, earlier: pd.Timestamp) -> int:
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)


def _company_name(rng: np.random.Generator) -> str:
    return (
        f"{rng.choice(COMPANY_PREFIXES)} "
        f"{rng.choice(COMPANY_NOUNS)} "
        f"{rng.choice(COMPANY_SUFFIXES)}"
    )


def _arr_band(arr: float) -> str:
    if arr < 25000:
        return "<25k"
    if arr < 75000:
        return "25k-75k"
    if arr < 250000:
        return "75k-250k"
    return "250k+"


def _severity_from_context(
    rng: np.random.Generator,
    plan_tier: str,
    category: str,
    usage_drop_flag: int,
) -> str:
    base_weights = {
        "billing": np.array([0.36, 0.41, 0.19, 0.04]),
        "onboarding": np.array([0.28, 0.44, 0.24, 0.04]),
        "bug": np.array([0.10, 0.35, 0.38, 0.17]),
        "feature_request": np.array([0.55, 0.31, 0.12, 0.02]),
        "access": np.array([0.18, 0.46, 0.28, 0.08]),
        "performance": np.array([0.08, 0.28, 0.41, 0.23]),
        "integration": np.array([0.08, 0.31, 0.39, 0.22]),
        "account_management": np.array([0.28, 0.43, 0.23, 0.06]),
    }[category].copy()
    if plan_tier == "Enterprise":
        base_weights += np.array([-0.04, -0.02, 0.03, 0.03])
    if usage_drop_flag and category in {"performance", "bug", "integration"}:
        base_weights += np.array([-0.05, -0.04, 0.04, 0.05])
    base_weights = np.clip(base_weights, 0.02, None)
    base_weights = base_weights / base_weights.sum()
    return str(rng.choice(SEVERITY_ORDER, p=base_weights))


def _priority_from_severity(severity: str, plan_tier: str) -> str:
    lookup = {
        "low": "low",
        "medium": "medium",
        "high": "high",
        "critical": "urgent",
    }
    priority = lookup[severity]
    if plan_tier == "Enterprise" and priority == "high":
        return "urgent"
    return priority


def _message_text(
    rng: np.random.Generator,
    theme: str,
    sender_type: str,
    plan_tier: str,
    company_name: str,
    region: str,
    issue_category: str,
) -> str:
    language = THEME_LANGUAGE[theme]
    noise = rng.choice(
        [
            "pls advise",
            "seeing this again",
            "same blocker as yesterday",
            "screen recording attached",
            "cc'ing our admin lead",
            "this is affecting our rollout",
            "happening in prod only",
            "it worked last week",
        ]
    )
    if sender_type == "customer":
        opener = rng.choice(
            [
                f"Hi team, {language['problem']}.",
                f"We're running into an issue where {language['problem']}.",
                f"Need help quickly: {language['problem']}.",
            ]
        )
        context = (
            f"{language['impact']}. "
            f"We're a {plan_tier.lower()} account in {region} and this is not ideal for {company_name}. "
            f"{noise}."
        )
        return f"{opener} {context}"
    return (
        f"Thanks for flagging this. We have logged the {issue_category} issue and are checking "
        f"{', '.join(language['keywords'][:2])}. We will update you after reviewing the logs and the account setup."
    )


def _choose_category(
    rng: np.random.Generator,
    plan_tier: str,
    created_at: pd.Timestamp,
    usage_drop_flag: int,
    months_since_signup: int,
) -> str:
    weights = PLAN_CONFIG[plan_tier]["category_weights"].copy()
    if months_since_signup <= 2:
        weights["onboarding"] += 0.10
        weights["access"] += 0.05
    if usage_drop_flag:
        weights["performance"] += 0.06
        weights["bug"] += 0.04
    if created_at.strftime("%Y-%m") in {"2025-09", "2025-10", "2025-11"}:
        weights["performance"] += 0.05
        weights["bug"] += 0.04
    if created_at.strftime("%Y-%m") in {"2026-01", "2026-02"}:
        weights["billing"] += 0.07
    return _weighted_choice(rng, weights)


def generate_accounts(
    rng: np.random.Generator,
    n_accounts: int,
    months: pd.DatetimeIndex,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rows: List[dict] = []
    profiles: List[dict] = []
    plan_distribution = {"SMB": 0.55, "Growth": 0.28, "Enterprise": 0.17}
    experiments = [item["experiment_variant"] for item in EXPERIMENTS]
    experiment_weights = [0.40, 0.30, 0.30]

    for index in range(1, n_accounts + 1):
        plan_tier = _weighted_choice(rng, plan_distribution)
        cfg = PLAN_CONFIG[plan_tier]
        region = _weighted_choice(
            rng,
            {
                "North America": 0.46,
                "EMEA": 0.24,
                "APAC": 0.20,
                "LATAM": 0.10,
            },
        )
        country = str(rng.choice(REGION_COUNTRIES[region]))
        arr = float(rng.integers(cfg["arr_range"][0], cfg["arr_range"][1]))
        seat_count = int(rng.integers(cfg["seat_range"][0], cfg["seat_range"][1]))
        signup_date = pd.Timestamp("2024-02-01") + pd.to_timedelta(
            int(rng.integers(0, 730)), unit="D"
        )
        signup_date = min(signup_date, months[-1] - pd.Timedelta(days=10))
        renewal_date = signup_date + pd.to_timedelta(365, unit="D")
        account_id = f"ACC-{index:04d}"
        company_name = _company_name(rng)
        experiment_variant = str(rng.choice(experiments, p=experiment_weights))
        pain_bias = float(np.clip(rng.normal(1.0, 0.22), 0.55, 1.55))
        product_fit = float(np.clip(rng.normal(1.0, 0.18), 0.60, 1.40))
        rows.append(
            {
                "account_id": account_id,
                "company_name": company_name,
                "plan_tier": plan_tier,
                "arr_band": _arr_band(arr),
                "industry": str(rng.choice(INDUSTRIES)),
                "region": region,
                "signup_date": signup_date.date().isoformat(),
                "renewal_date": renewal_date.date().isoformat(),
                "current_status": "active",
                "churn_flag": 0,
            }
        )
        profiles.append(
            {
                "account_id": account_id,
                "company_name": company_name,
                "plan_tier": plan_tier,
                "arr": arr,
                "seat_count": seat_count,
                "country": country,
                "region": region,
                "signup_date": signup_date,
                "renewal_date": renewal_date,
                "base_ticket_rate": cfg["ticket_rate"],
                "base_adoption": cfg["adoption"],
                "pain_bias": pain_bias,
                "product_fit": product_fit,
                "experiment_variant": experiment_variant,
                "industry": rows[-1]["industry"],
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(profiles)


def generate_users(rng: np.random.Generator, profiles: pd.DataFrame) -> pd.DataFrame:
    role_weights = {
        "SMB": {"Admin": 0.30, "Operations Manager": 0.24, "Analyst": 0.22, "Support Lead": 0.14, "Executive": 0.10},
        "Growth": {"Admin": 0.18, "Operations Manager": 0.22, "Analyst": 0.27, "Support Lead": 0.19, "Executive": 0.14},
        "Enterprise": {"Admin": 0.14, "Operations Manager": 0.25, "Analyst": 0.23, "Support Lead": 0.20, "Executive": 0.18},
    }
    rows: List[dict] = []
    user_counter = 1
    snapshot_date = pd.Timestamp("2026-03-31")
    for profile in profiles.to_dict("records"):
        cfg = PLAN_CONFIG[profile["plan_tier"]]
        min_users, max_users = cfg["user_contacts"]
        user_count = int(np.clip(profile["seat_count"] // 18, min_users, max_users))
        weights = role_weights[profile["plan_tier"]]
        for _ in range(user_count):
            role = _weighted_choice(np.random.default_rng(rng.integers(0, 1_000_000)), weights)
            last_active = snapshot_date - pd.to_timedelta(int(rng.integers(1, 45)), unit="D")
            rows.append(
                {
                    "user_id": f"USR-{user_counter:05d}",
                    "account_id": profile["account_id"],
                    "role": role,
                    "seat_count": int(profile["seat_count"]),
                    "last_active_date": last_active.date().isoformat(),
                    "country": profile["country"],
                }
            )
            user_counter += 1
    return pd.DataFrame(rows)


def generate_product_usage(
    rng: np.random.Generator,
    profiles: pd.DataFrame,
    months: pd.DatetimeIndex,
) -> pd.DataFrame:
    rows: List[dict] = []
    for profile in profiles.to_dict("records"):
        prev_active_users: float | None = None
        for month in months:
            if month < pd.Timestamp(profile["signup_date"]).replace(day=1):
                continue
            seasonality = 0.94 if month.month in {7, 12} else 1.0
            early_onboarding_penalty = 0.88 if _month_diff(month, profile["signup_date"]) < 3 else 1.0
            performance_shock = (
                0.82
                if month.strftime("%Y-%m") in {"2025-09", "2025-10", "2025-11"} and profile["plan_tier"] != "SMB"
                else 1.0
            )
            active_ratio = (
                profile["base_adoption"]
                * profile["product_fit"]
                * seasonality
                * early_onboarding_penalty
                * performance_shock
                * np.clip(rng.normal(1.0, 0.06), 0.78, 1.16)
            )
            active_users = int(
                np.clip(round(profile["seat_count"] * active_ratio), 4, profile["seat_count"])
            )
            feature_a = int(active_users * np.clip(rng.normal(6.5, 1.1), 3.2, 9.5))
            feature_b = int(active_users * np.clip(rng.normal(4.1, 0.8), 1.3, 6.8))
            feature_c = int(active_users * np.clip(rng.normal(3.2, 0.7), 1.0, 5.6))
            if profile["plan_tier"] == "Enterprise":
                feature_b = int(feature_b * 1.25)
            if profile["plan_tier"] == "SMB":
                feature_c = int(feature_c * 0.78)
            login_frequency = float(np.clip(rng.normal(4.2, 0.7), 2.1, 6.2))
            usage_drop_flag = 0
            if prev_active_users is not None and active_users < prev_active_users * 0.86:
                usage_drop_flag = 1
            if (
                month.strftime("%Y-%m") in {"2025-09", "2025-10", "2025-11"}
                and profile["plan_tier"] == "Enterprise"
                and rng.random() < 0.25
            ):
                usage_drop_flag = 1
            rows.append(
                {
                    "account_id": profile["account_id"],
                    "month": month.date().isoformat(),
                    "active_users": active_users,
                    "feature_a_usage": feature_a,
                    "feature_b_usage": feature_b,
                    "feature_c_usage": feature_c,
                    "login_frequency": round(login_frequency, 2),
                    "usage_drop_flag": usage_drop_flag,
                }
            )
            prev_active_users = active_users
    return pd.DataFrame(rows)


def generate_tickets_and_messages(
    rng: np.random.Generator,
    profiles: pd.DataFrame,
    users: pd.DataFrame,
    product_usage: pd.DataFrame,
    months: pd.DatetimeIndex,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    usage_lookup = {
        (row["account_id"], row["month"]): row
        for row in product_usage.to_dict("records")
    }
    users_by_account = users.groupby("account_id")["user_id"].apply(list).to_dict()
    ticket_rows: List[dict] = []
    message_rows: List[dict] = []
    ticket_counter = 1
    message_counter = 1

    for profile in profiles.to_dict("records"):
        signup_month = pd.Timestamp(profile["signup_date"]).replace(day=1)
        for month in months:
            if month < signup_month:
                continue
            usage_row = usage_lookup[(profile["account_id"], month.date().isoformat())]
            months_since_signup = _month_diff(month, signup_month)
            seasonality = 1.12 if month.month in {1, 2} else 1.0
            if month.strftime("%Y-%m") in {"2025-09", "2025-10", "2025-11"}:
                seasonality *= 1.08
            ticket_rate = (
                profile["base_ticket_rate"]
                * profile["pain_bias"]
                * seasonality
                * (1.18 if months_since_signup <= 2 else 1.0)
                * (1.20 if usage_row["usage_drop_flag"] else 1.0)
            )
            monthly_ticket_count = int(max(0, rng.poisson(ticket_rate)))
            for _ in range(monthly_ticket_count):
                created_at = month + pd.to_timedelta(int(rng.integers(0, 27)), unit="D") + pd.to_timedelta(
                    int(rng.integers(8, 19)), unit="h"
                )
                category = _choose_category(
                    rng,
                    profile["plan_tier"],
                    created_at,
                    int(usage_row["usage_drop_flag"]),
                    months_since_signup,
                )
                theme = str(rng.choice(THEMES_BY_CATEGORY[category]))
                severity = _severity_from_context(
                    rng,
                    profile["plan_tier"],
                    category,
                    int(usage_row["usage_drop_flag"]),
                )
                priority = _priority_from_severity(severity, profile["plan_tier"])
                base_resolution = {
                    "billing": 9,
                    "onboarding": 14,
                    "bug": 20,
                    "feature_request": 30,
                    "access": 8,
                    "performance": 24,
                    "integration": 26,
                    "account_management": 12,
                }[category]
                severity_multiplier = {"low": 0.8, "medium": 1.0, "high": 1.3, "critical": 1.8}[severity]
                plan_multiplier = {"SMB": 0.95, "Growth": 1.0, "Enterprise": 1.18}[profile["plan_tier"]]
                experiment_multiplier = 1.0
                if profile["experiment_variant"] == "ai_triage" and created_at >= pd.Timestamp("2025-11-01"):
                    if category in {"bug", "performance", "integration"}:
                        experiment_multiplier *= 0.85
                if profile["experiment_variant"] == "guided_onboarding" and created_at >= pd.Timestamp("2025-10-15"):
                    if category in {"onboarding", "access"}:
                        experiment_multiplier *= 0.78
                resolution = base_resolution * severity_multiplier * plan_multiplier * experiment_multiplier
                resolution *= float(np.clip(rng.normal(1.0, 0.18), 0.72, 1.45))
                resolution_time_hours = round(float(np.clip(resolution, 2.0, 144.0)), 2)
                escalated_probability = {
                    "billing": 0.10,
                    "onboarding": 0.12,
                    "bug": 0.24,
                    "feature_request": 0.05,
                    "access": 0.16,
                    "performance": 0.32,
                    "integration": 0.30,
                    "account_management": 0.11,
                }[category]
                if severity in {"high", "critical"}:
                    escalated_probability += 0.12
                if profile["plan_tier"] == "Enterprise":
                    escalated_probability += 0.05
                if profile["experiment_variant"] == "ai_triage" and category in {"bug", "performance", "integration"}:
                    escalated_probability -= 0.06
                escalated_flag = int(rng.random() < clamp(escalated_probability, 0.02, 0.82))
                refund_probability = 0.03
                if category == "billing":
                    refund_probability += 0.16
                if category in {"bug", "performance"}:
                    refund_probability += 0.08
                if profile["plan_tier"] == "SMB":
                    refund_probability += 0.04
                refund_flag = int(rng.random() < clamp(refund_probability, 0.01, 0.65))
                churn_probability = 0.05
                if category in {"performance", "integration", "billing"}:
                    churn_probability += 0.08
                if severity in {"high", "critical"}:
                    churn_probability += 0.10
                if usage_row["usage_drop_flag"]:
                    churn_probability += 0.08
                if profile["plan_tier"] == "Enterprise":
                    churn_probability += 0.04
                churn_risk_flag = int(rng.random() < clamp(churn_probability, 0.02, 0.72))
                csat_base = {
                    "billing": 3.55,
                    "onboarding": 3.65,
                    "bug": 3.10,
                    "feature_request": 3.75,
                    "access": 3.45,
                    "performance": 2.95,
                    "integration": 3.05,
                    "account_management": 3.70,
                }[category]
                csat_penalty = (resolution_time_hours / 48) * 0.45
                csat_penalty += 0.32 if escalated_flag else 0.0
                csat_penalty += 0.28 if refund_flag else 0.0
                csat_penalty += 0.34 if churn_risk_flag else 0.0
                if profile["experiment_variant"] == "ai_triage" and category in {"bug", "performance", "integration"}:
                    csat_base += 0.18
                if profile["experiment_variant"] == "guided_onboarding" and category in {"onboarding", "access"}:
                    csat_base += 0.24
                csat_score = round(float(np.clip(csat_base - csat_penalty + rng.normal(0.0, 0.35), 1.0, 5.0)), 2)
                channel = _weighted_choice(
                    rng,
                    {
                        "email": 0.38,
                        "chat": 0.28 if profile["plan_tier"] != "Enterprise" else 0.15,
                        "web_form": 0.22,
                        "phone": 0.12 if profile["plan_tier"] == "Enterprise" else 0.07,
                    },
                )
                ticket_id = f"TKT-{ticket_counter:06d}"
                ticket_rows.append(
                    {
                        "ticket_id": ticket_id,
                        "account_id": profile["account_id"],
                        "user_id": str(rng.choice(users_by_account[profile["account_id"]])),
                        "created_at": created_at.isoformat(),
                        "channel": channel,
                        "issue_category": category,
                        "severity": severity,
                        "priority": priority,
                        "resolution_time_hours": resolution_time_hours,
                        "escalated_flag": escalated_flag,
                        "csat_score": csat_score,
                        "refund_flag": refund_flag,
                        "churn_risk_flag": churn_risk_flag,
                        "experiment_variant": profile["experiment_variant"],
                        "ai_predicted_category": None,
                        "ai_detected_theme": None,
                        "ai_priority_score": None,
                    }
                )
                first_message = _message_text(
                    rng,
                    theme,
                    "customer",
                    profile["plan_tier"],
                    profile["company_name"],
                    profile["region"],
                    category,
                )
                response_message = _message_text(
                    rng,
                    theme,
                    "agent",
                    profile["plan_tier"],
                    profile["company_name"],
                    profile["region"],
                    category,
                )
                follow_up_message = (
                    f"Following up because {THEME_LANGUAGE[theme]['impact']}. "
                    f"We also noticed related keywords: {', '.join(THEME_LANGUAGE[theme]['keywords'][:3])}. "
                    f"Please share ETA if possible."
                )
                timeline = [
                    (created_at, "customer", first_message),
                    (created_at + pd.to_timedelta(int(rng.integers(1, 8)), unit="h"), "agent", response_message),
                    (created_at + pd.to_timedelta(int(rng.integers(9, 36)), unit="h"), "customer", follow_up_message),
                ]
                if escalated_flag:
                    escalation_note = (
                        f"We've escalated this internally because {THEME_LANGUAGE[theme]['problem']} "
                        f"and the account impact is above normal."
                    )
                    timeline.append(
                        (
                            created_at + pd.to_timedelta(int(rng.integers(18, 48)), unit="h"),
                            "agent",
                            escalation_note,
                        )
                    )
                for timestamp, sender_type, message_text in timeline:
                    message_rows.append(
                        {
                            "message_id": f"MSG-{message_counter:07d}",
                            "ticket_id": ticket_id,
                            "sender_type": sender_type,
                            "message_text": message_text,
                            "timestamp": timestamp.isoformat(),
                        }
                    )
                    message_counter += 1
                ticket_counter += 1
    return pd.DataFrame(ticket_rows), pd.DataFrame(message_rows)


def generate_feature_requests(
    rng: np.random.Generator,
    profiles: pd.DataFrame,
    tickets: pd.DataFrame,
) -> pd.DataFrame:
    ticket_lookup = tickets.groupby(["account_id", "issue_category"]).size().to_dict()
    rows: List[dict] = []
    counter = 1
    for profile in profiles.to_dict("records"):
        request_count = int(
            np.clip(
                rng.poisson(0.9 if profile["plan_tier"] == "SMB" else 1.3 if profile["plan_tier"] == "Growth" else 1.7),
                0,
                5,
            )
        )
        themes = FEATURE_REQUEST_SEGMENT_THEMES[profile["plan_tier"]]
        for _ in range(request_count):
            request_theme = str(rng.choice(themes))
            created_at = profile["signup_date"] + pd.to_timedelta(int(rng.integers(30, 520)), unit="D")
            created_at = min(created_at, pd.Timestamp("2026-03-31"))
            linked_ticket_count = int(
                ticket_lookup.get((profile["account_id"], "feature_request"), 0)
                + rng.integers(0, 4)
            )
            estimated_revenue_impact = round(
                float(profile["arr"] * np.clip(rng.normal(0.08, 0.03), 0.03, 0.18)),
                2,
            )
            votes = int(
                np.clip(
                    rng.normal(3.5 if profile["plan_tier"] == "SMB" else 6.0 if profile["plan_tier"] == "Growth" else 10.0, 2.0),
                    1,
                    20,
                )
            )
            rows.append(
                {
                    "request_id": f"FR-{counter:05d}",
                    "account_id": profile["account_id"],
                    "created_at": created_at.date().isoformat(),
                    "request_theme": request_theme,
                    "votes": votes,
                    "linked_ticket_count": linked_ticket_count,
                    "estimated_revenue_impact": estimated_revenue_impact,
                }
            )
            counter += 1
    return pd.DataFrame(rows)


def generate_monthly_account_metrics(
    rng: np.random.Generator,
    accounts: pd.DataFrame,
    profiles: pd.DataFrame,
    product_usage: pd.DataFrame,
    tickets: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    profiles_enriched = profiles.merge(accounts[["account_id", "arr_band"]], on="account_id", how="left")
    tickets = tickets.copy()
    tickets["month"] = pd.to_datetime(tickets["created_at"]).dt.to_period("M").dt.to_timestamp().dt.date.astype(str)
    monthly_ticket_summary = (
        tickets.groupby(["account_id", "month"])
        .agg(
            monthly_tickets=("ticket_id", "count"),
            avg_csat=("csat_score", "mean"),
            escalated_rate=("escalated_flag", "mean"),
            churn_risk_rate=("churn_risk_flag", "mean"),
            refund_rate=("refund_flag", "mean"),
            avg_resolution=("resolution_time_hours", "mean"),
        )
        .reset_index()
    )
    metrics = product_usage.merge(monthly_ticket_summary, on=["account_id", "month"], how="left").fillna(
        {
            "monthly_tickets": 0,
            "avg_csat": 4.2,
            "escalated_rate": 0.0,
            "churn_risk_rate": 0.0,
            "refund_rate": 0.0,
            "avg_resolution": 0.0,
        }
    )
    profile_lookup = profiles_enriched.set_index("account_id").to_dict("index")
    metric_rows: List[dict] = []
    account_status_rows: List[dict] = []
    latest_by_account = metrics.sort_values("month").groupby("account_id").tail(1)
    for row in metrics.to_dict("records"):
        profile = profile_lookup[row["account_id"]]
        monthly_mrr = round(profile["arr"] / 12.0, 2)
        usage_ratio = row["active_users"] / max(profile["seat_count"], 1)
        contraction_probability = clamp(
            0.04
            + (0.10 if row["usage_drop_flag"] else 0.0)
            + (0.10 if row["churn_risk_rate"] > 0.25 else 0.0),
            0.02,
            0.55,
        )
        expansion_probability = clamp(
            0.05
            + (0.12 if usage_ratio > 0.72 else 0.0)
            + (0.08 if row["avg_csat"] >= 4.1 else 0.0)
            - (0.06 if row["usage_drop_flag"] else 0.0),
            0.02,
            0.48,
        )
        contraction_flag = int(rng.random() < contraction_probability)
        expansion_flag = int(rng.random() < expansion_probability)
        renewal_risk_score = (
            0.14
            + (0.18 if row["usage_drop_flag"] else 0.0)
            + row["escalated_rate"] * 0.20
            + row["churn_risk_rate"] * 0.28
            + max(0.0, (3.6 - float(row["avg_csat"])) / 4.0)
            + (0.08 if contraction_flag else 0.0)
            - (0.05 if expansion_flag else 0.0)
        )
        renewal_risk_score = round(clamp(float(renewal_risk_score), 0.03, 0.97), 3)
        metric_rows.append(
            {
                "account_id": row["account_id"],
                "month": row["month"],
                "mrr": monthly_mrr,
                "expansion_flag": expansion_flag,
                "contraction_flag": contraction_flag,
                "renewal_risk_score": renewal_risk_score,
            }
        )
    updated_accounts = accounts.copy()
    final_metrics = latest_by_account.merge(
        pd.DataFrame(metric_rows), on=["account_id", "month"], how="left"
    )
    for final_row in final_metrics.to_dict("records"):
        risk = float(final_row["renewal_risk_score"])
        if risk >= 0.78 and final_row["usage_drop_flag"]:
            status = "churned"
            churn_flag = 1
        elif risk >= 0.56:
            status = "at_risk"
            churn_flag = 0
        else:
            status = "active"
            churn_flag = 0
        account_status_rows.append(
            {
                "account_id": final_row["account_id"],
                "current_status": status,
                "churn_flag": churn_flag,
            }
        )
    status_df = pd.DataFrame(account_status_rows)
    updated_accounts = updated_accounts.drop(columns=["current_status", "churn_flag"]).merge(
        status_df, on="account_id", how="left"
    )
    return pd.DataFrame(metric_rows), updated_accounts


def build_dataset(random_seed: int = 42, n_accounts: int = 320) -> SimulationBundle:
    rng = np.random.default_rng(random_seed)
    months = month_starts("2025-01-01", "2026-03-01")
    accounts, profiles = generate_accounts(rng, n_accounts=n_accounts, months=months)
    users = generate_users(rng, profiles)
    product_usage = generate_product_usage(rng, profiles, months)
    tickets, ticket_messages = generate_tickets_and_messages(rng, profiles, users, product_usage, months)
    feature_requests = generate_feature_requests(rng, profiles, tickets)
    monthly_account_metrics, updated_accounts = generate_monthly_account_metrics(
        rng, accounts, profiles, product_usage, tickets
    )
    experiments = pd.DataFrame(EXPERIMENTS)
    assumptions = {
        "random_seed": random_seed,
        "history_start": str(months.min().date()),
        "history_end": str(months.max().date()),
        "n_accounts": n_accounts,
        "plan_distribution": {"SMB": 0.55, "Growth": 0.28, "Enterprise": 0.17},
        "ticket_shocks": [
            "Performance and bug issues spike from Sep-Nov 2025.",
            "Billing confusion increases around Jan-Feb 2026 renewals.",
            "Guided onboarding improves onboarding/access outcomes after mid-Oct 2025.",
            "AI triage improves bug/performance/integration handling after Nov 2025.",
        ],
    }
    return SimulationBundle(
        tables={
            "accounts": updated_accounts,
            "users": users,
            "tickets": tickets,
            "ticket_messages": ticket_messages,
            "product_usage": product_usage,
            "feature_requests": feature_requests,
            "experiments": experiments,
            "monthly_account_metrics": monthly_account_metrics,
        },
        assumptions=assumptions,
    )


def save_dataset(bundle: SimulationBundle, db_path: str | None = None) -> Dict[str, str]:
    ensure_project_directories()
    db_target = DB_PATH if db_path is None else Path(db_path)
    output_paths: Dict[str, str] = {}
    for name, df in bundle.tables.items():
        csv_path = RAW_DATA_DIR / f"{name}.csv"
        df.to_csv(csv_path, index=False)
        output_paths[name] = str(csv_path)
    connection = sqlite3.connect(str(db_target))
    try:
        for name, df in bundle.tables.items():
            df.to_sql(name, connection, if_exists="replace", index=False)
    finally:
        connection.close()
    return output_paths
