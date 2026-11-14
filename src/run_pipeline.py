"""Rebuild clean data, ordered funnel, time-split purchase prediction and figures."""

import hashlib
import json
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.logic import build_snapshot, ordered_funnel


ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["view_count", "cart_count", "transaction_count", "unique_items", "active_days", "recency_days"]
CUTOFFS = {
    "train": ["2015-06-01", "2015-06-15", "2015-07-01", "2015-07-15"],
    "validation": ["2015-08-01"],
    "test": ["2015-08-15"],
}


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def evaluate(model, data):
    y = data.label.to_numpy()
    score = model.predict_proba(data[FEATURES])[:, 1]
    top_count = max(1, int(np.ceil(len(score) * 0.1)))
    top = np.zeros(len(score), dtype=bool)
    top[np.argsort(-score, kind="stable")[:top_count]] = True
    threshold = 0.5
    return {
        "rows": int(len(y)), "buyers": int(y.sum()), "base_rate": float(y.mean()),
        "pr_auc": float(average_precision_score(y, score)),
        "roc_auc": float(roc_auc_score(y, score)) if len(set(y)) == 2 else None,
        "recall_at_0_5": float(recall_score(y, score >= threshold, zero_division=0)),
        "precision_at_0_5": float(precision_score(y, score >= threshold, zero_division=0)),
        "top_decile_precision": float(y[top].mean()),
        "top_decile_lift": float(y[top].mean() / y.mean()) if y.mean() else None,
    }


def main():
    raw = ROOT / "data/raw/events.csv"
    if not raw.exists() or raw.stat().st_size < 50_000_000:
        raise FileNotFoundError("Complete RetailRocket events.csv (~94 MB) required in data/raw/")
    for name in ["data/processed", "figures", "reports"]:
        (ROOT / name).mkdir(exist_ok=True)
    db = duckdb.connect(str(ROOT / "data/processed/analytics.duckdb"))
    db.execute("SET threads TO 4")
    db.execute("SET memory_limit = '4GB'")
    db.execute("SET TimeZone = 'UTC'")
    # DuckDB reads relative CSV and writes relative Parquet from the project directory.
    import os
    os.chdir(ROOT)
    db.execute((ROOT / "sql/01_clean.sql").read_text(encoding="utf-8"))
    raw_count = db.execute("SELECT COUNT(*) FROM read_csv('data/raw/events.csv', header=true, all_varchar=true)").fetchone()[0]
    overview = db.execute("SELECT COUNT(*), COUNT(DISTINCT visitorid), COUNT(DISTINCT itemid), MIN(event_time), MAX(event_time) FROM events_clean").fetchone()
    counts = db.execute("SELECT event, COUNT(*) FROM events_clean GROUP BY event").fetchall()
    by_day = db.execute("SELECT CAST(event_time AS DATE) AS event_date, event, COUNT(*) AS events FROM events_clean GROUP BY 1,2 ORDER BY 1,2").df()
    by_day.to_csv(ROOT / "reports/daily_events.csv", index=False)
    events = db.execute("SELECT visitorid, itemid, event, event_time FROM events_clean ORDER BY event_time, visitorid, itemid, event, transactionid").df()
    events["event_time"] = pd.to_datetime(events.event_time, utc=True)
    funnel = ordered_funnel(events)
    snapshots = {}
    for split, dates in CUTOFFS.items():
        snapshots[split] = pd.concat(
            [build_snapshot(events, pd.Timestamp(date, tz="UTC")) for date in dates], ignore_index=True
        )
        snapshots[split].to_parquet(ROOT / f"data/processed/{split}_snapshots.parquet", index=False)
    train, val, test = (snapshots[k] for k in ["train", "validation", "test"])
    if any(s.label.nunique() < 2 for s in [train, val, test]):
        raise ValueError("A split has only one label; inspect date windows")
    models = {
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear")),
        "random_forest": RandomForestClassifier(n_estimators=80, max_depth=8, min_samples_leaf=20, class_weight="balanced_subsample", n_jobs=4, random_state=42),
    }
    validation = {}
    for name, model in models.items():
        model.fit(train[FEATURES], train.label)
        validation[name] = evaluate(model, val)
    winner = max(validation, key=lambda k: validation[k]["pr_auc"])
    # Test set is touched once, after model choice on validation PR-AUC.
    heldout = evaluate(models[winner], test)
    data_report = {
        "source": "RetailRocket/Kaggle; retrieved via public Google Drive mirror (see README); SHA-256 matches the Hugging Face mirror",
        "raw_sha256": sha256(raw), "raw_rows": int(raw_count), "clean_rows": int(overview[0]),
        "visitors": int(overview[1]), "items": int(overview[2]),
        "first_utc": str(overview[3]), "last_utc": str(overview[4]),
        "clean_event_counts": {k: int(v) for k, v in counts},
        "removed_rows": int(raw_count - overview[0]), "ordered_funnel": funnel,
        "funnel_definition": "Unique visitor, strictly time-ordered view < addtocart < transaction; any item. Direct view-to-purchase shown separately.",
    }
    model_report = {
        "target": "Active visitor buys within [cutoff, cutoff + 7 days)",
        "features": FEATURES, "history": "[cutoff - 14 days, cutoff)",
        "cutoffs_utc": CUTOFFS, "split_sizes": {k: int(len(v)) for k, v in snapshots.items()},
        "validation": validation, "chosen_by_validation_pr_auc": winner, "test": heldout,
        "caveat": "Repeated visitors can appear at separate time cutoffs; all features and labels respect time. Scores are observational, not causal uplift or ad attribution.",
    }
    save_json(ROOT / "reports/data_quality.json", data_report)
    save_json(ROOT / "reports/model_metrics.json", model_report)
    fig, ax = plt.subplots(figsize=(8, 4))
    daily = by_day.pivot(index="event_date", columns="event", values="events").fillna(0)
    for col in ["view", "addtocart", "transaction"]:
        ax.plot(daily.index, daily[col], label=col)
    ax.set_yscale("log")
    ax.set_ylabel("Daily event count (log scale)")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(ROOT / "figures/daily_events.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = ["Viewed", "Viewed → cart", "Viewed → cart → purchase"]
    values = [funnel["view"], funnel["view_to_cart"], funnel["view_cart_to_purchase"]]
    ax.barh(labels[::-1], values[::-1], color=["#177E89", "#39A7A0", "#99D5CF"][::-1])
    ax.set_xlabel("Unique visitors")
    fig.tight_layout()
    fig.savefig(ROOT / "figures/ordered_funnel.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"data_quality": data_report, "model_metrics": model_report}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
