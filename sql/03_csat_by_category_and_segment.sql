SELECT
    t.issue_category,
    a.plan_tier,
    a.arr_band,
    a.region,
    COUNT(*) AS ticket_count,
    ROUND(AVG(t.csat_score), 2) AS avg_csat,
    ROUND(AVG(t.resolution_time_hours), 2) AS avg_resolution_time_hours
FROM tickets t
JOIN accounts a
    ON t.account_id = a.account_id
GROUP BY t.issue_category, a.plan_tier, a.arr_band, a.region
HAVING COUNT(*) >= 10
ORDER BY avg_csat ASC, ticket_count DESC;

