"""
Builds a SQLite database (fintech_ops.db) from the CSVs in this folder.
SQLite is used so the whole project runs with zero external DB setup —
perfect for free hosting (Streamlit Cloud has no persistent server DB).

Run:
    python build_database.py
"""
import sqlite3
import pandas as pd
import os

HERE = os.path.dirname(__file__)
DB_PATH = os.path.join(HERE, "fintech_ops.db")

txn_df = pd.read_csv(os.path.join(HERE, "transactions.csv"), parse_dates=["timestamp"])
tickets_df = pd.read_csv(
    os.path.join(HERE, "support_tickets.csv"), parse_dates=["created_at", "resolved_at"]
)

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
txn_df.to_sql("transactions", conn, if_exists="replace", index=False)
tickets_df.to_sql("support_tickets", conn, if_exists="replace", index=False)

conn.execute("CREATE INDEX idx_txn_ts ON transactions(timestamp);")
conn.execute("CREATE INDEX idx_txn_status ON transactions(status);")
conn.execute("CREATE INDEX idx_ticket_created ON support_tickets(created_at);")
conn.execute("CREATE INDEX idx_ticket_sla ON support_tickets(sla_breached);")
conn.commit()
conn.close()

print(f"Database built at: {DB_PATH}")
print(f"  transactions: {len(txn_df):,} rows")
print(f"  support_tickets: {len(tickets_df):,} rows")
