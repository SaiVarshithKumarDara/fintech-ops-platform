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

## How the resume bullets map to the code

| Resume bullet | Where it lives |
|---|---|
| SQL analysis of failures, SLA risk, bottlenecks | `db/analysis_queries.sql` (9 queries) |
| KPI dashboards: SLA adherence, resolution efficiency, success rate, throughput | `app/app.py` Tabs 1–2 |
| Automated anomaly detection & prioritization | `app/anomaly_detection.py` (IsolationForest + composite priority score), Tab 3 |
| Scalable reporting pipelines (SQL + Python + dashboard automation) | `db/build_database.py` → SQLite → `app.py` reads via cached SQL queries |
| 100K+ simulated transaction/support records | `data/generate_data.py` (120K + 32K rows) |

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

---

## Hosting it for free (so you can link it from your portfolio)

### Option A — Streamlit Community Cloud (recommended, easiest)

1. Push this whole folder to a **public GitHub repo**.
2. Go to **https://share.streamlit.io** → sign in with GitHub.
3. Click **"New app"** → select your repo → set:
   - **Main file path:** `app/app.py`
   - Branch: `main`
4. Click **Deploy**. Streamlit Cloud installs `requirements.txt` automatically.
5. You'll get a free URL like `https://your-app-name.streamlit.app` — link this directly from your portfolio.
6. Any push to `main` auto-redeploys.

> Free tier limits: 1 GB RAM, app sleeps after inactivity but wakes on visit — fine for a portfolio demo.

### Option B — Render (free web service)

1. Push to GitHub.
2. On **https://render.com** → New → Web Service → connect your repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run app/app.py --server.port $PORT --server.address 0.0.0.0`
5. Choose the **Free** instance type and deploy.

### Option C — Hugging Face Spaces (free, supports Streamlit natively)

1. Create a new Space at **https://huggingface.co/spaces** → SDK: **Streamlit**.
2. Upload the repo files (or connect via git).
3. Make sure `app/app.py` is referenced as the entry point (or move it to the repo root — Spaces expects `app.py` at root by default, so for Spaces specifically, copy `app/app.py`, `app/anomaly_detection.py`, and the `db/` folder to the repo root).
4. The Space builds and gives you a free public URL.

### About the Power BI piece

Power BI Desktop (`.pbix`) files can't be hosted on a free public URL the
way Streamlit can — Power BI's free "Publish to Web" tier requires a
Microsoft work/school account and is meant for org-internal sharing, not a
public portfolio. The recommended approach:

1. Build the KPI report in **Power BI Desktop** using `transactions.csv` and
   `support_tickets.csv` (mirroring the dashboard tabs above: SLA adherence,
   resolution efficiency, success rate, throughput).
2. Export 2–3 high-quality **screenshots** of the report.
3. On your portfolio page, show those screenshots as the "Power BI" artifact
   and link the **live Streamlit app** as the interactive, hostable version
   of the same analytics — this gives you both deliverables described in the
   resume bullet without needing paid Power BI hosting.

---

## Suggested portfolio write-up snippet

> An end-to-end fintech operations analytics platform built with Python,
> SQL, and Streamlit, simulating 150K+ transaction and support records to
> surface SLA risks, transaction failure trends, and operational
> bottlenecks. Includes an automated anomaly detection workflow
> (IsolationForest + statistical scoring) that prioritizes high-impact
> issues, and an interactive live dashboard tracking SLA adherence, ticket
> resolution efficiency, and transaction success rates in real time.
