"""
Fintech Operations Intelligence & Customer Experience Analytics Platform
--------------------------------------------------------------------------
A Streamlit web app that turns the SQL + Python analysis into an
interactive operational dashboard (the free-hostable equivalent of the
Power BI report referenced in the project write-up).

Run locally:
    streamlit run app.py
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from anomaly_detection import get_top_priority_anomalies

st.set_page_config(
    page_title="Fintech Ops Intelligence Platform",
    page_icon="💳",
    layout="wide",
)

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "..", "db", "fintech_ops.db")
TXN_CSV = os.path.join(HERE, "..", "db", "transactions.csv")
TICKETS_CSV = os.path.join(HERE, "..", "db", "support_tickets.csv")


# ---------------------------------------------------------------------------
# DATA LOADING (cached so the app stays fast on free-tier hosting)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading transaction & ticket data...")
def load_data():
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        txn = pd.read_sql("SELECT * FROM transactions", conn, parse_dates=["timestamp"])
        tickets = pd.read_sql(
            "SELECT * FROM support_tickets", conn, parse_dates=["created_at", "resolved_at"]
        )
        conn.close()
    else:
        txn = pd.read_csv(TXN_CSV, parse_dates=["timestamp"])
        tickets = pd.read_csv(TICKETS_CSV, parse_dates=["created_at", "resolved_at"])
    return txn, tickets


txn_df, tickets_df = load_data()

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------
st.sidebar.title("💳 Fintech Ops Intelligence")
st.sidebar.caption("Operations & Customer Experience Analytics Platform")

min_date, max_date = txn_df["timestamp"].min().date(), txn_df["timestamp"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

regions = st.sidebar.multiselect("Region", sorted(txn_df["region"].unique()), default=list(txn_df["region"].unique()))
gateways = st.sidebar.multiselect("Gateway", sorted(txn_df["gateway"].unique()), default=list(txn_df["gateway"].unique()))

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

mask = (
    (txn_df["timestamp"].dt.date >= start_date)
    & (txn_df["timestamp"].dt.date <= end_date)
    & (txn_df["region"].isin(regions))
    & (txn_df["gateway"].isin(gateways))
)
ftxn = txn_df[mask]

tmask = (
    (tickets_df["created_at"].dt.date >= start_date)
    & (tickets_df["created_at"].dt.date <= end_date)
    & (tickets_df["region"].isin(regions))
)
ftickets = tickets_df[tmask]

st.sidebar.markdown("---")
st.sidebar.metric("Transactions in view", f"{len(ftxn):,}")
st.sidebar.metric("Tickets in view", f"{len(ftickets):,}")
st.sidebar.markdown("---")
st.sidebar.caption("Built with Python, SQL (SQLite) & Streamlit · Simulated data for portfolio demonstration")

# ---------------------------------------------------------------------------
# HEADER + TOP KPIs
# ---------------------------------------------------------------------------
st.title("Fintech Operations Intelligence & Customer Experience Analytics Platform")
st.caption(
    "Monitoring SLA adherence, ticket resolution efficiency, transaction success rates, "
    "and operational throughput across a simulated high-volume transaction environment."
)

total_txns = len(ftxn)
success_rate = 100 * (ftxn["status"] == "Success").mean() if total_txns else 0
failure_rate = 100 * (ftxn["status"] == "Failed").mean() if total_txns else 0
avg_proc_time = ftxn["processing_time_ms"].mean() if total_txns else 0

total_tickets = len(ftickets)
sla_breach_rate = 100 * ftickets["sla_breached"].mean() if total_tickets else 0
avg_resolution = ftickets["resolution_time_hours"].mean() if total_tickets else 0
avg_csat = ftickets["csat_score"].mean() if total_tickets else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Transaction Success Rate", f"{success_rate:.1f}%")
k2.metric("Transaction Failure Rate", f"{failure_rate:.1f}%", delta=f"{failure_rate:.1f}%", delta_color="inverse")
k3.metric("Avg Processing Time", f"{avg_proc_time:,.0f} ms")
k4.metric("SLA Breach Rate", f"{sla_breach_rate:.1f}%", delta=f"{sla_breach_rate:.1f}%", delta_color="inverse")
k5.metric("Avg Resolution Time", f"{avg_resolution:.1f} hrs")
k6.metric("Avg CSAT (1-5)", f"{avg_csat:.2f}")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Operations Overview", "🛟 SLA & Support Efficiency", "🚨 Anomaly Detection", "🔎 Raw Data Explorer"]
)

# ---------------------------------------------------------------------------
# TAB 1 — OPERATIONS OVERVIEW
# ---------------------------------------------------------------------------
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Daily Transaction Throughput & Failure Trend")
        daily = ftxn.groupby(ftxn["timestamp"].dt.date).agg(
            total=("transaction_id", "count"),
            failed=("status", lambda s: (s == "Failed").sum()),
        ).reset_index().rename(columns={"timestamp": "date"})
        daily["failure_rate_pct"] = 100 * daily["failed"] / daily["total"]
        fig = go.Figure()
        fig.add_bar(x=daily["timestamp"], y=daily["total"], name="Total Transactions", yaxis="y1", opacity=0.6)
        fig.add_trace(go.Scatter(x=daily["timestamp"], y=daily["failure_rate_pct"], name="Failure Rate %",
                                  yaxis="y2", line=dict(color="crimson")))
        fig.update_layout(
            yaxis=dict(title="Transactions"),
            yaxis2=dict(title="Failure Rate %", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.1), height=400, margin=dict(t=30),
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Success Rate & Avg Processing Time by Gateway")
        gw = ftxn.groupby("gateway").agg(
            total=("transaction_id", "count"),
            success_rate=("status", lambda s: 100 * (s == "Success").mean()),
            avg_proc=("processing_time_ms", "mean"),
        ).reset_index()
        fig2 = px.bar(gw, x="gateway", y="success_rate", color="avg_proc",
                      color_continuous_scale="RdYlGn_r", text=gw["success_rate"].round(1),
                      labels={"success_rate": "Success Rate %", "avg_proc": "Avg Proc. Time (ms)"})
        fig2.update_layout(height=400, margin=dict(t=30))
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Top Failure Reasons")
        fr = ftxn[ftxn["status"] == "Failed"]["failure_reason"].value_counts().reset_index()
        fr.columns = ["failure_reason", "count"]
        fig3 = px.bar(fr.head(10), x="count", y="failure_reason", orientation="h")
        fig3.update_layout(height=380, margin=dict(t=20), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.subheader("Regional Operational Health")
        reg = ftxn.groupby("region").agg(
            total=("transaction_id", "count"),
            success_rate=("status", lambda s: 100 * (s == "Success").mean()),
            fraud_flagged=("is_fraud_flag", "sum"),
        ).reset_index()
        fig4 = px.scatter(reg, x="success_rate", y="fraud_flagged", size="total", color="region",
                           labels={"success_rate": "Success Rate %", "fraud_flagged": "Fraud-Flagged Txns"})
        fig4.update_layout(height=380, margin=dict(t=20))
        st.plotly_chart(fig4, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 2 — SLA & SUPPORT EFFICIENCY
# ---------------------------------------------------------------------------
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("SLA Breach Rate by Priority & Team")
        sla = ftickets.groupby(["priority", "agent_team"]).agg(
            total=("ticket_id", "count"),
            breach_rate=("sla_breached", lambda s: 100 * s.mean()),
        ).reset_index()
        fig = px.density_heatmap(sla, x="agent_team", y="priority", z="breach_rate",
                                  color_continuous_scale="Reds", text_auto=".1f")
        fig.update_layout(height=420, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Resolution Time Distribution by Team")
        fig2 = px.box(ftickets, x="agent_team", y="resolution_time_hours", color="agent_team", points=False)
        fig2.update_layout(height=420, margin=dict(t=20), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("CSAT vs SLA Outcome")
        csat_sla = ftickets.groupby("sla_breached")["csat_score"].mean().reset_index()
        csat_sla["sla_breached"] = csat_sla["sla_breached"].map({0: "SLA Met", 1: "SLA Breached"})
        fig3 = px.bar(csat_sla, x="sla_breached", y="csat_score", color="sla_breached",
                       color_discrete_map={"SLA Met": "#2ecc71", "SLA Breached": "#e74c3c"})
        fig3.update_layout(height=380, margin=dict(t=20))
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.subheader("Bottleneck Agents (lowest efficiency, n≥20 tickets)")
        agents = ftickets.groupby(["agent_id", "agent_team"]).agg(
            tickets=("ticket_id", "count"),
            avg_resolution=("resolution_time_hours", "mean"),
            breaches=("sla_breached", "sum"),
        ).reset_index()
        agents = agents[agents["tickets"] >= 20].sort_values("avg_resolution", ascending=False).head(10)
        st.dataframe(agents, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# TAB 3 — ANOMALY DETECTION
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Automated Anomaly Detection & Prioritization")
    st.caption(
        "Uses an IsolationForest model across processing time, amount, retry count, and risk score "
        "to flag operationally significant transactions, then ranks them by a composite priority score."
    )
    contamination = st.slider("Sensitivity (expected anomaly %)", 0.5, 5.0, 2.0, step=0.5) / 100
    top_n = st.slider("Number of top anomalies to show", 5, 50, 20, step=5)

    with st.spinner("Running anomaly detection model..."):
        sample_df = ftxn.sample(min(len(ftxn), 20000), random_state=1) if len(ftxn) > 20000 else ftxn
        anomalies = get_top_priority_anomalies(sample_df, top_n=top_n, contamination=contamination)

    st.dataframe(anomalies, use_container_width=True, hide_index=True)

    if not anomalies.empty:
        fig = px.scatter(
            anomalies, x="processing_time_ms", y="amount", size="priority_score",
            color="anomaly_reason", hover_data=["transaction_id", "gateway"],
            title="Flagged Anomalies — Processing Time vs Amount",
        )
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 4 — RAW DATA EXPLORER
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Transactions")
    st.dataframe(ftxn.head(1000), use_container_width=True, hide_index=True)
    st.download_button("Download filtered transactions (CSV)", ftxn.to_csv(index=False), "transactions_filtered.csv")

    st.subheader("Support Tickets")
    st.dataframe(ftickets.head(1000), use_container_width=True, hide_index=True)
    st.download_button("Download filtered tickets (CSV)", ftickets.to_csv(index=False), "tickets_filtered.csv")
