# Implementation Notes

This document explains how the project was implemented and summarizes interview questions that are likely to come up when discussing the work.

## Implementation Steps

1. Define the product problem.

The project starts from a realistic SaaS support workflow: customers submit billing questions, onboarding issues, bug reports, access problems, performance complaints, integration failures, account-management requests, and feature requests. The goal is to turn those support signals into product and operations decisions.

2. Design the data model.

The repository uses eight core tables:
- `accounts`
- `users`
- `tickets`
- `ticket_messages`
- `product_usage`
- `feature_requests`
- `experiments`
- `monthly_account_metrics`

These tables connect support activity to account segment, product usage, ARR exposure, churn risk, feature demand, and experiment assignment.

3. Generate synthetic SaaS data.

The data generator in `scripts/generate_data.py` calls the simulation logic in `src/support_intelligence/data_simulation.py`. It creates coherent account, user, ticket, message, usage, feature-request, experiment, and monthly account metric data.

The simulation includes business rules such as:
- SMB accounts have more billing and onboarding demand
- enterprise accounts have fewer tickets but higher severity and churn risk
- performance and integration issues tend to have lower CSAT and longer resolution times
- billing demand increases around renewal periods
- experiment variants affect targeted support outcomes

4. Store the dataset locally.

The generated data is written to:
- CSV files in `data/raw/`
- a SQLite database in `data/warehouse/support_intelligence.db`

This keeps the project easy to inspect, rerun, and query without external infrastructure.

5. Build the AI support intelligence layer.

The AI layer in `src/support_intelligence/ai.py` has three local, explainable capabilities:
- ticket classification with TF-IDF and logistic regression
- recurring theme detection with transparent keyword rules
- prioritization scoring using severity, CSAT impact, resolution time, ARR exposure, churn risk, and support pressure

The project intentionally uses AI as a workflow layer for classification, summarization, and prioritization instead of building a chatbot interface.

6. Build SQL and Python analytics.

The `sql/` folder contains reusable SQL reports for ticket volume, CSAT, resolution time, churn-risk rates, ARR exposure, feature-request trends, experiment comparison, and executive KPIs.

The Python analysis script in `scripts/run_analysis.py` generates dashboard-ready output tables and static figures in `outputs/`.

7. Evaluate the AI features.

The evaluation script in `scripts/run_evaluation.py` writes:
- classification metrics
- a confusion matrix
- a summarization review sheet
- prioritization sanity checks
- a short evaluation report

The current classifier evaluation uses a noisy, account-held-out split and reports macro-F1 so performance is not judged only by the largest categories.

8. Build the dashboard.

The Streamlit app in `app/streamlit_app.py` reads generated output tables and provides five views:
- Executive Overview
- Issue Trends
- Segment Analysis
- Product Prioritization
- Experiment Analysis

The dashboard is designed as a local demo layer over the generated analytics outputs.

9. Write product and evaluation documentation.

The `docs/` folder includes the PRD, personas, user stories, tracking plan, analytics spec, experiment ideas, evaluation design, launch recommendation memo, and resume bullets.

10. Make the repository reproducible.

The main commands are:

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py
streamlit run app/streamlit_app.py
pytest -q
```

## Likely Interview Questions

### Product And Business Questions

**What problem does this project solve?**

It helps SaaS support, product, and operations teams turn noisy support tickets into structured insights. The project connects support demand with account segments, product usage, revenue exposure, churn risk, and feature-request pressure so teams can identify trends and prioritize issues more systematically.

**Why did you avoid building a chatbot?**

The core user need is not conversation; it is decision support. Support and product teams need classification, trend analysis, summaries, prioritization, and experiment comparison. A chatbot would be a weaker fit because it would hide the analytical workflow behind a conversational interface.

**Who are the target users?**

The main users are support operations managers, product managers, and customer success leads. They each need a different view of the same support signal: operational pressure, roadmap impact, and renewal risk.

**What is the strongest recommendation from the analysis?**

Performance reliability should be prioritized because performance issues have the worst CSAT and long resolution times, and dashboard latency appears as the top-ranked pain point in the prioritization table.

**How would this create business value?**

It could reduce manual support review time, improve issue triage consistency, help teams prioritize product fixes using customer and revenue impact, and make support pain visible earlier in renewal-risk discussions.

### Data And Analytics Questions

**Why did you create synthetic data instead of using a public dataset?**

Public support-ticket datasets often lack account, usage, revenue, experiment, and renewal-risk context. Synthetic data makes it possible to model a realistic SaaS analytics environment while keeping the project runnable and privacy-safe.

**How did you make the data realistic?**

The generator uses segment-specific rules, category-specific severity patterns, seasonal shocks, experiment effects, usage drops, churn-risk relationships, noisy ticket text, and repeated issue themes.

**What are the most important metrics?**

The key metrics are ticket volume, average resolution time, CSAT, escalation rate, churn-risk ticket rate, refund rate, ARR exposure, and issue priority score.

**How would you validate this with real company data?**

I would compare simulated assumptions against historical ticket distributions, build a human-labeled evaluation set, validate account-level churn and renewal-risk signals, and review prioritization output with support, product, and customer success stakeholders.

**What is one limitation of the analysis?**

The dataset is synthetic, so the outputs are useful for workflow demonstration and analytical design, but they should not be treated as production evidence.

### AI And Modeling Questions

**What AI method did you use for classification?**

The classifier uses TF-IDF features with logistic regression. This was chosen because it is local, explainable, fast to run, and appropriate for a baseline support-triage workflow.

**Why not use a large language model?**

An LLM could improve flexible summarization, but this project prioritizes local reproducibility, explainability, and low setup cost. A simple classifier also makes evaluation and failure analysis easier.

**How is prioritization calculated?**

The issue priority score combines ticket frequency, severity, CSAT impact, ARR exposure, churn risk, and feature-request pressure. The goal is to balance customer pain with business impact.

**How did you evaluate the classifier?**

The evaluation uses a noisy, account-held-out test split and reports accuracy, macro precision, macro recall, and macro-F1. Macro-F1 is important because it gives every category weight instead of over-rewarding performance on high-volume categories.

**What failure cases would you expect?**

Likely failure cases include tickets that mix multiple issues, ambiguity between bug and performance complaints, billing versus account-management confusion, and feature requests written as complaints.

### Technical Questions

**How do I run the full project?**

Run `python scripts/run_pipeline.py` to generate data, analysis outputs, and evaluation artifacts. Then run `streamlit run app/streamlit_app.py` to launch the dashboard.

**Why SQLite?**

SQLite keeps the project local, simple, and easy to inspect while still supporting SQL analysis. It is enough for a portfolio-scale analytics prototype.

**What would you improve next?**

The next improvements would be adding a small human-labeled benchmark set, improving dashboard filters, comparing the baseline classifier to embedding-based approaches, and adding root-cause grouping across related issue themes.

**How is the repository organized?**

The project separates concerns into `src/` for reusable logic, `scripts/` for runnable workflows, `sql/` for queries, `app/` for the dashboard, `docs/` for product documentation, `data/` for generated datasets, and `outputs/` for analysis artifacts.

**What tradeoff did you make intentionally?**

The project favors explainability and reproducibility over advanced infrastructure. That keeps the system easy to run locally and easier to defend in an interview.

