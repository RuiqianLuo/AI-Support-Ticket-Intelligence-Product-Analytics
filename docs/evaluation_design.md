# Evaluation Design

## Goal

Evaluate whether the AI layer is good enough to support analyst and PM workflows without overstating automation quality.

## 1. Classification Evaluation

**Method**
- train a lightweight TF-IDF + logistic regression baseline locally
- evaluate on a noisy, account-held-out test split
- report accuracy, macro precision, macro recall, and macro-F1

**Current result**
- Accuracy: `0.938`
- Macro precision: `0.9263`
- Macro recall: `0.9303`
- Macro-F1: `0.9250`

**Why this design is reasonable**
- holding out accounts tests generalization beyond memorizing account-specific phrasing
- noisy text simulates messy customer-authored support messages more honestly than clean templates alone

## 2. Summarization Quality Rubric

Summaries are evaluated on three dimensions using the review sheet in `outputs/evaluation/summarization_review_sheet.csv`:

- Coverage: does the summary mention the main pain point and scale of the issue?
- Specificity: does it name the segment, category, or recurring theme clearly?
- Actionability: does it include operational or customer-impact context that a team can act on?

Scoring approach:
- 1 = weak
- 3 = acceptable
- 5 = highly useful for a weekly review or decision memo

## 3. Prioritization Sanity Checks

The project includes sanity checks in `outputs/evaluation/prioritization_sanity_checks.csv`:
- top-ranked issues should not be driven by ticket volume alone
- enterprise and high-ARR pain should appear near the top when impact is severe
- the final score should correlate positively with churn pressure

## 4. Failure Cases To Review

- multi-symptom tickets that mix access and onboarding language
- bug vs performance ambiguity around exports, refresh jobs, and sync delays
- billing vs account-management ambiguity around renewals and amendments
- feature-request tickets that read like complaints but are actually enhancement asks

## 5. Known Limitations

- synthetic templates still underrepresent the full messiness of real support language
- theme summarization is rule-assisted rather than generative freeform summarization
- prioritization is a scoring framework, not a replacement for roadmap judgment
- experiment comparisons are directional because the data is simulated

## 6. Suggested Next Evaluation Step

Add a small human-reviewed benchmark set:
- 200 tickets with gold issue labels
- 25 weekly theme summary reviews
- 20 PM/support stakeholder reviews of top-priority issues

