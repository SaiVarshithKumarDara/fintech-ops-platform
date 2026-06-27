# Fintech Operations Intelligence & Customer Experience Analytics Platform

A simulated fintech operations platform that analyzes **120,000+ transactions**
and **32,000+ support tickets** to surface SLA risks, transaction failure
trends, and operational bottlenecks — with automated anomaly detection and
an interactive live dashboard.

**Live demo:** *(add your Streamlit Cloud URL here after deploying)*

---

## What's inside

```
fintech-ops-platform/
├── data/
│   └── generate_data.py         # Synthetic data generator (120K txns, 32K tickets)
├── db/
│   ├── build_database.py        # Loads CSVs into a SQLite database
│   ├── analysis_queries.sql     # 9 core SQL analyses (SLA, failures, anomalies, etc.)
│   ├── transactions.csv         # Generated dataset (18 columns)
│   ├── support_tickets.csv      # Generated dataset (18 columns)
│   └── fintech_ops.db           # SQLite DB built from the CSVs
├── app/
│   ├── app.py                   # Streamlit dashboard (the "Power BI" replacement, free to host)
│   └── anomaly_detection.py     # IsolationForest + z-score anomaly/priority scoring
├── requirements.txt
└── README.md
```

## Datasets

**`transactions.csv`** (120,000 rows × 18 columns)
`transaction_id, timestamp, customer_id, channel, transaction_type, amount, currency, status, failure_reason, processing_time_ms, gateway, region, device_type, retry_count, is_fraud_flag, merchant_category, account_age_days, risk_score`

**`support_tickets.csv`** (32,000 rows × 18 columns)
`ticket_id, created_at, resolved_at, customer_id, related_transaction_id, issue_category, priority, channel, region, sla_target_hours, resolution_time_hours, sla_breached, agent_id, agent_team, csat_score, status, escalation_flag, reopened_count`

The data is intentionally messy/realistic: a simulated gateway (`GatewayC`)
has clustered timeouts, certain agent teams (`Fraud-Risk`, `Tier2-Technical`)
run slower with more SLA breaches, and CSAT correlates with SLA outcome —
giving the SQL/Python/dashboard logic real patterns to surface.


## Run locally

```bash
git clone <your-repo-url>
cd fintech-ops-platform
pip install -r requirements.txt

# 1. Generate the data (or use the CSVs already in db/)
python data/generate_data.py

# 2. Build the SQLite database
python db/build_database.py

# 3. Launch the dashboard
streamlit run app/app.py
```
