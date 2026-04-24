SELECT
    issue_category,
    COUNT(*) AS ticket_count,
    ROUND(AVG(csat_score), 2) AS avg_csat,
    ROUND(AVG(resolution_time_hours), 2) AS avg_resolution_time_hours
FROM tickets
GROUP BY issue_category
ORDER BY ticket_count DESC;

