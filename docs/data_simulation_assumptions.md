# Data Simulation Assumptions

## Time Window

- monthly history runs from January 2025 to March 2026
- ticket timestamps are generated within that window
- experiments have rollout dates in the same period

## Dataset Size

- 320 accounts
- 1,564 users
- 7,148 tickets
- 22,924 ticket messages
- 333 feature requests
- 3 experiment variants
- 3,846 monthly account metric rows

## Segment Logic

- `SMB` accounts have lower ARR, more tickets per account, and more billing/onboarding demand
- `Growth` accounts have more mixed bug, feature, and integration demand
- `Enterprise` accounts have fewer tickets per account but higher severity, longer resolution time, and higher churn-risk exposure

## Behavior Rules

- early-life accounts generate more onboarding and access tickets
- usage drops increase the likelihood of bug, performance, and churn-risk tickets
- Sep-Nov 2025 creates a performance/bug pressure spike
- Jan-Feb 2026 increases billing confusion around renewal and seat true-ups
- feature request demand varies by segment, with enterprise leaning toward audit, permissioning, and integration depth

## Experiment Rules

- `guided_onboarding` improves access/onboarding resolution and CSAT after mid-October 2025
- `ai_triage` improves routing and handling for bug, performance, and integration issues after November 2025
- `control` follows the default workflow

## AI Assumptions

- issue-category predictions come from a local TF-IDF + logistic regression model
- recurring themes are detected with transparent keyword rules
- issue prioritization is a weighted score using operational pain and business exposure signals

## Important Caveat

This dataset is intentionally synthetic. The goal is not to claim production truth, but to create a believable analytics environment with internal consistency, realistic tradeoffs, and enough noise for meaningful portfolio work.

