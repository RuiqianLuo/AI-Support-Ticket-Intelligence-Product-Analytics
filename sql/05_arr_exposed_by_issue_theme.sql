WITH affected_accounts AS (
    SELECT DISTINCT
        t.ai_predicted_category,
        t.ai_detected_theme,
        t.account_id,
        CASE
            WHEN a.arr_band = '<25k' THEN 12000
            WHEN a.arr_band = '25k-75k' THEN 50000
            WHEN a.arr_band = '75k-250k' THEN 150000
            ELSE 340000
        END AS approx_arr
    FROM tickets t
    JOIN accounts a
        ON t.account_id = a.account_id
),
ticket_summary AS (
    SELECT
        ai_predicted_category,
        ai_detected_theme,
        COUNT(*) AS ticket_count,
        ROUND(AVG(csat_score), 2) AS avg_csat
    FROM tickets
    GROUP BY ai_predicted_category, ai_detected_theme
)
SELECT
    aa.ai_predicted_category,
    aa.ai_detected_theme,
    COUNT(*) AS affected_accounts,
    ROUND(SUM(aa.approx_arr), 2) AS approx_arr_exposed,
    ts.ticket_count,
    ts.avg_csat
FROM affected_accounts aa
JOIN ticket_summary ts
    ON aa.ai_predicted_category = ts.ai_predicted_category
   AND aa.ai_detected_theme = ts.ai_detected_theme
GROUP BY aa.ai_predicted_category, aa.ai_detected_theme, ts.ticket_count, ts.avg_csat
ORDER BY approx_arr_exposed DESC, ts.ticket_count DESC;
