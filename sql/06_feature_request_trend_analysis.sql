SELECT
    substr(created_at, 1, 7) AS request_month,
    request_theme,
    COUNT(*) AS request_count,
    SUM(votes) AS total_votes,
    ROUND(SUM(estimated_revenue_impact), 2) AS estimated_revenue_impact
FROM feature_requests
GROUP BY substr(created_at, 1, 7), request_theme
ORDER BY request_month, request_count DESC;

