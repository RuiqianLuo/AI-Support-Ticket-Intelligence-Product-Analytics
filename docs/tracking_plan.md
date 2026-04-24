# Tracking Plan

## Goals

Track whether users engage with the analytics workflow, trust the outputs, and turn recommendations into action.

## Event Taxonomy

| Event | When It Fires | Key Properties | Why Track It |
|---|---|---|---|
| `dashboard_viewed` | User opens the app or a major page | `page_name`, `user_role`, `session_id` | Baseline adoption |
| `filter_applied` | User changes segment, issue, or date filters | `filter_name`, `filter_value`, `page_name` | Understand analysis behavior |
| `ticket_cluster_opened` | User opens a recurring theme or issue cluster | `theme`, `issue_category`, `segment`, `ticket_count` | Measures interest in summarized pain points |
| `prioritization_exported` | User exports or copies priority output | `export_type`, `row_count`, `page_name` | Proxy for decision-making use |
| `summary_generated` | User requests or refreshes an AI summary | `summary_scope`, `segment`, `time_window` | Measures summary feature adoption |
| `variant_compared` | User opens experiment comparison view | `variants_selected`, `metric_focus` | Indicates PM / ops experimentation use |
| `recommendation_accepted` | User accepts or bookmarks a recommendation | `recommendation_id`, `theme`, `owner_function` | Strong proxy for usefulness |
| `category_override_submitted` | Analyst changes the suggested issue category | `original_category`, `override_category`, `confidence` | Feedback loop for model improvement |
| `priority_override_submitted` | Stakeholder changes ranking or urgency | `theme`, `original_score_band`, `new_score_band` | Feedback loop for prioritization trust |

## Recommended User Properties

- `user_role`
- `team`
- `region`
- `seniority`
- `weekly_active_flag`

## Recommended Context Properties

- `page_name`
- `selected_plan_tier`
- `selected_region`
- `selected_arr_band`
- `selected_time_window`
- `selected_issue_category`

