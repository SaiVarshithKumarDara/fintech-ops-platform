"""
Automated Anomaly Detection & Prioritization Workflow
-------------------------------------------------------
Implements two complementary detection methods, as referenced in the
resume bullet "automated anomaly detection and prioritization workflows":

1. Statistical method -> Z-score / IQR based outlier flags (fast, explainable)
2. ML method           -> IsolationForest (catches multivariate anomalies
                          a single-column z-score would miss)

A composite "priority_score" ranks anomalies so an operations analyst can
triage the highest-impact issues first, instead of scanning raw logs.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


def zscore_flags(df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.Series:
    """Return boolean Series flagging statistical outliers in `column`."""
    mean, std = df[column].mean(), df[column].std()
    if std == 0 or np.isnan(std):
        return pd.Series(False, index=df.index)
    z = (df[column] - mean) / std
    return z.abs() > threshold


def detect_transaction_anomalies(txn_df: pd.DataFrame, contamination: float = 0.02) -> pd.DataFrame:
    """
    Flags anomalous transactions using IsolationForest across multiple
    operational signals: processing_time_ms, amount, retry_count, risk_score.
    Returns the input df with extra columns: anomaly_score, is_anomaly,
    anomaly_reason, priority_score.
    """
    features = ["processing_time_ms", "amount", "retry_count", "risk_score"]
    work = txn_df.copy()
    X = work[features].fillna(0)

    model = IsolationForest(
        n_estimators=150, contamination=contamination, random_state=42
    )
    model.fit(X)
    # decision_function: lower = more anomalous. Invert so higher = more anomalous.
    work["anomaly_score"] = -model.decision_function(X)
    work["is_anomaly"] = model.predict(X) == -1

    # Explainability: tag *why* a row was flagged using simple z-score checks
    reasons = []
    pt_flag = zscore_flags(work, "processing_time_ms", 2.5)
    amt_flag = zscore_flags(work, "amount", 2.5)
    retry_flag = work["retry_count"] >= 3
    risk_flag = work["risk_score"] > 75

    for i in work.index:
        tags = []
        if pt_flag.loc[i]:
            tags.append("Slow processing")
        if amt_flag.loc[i]:
            tags.append("Unusual amount")
        if retry_flag.loc[i]:
            tags.append("High retries")
        if risk_flag.loc[i]:
            tags.append("High risk score")
        if work.loc[i, "status"] == "Failed":
            tags.append("Failed txn")
        reasons.append(", ".join(tags) if tags else "Multivariate pattern")
    work["anomaly_reason"] = reasons

    # Priority score: blend anomaly strength with business impact (amount, fraud flag)
    norm_score = (work["anomaly_score"] - work["anomaly_score"].min()) / (
        work["anomaly_score"].max() - work["anomaly_score"].min() + 1e-9
    )
    norm_amount = (work["amount"] - work["amount"].min()) / (
        work["amount"].max() - work["amount"].min() + 1e-9
    )
    work["priority_score"] = np.round(
        (0.55 * norm_score + 0.30 * norm_amount + 0.15 * work["is_fraud_flag"]) * 100, 2
    )

    return work


def get_top_priority_anomalies(txn_df: pd.DataFrame, top_n: int = 25, contamination: float = 0.02) -> pd.DataFrame:
    scored = detect_transaction_anomalies(txn_df, contamination=contamination)
    anomalies = scored[scored["is_anomaly"]].sort_values("priority_score", ascending=False)
    cols = [
        "transaction_id", "timestamp", "gateway", "channel", "amount", "status",
        "processing_time_ms", "retry_count", "risk_score", "anomaly_reason", "priority_score",
    ]
    return anomalies[cols].head(top_n).reset_index(drop=True)
