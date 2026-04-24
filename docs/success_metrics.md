# Success Metrics

## North-Star Product Outcome

Help support and product teams turn support demand into faster, more trusted decisions.

## Core Success Metrics

| Metric | Definition | Why It Matters |
|---|---|---|
| Issue triage accuracy | Percent of tickets classified into the correct issue category | Measures whether AI can reduce manual tagging burden |
| Macro-F1 | Balanced classification quality across all issue categories | Prevents the model from only doing well on frequent classes |
| Summary usefulness | Analyst review score for whether theme summaries are specific and useful | Measures whether summaries help real review workflows |
| Prioritization usefulness | Stakeholder judgment that rankings reflect real product pain | Ensures scoring is decision-support, not math theater |
| Time saved for support review | Reduction in time required for weekly support demand analysis | Ties product value to workflow efficiency |
| Percent of tickets auto-classified | Share of tickets that can be classified without manual intervention | Measures coverage of the AI triage layer |
| Analyst trust proxy | Share of AI outputs accepted or retained after review | Captures whether teams trust the system enough to use it |
| Downstream decision usefulness | Share of prioritized issues that become accepted investigations, fixes, or roadmap inputs | Connects the tool to actual decisions |

## MVP Benchmarks In This Repo

- Classification accuracy: `0.938`
- Macro-F1: `0.925`
- 100% of synthetic tickets receive an AI category and priority score
- Summaries include segment, theme, volume, CSAT, resolution, and a representative signal

## Guardrail Metrics

- false confidence in prioritization
- excessive disagreement between AI category and analyst override
- over-focus on high-volume SMB issues at the expense of high-ARR enterprise pain
- experiment recommendations without enough sample size or context

