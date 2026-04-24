SELECT
    issue_category,
    severity,
    ROUND(AVG(resolution_time_hours), 2) AS avg_resolution_time_hours,
    ROUND(AVG(escalated_flag), 3) AS escalation_rate
FROM tickets
GROUP BY issue_category, severity
ORDER BY avg_resolution_time_hours DESC;

