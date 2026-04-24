# Analytics Specification

## Core Business Questions

1. Which issue categories are growing fastest over time?
2. Which issue types have the worst CSAT and resolution performance?
3. Which customer segments are most associated with churn-risk tickets?
4. What issues are concentrated among high-ARR accounts?
5. What themes appear most often in feature requests?
6. Which product pain points should be prioritized first?
7. Did any experiment variant improve support outcomes?

## Primary Entities

- `accounts`: account segment, industry, region, plan, churn status
- `users`: support-active users and admin/operator context
- `tickets`: support event grain
- `ticket_messages`: raw text signal
- `product_usage`: monthly adoption and usage-drop indicators
- `feature_requests`: demand-side product input
- `experiments`: operational / product intervention metadata
- `monthly_account_metrics`: MRR and renewal-risk context

## Key Metrics

| Metric | Definition |
|---|---|
| Ticket volume | Count of tickets in a given slice |
| Average resolution time | Mean `resolution_time_hours` |
| Average CSAT | Mean `csat_score` |
| Escalation rate | Mean `escalated_flag` |
| Churn-risk ticket rate | Mean `churn_risk_flag` |
| Refund rate | Mean `refund_flag` |
| ARR exposed | Approximate ARR tied to affected accounts for a theme |
| Priority score | Weighted score across frequency, severity, CSAT impact, ARR exposure, churn risk, and request pressure |

## Analytical Dimensions

- time: month, week
- account segment: `plan_tier`, `arr_band`, `region`, `industry`
- issue classification: `issue_category`, `ai_predicted_category`, `ai_detected_theme`
- experiment: `experiment_variant`

## SQL Assets

The repo ships SQL reports for:
- top issue categories by volume
- average resolution time by category
- CSAT by category and segment
- churn-risk ticket rate by plan tier
- ARR exposed by issue theme
- feature-request trend analysis
- experiment comparison summary
- executive KPI summary

## Dashboard Views

### Executive Overview
- ticket volume
- average resolution time
- average CSAT
- escalation rate
- churn-risk ticket rate

### Issue Trends
- category trend lines
- recurring themes
- severity and reliability pressure

### Segment Analysis
- by plan tier
- by ARR band
- by region

### Product Prioritization
- issue ranking
- ARR exposure
- customer pain intensity
- recommended action

### Experiment Analysis
- variant-level CSAT
- variant-level resolution time
- variant-level risk and escalation comparison

