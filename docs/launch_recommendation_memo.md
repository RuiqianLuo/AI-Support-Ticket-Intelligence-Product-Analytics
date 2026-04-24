# Launch Recommendation Memo

## Summary

The current dataset and analytics outputs support launching this as an internal decision-support workflow for support ops and product planning. The strongest near-term value comes from reliability prioritization, renewal-season billing cleanup, and scaling the best experiment tactics.

## Recommendations

### 1. Prioritize performance reliability first

Why:
- `performance` is the worst category on both satisfaction and effort: average CSAT `2.48` and average resolution time `31.5h`
- `dashboard_latency` is the top-ranked issue theme with priority score `61.26`
- `api_timeout` is also in the top 3 priority themes

Recommendation:
- assign a product + engineering owner to analytics performance
- investigate dashboard latency, refresh jobs, and API timeout patterns together
- add status communication for known incident windows

### 2. Clean up SMB billing experience before renewal season

Why:
- `billing` grew the fastest over time, up `128%` comparing early 2025 vs early 2026
- `invoice_confusion` generated `632` tickets and remains one of the highest-priority themes
- billing problems are operationally cheaper than performance issues, but they create unnecessary support load and refund pressure

Recommendation:
- simplify invoice line items
- add self-serve explanations for seat true-ups and billing contact changes
- give support an approved billing clarification workflow for renewals

### 3. Treat enterprise support pain as a retention program

Why:
- enterprise accounts show the highest churn-risk ticket rate at `18.2%`
- enterprise EMEA is the riskiest segment at `23.8%`
- among high-ARR accounts, `performance`, `bug`, and `integration` dominate support demand

Recommendation:
- create an enterprise risk review that combines support pain, usage drops, and renewal-risk signals
- route enterprise performance and integration issues to a specialized queue
- use this view in CS and product QBR planning

### 4. Scale guided onboarding for access and setup workflows

Why:
- `guided_onboarding` delivered the best outcomes on targeted categories
- access CSAT under guided onboarding reached `3.514`, higher than both control and AI triage
- onboarding CSAT improved to `3.631` with resolution time down to `12.6h` versus `14.3h` in control

Recommendation:
- expand guided onboarding to new admin cohorts
- pair it with clearer setup guidance and permission templates
- monitor whether the improvement persists by region and plan tier

### 5. Use AI triage for technical issue routing, not as a blanket solution

Why:
- `ai_triage` improved targeted technical categories, especially bug, performance, and integration handling
- example: bug CSAT rose to `2.922` under AI triage versus `2.694` in control, with faster resolution
- the lift is strongest where routing and issue recognition matter most

Recommendation:
- deploy AI triage primarily for technical queues
- keep billing and account-management workflows more rules-driven
- measure whether agent trust and escalation savings justify broader rollout

