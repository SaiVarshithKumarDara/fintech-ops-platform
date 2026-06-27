-- ============================================================================
-- Fintech Operations Intelligence Platform — Core SQL Analysis Queries
-- Engine: SQLite (also valid, with minor syntax tweaks, on PostgreSQL/MySQL)
-- These queries power the KPIs shown in the Streamlit dashboard / Power BI.
-- ============================================================================

-- 1. TRANSACTION SUCCESS RATE & FAILURE BREAKDOWN BY GATEWAY
-- Surfaces systemic gateway issues (e.g., GatewayC failure clustering)
SELECT
    gateway,
    COUNT(*)                                            AS total_txns,
    SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) AS successful,
    SUM(CASE WHEN status = 'Failed'  THEN 1 ELSE 0 END) AS failed,
    ROUND(100.0 * SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2)  AS failure_rate_pct,
    ROUND(AVG(processing_time_ms), 1)                   AS avg_processing_time_ms
FROM transactions
GROUP BY gateway
ORDER BY failure_rate_pct DESC;


-- 2. TOP FAILURE REASONS DRIVING OPERATIONAL ISSUES
SELECT
    failure_reason,
    COUNT(*) AS occurrences,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM transactions WHERE status = 'Failed'), 2) AS pct_of_all_failures
FROM transactions
WHERE status = 'Failed' AND failure_reason != ''
GROUP BY failure_reason
ORDER BY occurrences DESC;


-- 3. DAILY OPERATIONAL THROUGHPUT & FAILURE TREND (time series for dashboard)
SELECT
    DATE(timestamp)                                       AS txn_date,
    COUNT(*)                                              AS total_txns,
    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END)    AS failed_txns,
    ROUND(100.0 * SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
    ROUND(AVG(amount), 2)                                 AS avg_txn_amount
FROM transactions
GROUP BY DATE(timestamp)
ORDER BY txn_date;


-- 4. SLA ADHERENCE BY PRIORITY AND AGENT TEAM (core KPI)
SELECT
    priority,
    agent_team,
    COUNT(*)                                                AS total_tickets,
    SUM(sla_breached)                                       AS breached_tickets,
    ROUND(100.0 * SUM(sla_breached) / COUNT(*), 2)          AS sla_breach_rate_pct,
    ROUND(AVG(resolution_time_hours), 2)                    AS avg_resolution_hours,
    ROUND(AVG(csat_score), 2)                               AS avg_csat
FROM support_tickets
GROUP BY priority, agent_team
ORDER BY sla_breach_rate_pct DESC;


-- 5. TICKET RESOLUTION EFFICIENCY BY AGENT (identifies bottleneck agents)
SELECT
    agent_id,
    agent_team,
    COUNT(*)                                       AS tickets_handled,
    ROUND(AVG(resolution_time_hours), 2)           AS avg_resolution_hours,
    SUM(sla_breached)                              AS sla_breaches,
    SUM(escalation_flag)                           AS escalations,
    ROUND(AVG(csat_score), 2)                      AS avg_csat
FROM support_tickets
GROUP BY agent_id, agent_team
HAVING COUNT(*) >= 20
ORDER BY avg_resolution_hours DESC
LIMIT 20;


-- 6. HIGH-IMPACT CUSTOMER EXPERIENCE ISSUES: tickets linked to failed transactions
-- (Quantifies how much support load is actually caused by transaction failures)
SELECT
    t.failure_reason,
    COUNT(DISTINCT s.ticket_id)         AS tickets_generated,
    ROUND(AVG(s.resolution_time_hours), 2) AS avg_resolution_hours,
    ROUND(AVG(s.csat_score), 2)            AS avg_csat
FROM support_tickets s
JOIN transactions t ON s.related_transaction_id = t.transaction_id
WHERE s.related_transaction_id != ''
GROUP BY t.failure_reason
ORDER BY tickets_generated DESC;


-- 7. SLA RISK FLAG — OPEN TICKETS APPROACHING / EXCEEDING SLA (operational alerting)
SELECT
    ticket_id,
    priority,
    agent_team,
    created_at,
    sla_target_hours,
    ROUND((JULIANDAY('now') - JULIANDAY(created_at)) * 24, 2) AS hours_open,
    CASE
        WHEN (JULIANDAY('now') - JULIANDAY(created_at)) * 24 > sla_target_hours THEN 'BREACHED'
        WHEN (JULIANDAY('now') - JULIANDAY(created_at)) * 24 > 0.8 * sla_target_hours THEN 'AT RISK'
        ELSE 'ON TRACK'
    END AS sla_risk_status
FROM support_tickets
WHERE status = 'Pending'
ORDER BY hours_open DESC;


-- 8. ANOMALY CANDIDATE QUERY — transactions with statistically unusual processing time
-- (z-score style outlier flag, complements the Python IsolationForest model in anomaly_detection.py)
WITH stats AS (
    SELECT AVG(processing_time_ms) AS mean_pt, AVG(processing_time_ms * processing_time_ms) - AVG(processing_time_ms) * AVG(processing_time_ms) AS variance_pt
    FROM transactions
)
SELECT
    t.transaction_id,
    t.gateway,
    t.processing_time_ms,
    ROUND((t.processing_time_ms - s.mean_pt) / SQRT(s.variance_pt), 2) AS z_score
FROM transactions t, stats s
WHERE ABS((t.processing_time_ms - s.mean_pt) / SQRT(s.variance_pt)) > 3
ORDER BY z_score DESC
LIMIT 100;


-- 9. REGIONAL OPERATIONAL HEALTH SUMMARY (for executive KPI rollup)
SELECT
    region,
    COUNT(*)                                                              AS total_txns,
    ROUND(100.0 * SUM(CASE WHEN status='Success' THEN 1 ELSE 0 END)/COUNT(*), 2) AS success_rate_pct,
    SUM(is_fraud_flag)                                                    AS fraud_flagged_txns
FROM transactions
GROUP BY region
ORDER BY success_rate_pct ASC;
