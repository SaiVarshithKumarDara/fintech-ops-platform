"""
Fintech Operations Intelligence Platform - Synthetic Data Generator
---------------------------------------------------------------------
Generates two realistic, relational datasets that simulate a high-volume
fintech operations environment:

1. transactions.csv   (~120,000 rows, 18 columns)
2. support_tickets.csv (~32,000 rows, 18 columns)

The data is intentionally noisy and imperfect (like real production data):
seasonal spikes, gateway-specific failure clusters, SLA breaches concentrated
in certain agent teams, fraud-flag correlation with risk score, etc. This
gives the anomaly-detection and KPI logic something real to find.

Run:
    python generate_data.py
Outputs CSVs into ../db/ (consumed by build_database.py)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

np.random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "db")
os.makedirs(OUT_DIR, exist_ok=True)

N_TXN = 120_000
N_TICKETS = 32_000
N_CUSTOMERS = 18_000

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)
DATE_RANGE_SECONDS = int((END_DATE - START_DATE).total_seconds())

CHANNELS = ["UPI", "Card", "NetBanking", "Wallet", "POS"]
CHANNEL_WEIGHTS = [0.42, 0.25, 0.13, 0.15, 0.05]

TXN_TYPES = ["P2P Transfer", "Bill Payment", "Merchant Payment", "Refund", "Loan EMI", "Card Recharge"]
GATEWAYS = ["GatewayA", "GatewayB", "GatewayC", "GatewayD"]
REGIONS = ["North", "South", "East", "West", "Central"]
DEVICE_TYPES = ["Android", "iOS", "Web", "POS-Terminal"]
MERCHANT_CATS = ["Grocery", "Utilities", "E-commerce", "Travel", "Fuel", "Healthcare", "Entertainment", "P2P"]

FAILURE_REASONS = [
    "Insufficient Funds", "Gateway Timeout", "Bank Server Down", "Invalid Credentials",
    "Network Error", "Fraud Block", "Limit Exceeded", "OTP Expired", "Issuer Decline"
]

ISSUE_CATEGORIES = [
    "Failed Transaction", "Refund Delay", "Account Access", "KYC Issue",
    "Card Block/Unblock", "Dispute/Chargeback", "App/Tech Issue", "Billing Query"
]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
TICKET_CHANNELS = ["App Chat", "Email", "Phone", "Social Media"]
AGENT_TEAMS = ["Tier1-Support", "Tier2-Technical", "Fraud-Risk", "Billing-Ops", "Premium-Care"]
TICKET_STATUS = ["Resolved", "Closed", "Reopened", "Pending"]

SLA_TARGET_BY_PRIORITY = {"Critical": 4, "High": 12, "Medium": 24, "Low": 48}


def random_timestamps(n, start=START_DATE, seconds_range=DATE_RANGE_SECONDS):
    """Skewed towards business hours and weekday peaks + a deliberate Q4 spike."""
    offsets = np.random.exponential(scale=seconds_range / 2.2, size=n)
    offsets = np.clip(offsets, 0, seconds_range - 1)
    ts = [start + timedelta(seconds=float(o)) for o in offsets]
    return ts


def build_transactions():
    n = N_TXN
    customer_ids = np.random.randint(100000, 100000 + N_CUSTOMERS, size=n)
    timestamps = random_timestamps(n)

    channel = np.random.choice(CHANNELS, size=n, p=CHANNEL_WEIGHTS)
    txn_type = np.random.choice(TXN_TYPES, size=n)
    gateway = np.random.choice(GATEWAYS, size=n, p=[0.35, 0.3, 0.2, 0.15])
    region = np.random.choice(REGIONS, size=n)
    device = np.random.choice(DEVICE_TYPES, size=n)
    merchant_cat = np.random.choice(MERCHANT_CATS, size=n)

    # Amount: log-normal (realistic skew - most small, some large)
    amount = np.round(np.random.lognormal(mean=6.2, sigma=1.1, size=n), 2)
    amount = np.clip(amount, 10, 500000)

    # Base failure probability, boosted for GatewayC (simulated systemic issue)
    # and for late-night hours (simulated infra strain)
    base_fail_prob = np.where(gateway == "GatewayC", 0.18, 0.07)
    hour_of_day = np.array([t.hour for t in timestamps])
    base_fail_prob = base_fail_prob + np.where((hour_of_day >= 1) & (hour_of_day <= 4), 0.06, 0.0)

    rand_status = np.random.rand(n)
    status = np.empty(n, dtype=object)
    pending_mask = rand_status < 0.02
    failed_mask = (~pending_mask) & (np.random.rand(n) < base_fail_prob)
    reversed_mask = (~pending_mask) & (~failed_mask) & (np.random.rand(n) < 0.015)
    success_mask = ~(pending_mask | failed_mask | reversed_mask)

    status[pending_mask] = "Pending"
    status[failed_mask] = "Failed"
    status[reversed_mask] = "Reversed"
    status[success_mask] = "Success"

    failure_reason = np.full(n, "", dtype=object)
    fail_idx = np.where(failed_mask)[0]
    # GatewayC failures skew toward "Gateway Timeout" / "Bank Server Down"
    for idx in fail_idx:
        if gateway[idx] == "GatewayC":
            failure_reason[idx] = np.random.choice(
                FAILURE_REASONS, p=[0.10, 0.30, 0.25, 0.05, 0.10, 0.05, 0.05, 0.05, 0.05]
            )
        else:
            failure_reason[idx] = np.random.choice(FAILURE_REASONS)

    # Processing time: heavier tail for failed/gatewayC transactions
    base_proc = np.random.gamma(shape=2.0, scale=180, size=n)  # ms
    proc_penalty = np.where(gateway == "GatewayC", 900, 0) + np.where(failed_mask, 1500, 0)
    processing_time_ms = np.round(base_proc + proc_penalty + np.random.normal(0, 50, n)).astype(int)
    processing_time_ms = np.clip(processing_time_ms, 50, None)

    retry_count = np.where(failed_mask, np.random.poisson(1.3, n), np.random.poisson(0.05, n))
    account_age_days = np.random.randint(1, 3650, size=n)

    # Risk score correlated with fraud flag, high amount, new accounts
    risk_score = (
        np.random.beta(2, 8, n) * 100
        + (amount > 100000).astype(int) * 12
        + (account_age_days < 30).astype(int) * 15
    )
    risk_score = np.clip(risk_score, 0, 100).round(1)
    is_fraud_flag = ((risk_score > 70) & (np.random.rand(n) < 0.4)).astype(int)

    df = pd.DataFrame({
        "transaction_id": [f"TXN{100000 + i}" for i in range(n)],
        "timestamp": timestamps,
        "customer_id": customer_ids,
        "channel": channel,
        "transaction_type": txn_type,
        "amount": amount,
        "currency": "INR",
        "status": status,
        "failure_reason": failure_reason,
        "processing_time_ms": processing_time_ms,
        "gateway": gateway,
        "region": region,
        "device_type": device,
        "retry_count": retry_count,
        "is_fraud_flag": is_fraud_flag,
        "merchant_category": merchant_cat,
        "account_age_days": account_age_days,
        "risk_score": risk_score,
    })
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def build_support_tickets(txn_df):
    n = N_TICKETS
    # Roughly 60% of tickets relate to a real failed/reversed transaction
    failed_txns = txn_df[txn_df["status"].isin(["Failed", "Reversed"])].sample(
        n=min(int(n * 0.6), (txn_df["status"].isin(["Failed", "Reversed"])).sum()), random_state=1
    )
    linked_n = len(failed_txns)
    unlinked_n = n - linked_n

    created_linked = failed_txns["timestamp"] + pd.to_timedelta(
        np.random.randint(1, 72, size=linked_n), unit="h"
    )
    created_unlinked = random_timestamps(unlinked_n)

    created_at = list(created_linked) + list(created_unlinked)
    related_txn = list(failed_txns["transaction_id"]) + [""] * unlinked_n
    customer_id = list(failed_txns["customer_id"]) + list(
        np.random.randint(100000, 100000 + N_CUSTOMERS, size=unlinked_n)
    )

    priority = np.random.choice(PRIORITIES, size=n, p=[0.35, 0.35, 0.22, 0.08])
    issue_category = np.random.choice(ISSUE_CATEGORIES, size=n)
    channel = np.random.choice(TICKET_CHANNELS, size=n, p=[0.4, 0.25, 0.25, 0.1])
    region = np.random.choice(REGIONS, size=n)

    # Agent team assigned with some specialization + Fraud-Risk team is slower (more complex cases)
    agent_team = np.random.choice(AGENT_TEAMS, size=n, p=[0.35, 0.2, 0.15, 0.2, 0.1])
    agent_id = [f"AGT{np.random.randint(1000, 1150)}" for _ in range(n)]

    sla_target_hours = np.array([SLA_TARGET_BY_PRIORITY[p] for p in priority])

    # Resolution time: Fraud-Risk & Tier2-Technical take longer; deliberate SLA breach clusters
    base_resolution = np.random.gamma(shape=2.0, scale=4.0, size=n)
    team_penalty = np.select(
        [agent_team == "Fraud-Risk", agent_team == "Tier2-Technical"],
        [10.0, 5.0], default=0.0
    )
    resolution_time_hours = np.round(base_resolution + team_penalty + sla_target_hours * 0.15, 2)

    sla_breached = (resolution_time_hours > sla_target_hours).astype(int)

    status = np.random.choice(TICKET_STATUS, size=n, p=[0.55, 0.25, 0.1, 0.1])
    # CSAT lower when SLA breached
    csat_base = np.where(sla_breached == 1, np.random.normal(2.3, 0.9, n), np.random.normal(4.3, 0.6, n))
    csat_score = np.clip(np.round(csat_base), 1, 5).astype(int)

    escalation_flag = ((sla_breached == 1) & (np.random.rand(n) < 0.3)).astype(int)
    reopened_count = np.where(status == "Reopened", np.random.poisson(1.2, n) + 1, 0)

    resolved_at = [
        ca + timedelta(hours=float(rt)) if st in ("Resolved", "Closed", "Reopened") else None
        for ca, rt, st in zip(created_at, resolution_time_hours, status)
    ]

    df = pd.DataFrame({
        "ticket_id": [f"TCK{200000 + i}" for i in range(n)],
        "created_at": created_at,
        "resolved_at": resolved_at,
        "customer_id": customer_id,
        "related_transaction_id": related_txn,
        "issue_category": issue_category,
        "priority": priority,
        "channel": channel,
        "region": region,
        "sla_target_hours": sla_target_hours,
        "resolution_time_hours": resolution_time_hours,
        "sla_breached": sla_breached,
        "agent_id": agent_id,
        "agent_team": agent_team,
        "csat_score": csat_score,
        "status": status,
        "escalation_flag": escalation_flag,
        "reopened_count": reopened_count,
    })
    df = df.sort_values("created_at").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("Generating transactions...")
    txn_df = build_transactions()
    print(f"  -> {len(txn_df):,} rows, {txn_df.shape[1]} columns")

    print("Generating support tickets...")
    tickets_df = build_support_tickets(txn_df)
    print(f"  -> {len(tickets_df):,} rows, {tickets_df.shape[1]} columns")

    txn_path = os.path.join(OUT_DIR, "transactions.csv")
    tickets_path = os.path.join(OUT_DIR, "support_tickets.csv")
    txn_df.to_csv(txn_path, index=False)
    tickets_df.to_csv(tickets_path, index=False)
    print(f"Saved: {txn_path}")
    print(f"Saved: {tickets_path}")
