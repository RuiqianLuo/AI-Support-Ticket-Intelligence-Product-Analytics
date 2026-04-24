SELECT
    a.plan_tier,
    COUNT(*) AS total_tickets,
    SUM(t.churn_risk_flag) AS churn_risk_tickets,
    ROUND(1.0 * SUM(t.churn_risk_flag) / COUNT(*), 4) AS churn_risk_ticket_rate,
    ROUND(AVG(t.csat_score), 2) AS avg_csat
FROM tickets t
JOIN accounts a
    ON t.account_id = a.account_id
GROUP BY a.plan_tier
ORDER BY churn_risk_ticket_rate DESC;

