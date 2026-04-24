SELECT
    experiment_variant,
    COUNT(*) AS ticket_count,
    ROUND(AVG(resolution_time_hours), 2) AS avg_resolution_time_hours,
    ROUND(AVG(csat_score), 2) AS avg_csat,
    ROUND(AVG(escalated_flag), 4) AS escalation_rate,
    ROUND(AVG(churn_risk_flag), 4) AS churn_risk_ticket_rate
FROM tickets
GROUP BY experiment_variant
ORDER BY avg_csat DESC;

