"""Time-safe features and chronological visitor funnel."""

import pandas as pd


def build_snapshot(events: pd.DataFrame, cutoff: pd.Timestamp, history_days: int = 14, horizon_days: int = 7) -> pd.DataFrame:
    """Build one active-user snapshot; features precede cutoff, label follows it."""
    start = cutoff - pd.Timedelta(days=history_days)
    end = cutoff + pd.Timedelta(days=horizon_days)
    history = events.loc[(events.event_time >= start) & (events.event_time < cutoff)].copy()
    history["event_day"] = history.event_time.dt.floor("D")
    history["is_view"] = (history.event == "view").astype("int8")
    history["is_cart"] = (history.event == "addtocart").astype("int8")
    history["is_transaction"] = (history.event == "transaction").astype("int8")
    features = history.groupby("visitorid", sort=False).agg(
        view_count=("is_view", "sum"),
        cart_count=("is_cart", "sum"),
        transaction_count=("is_transaction", "sum"),
        unique_items=("itemid", "nunique"),
        active_days=("event_day", "nunique"),
        last_event=("event_time", "max"),
    ).reset_index()
    features["recency_days"] = (cutoff - features.pop("last_event")).dt.total_seconds() / 86400
    buyers = set(events.loc[(events.event_time >= cutoff) & (events.event_time < end) & (events.event == "transaction"), "visitorid"])
    features["label"] = features.visitorid.isin(buyers).astype("int8")
    features["cutoff"] = cutoff
    return features


def ordered_funnel(events: pd.DataFrame) -> dict[str, int]:
    """Count unique visitors with strictly ordered events (all products)."""
    first_view = events.loc[events.event == "view"].groupby("visitorid").event_time.min().rename("view_time")
    carts = events.loc[events.event == "addtocart", ["visitorid", "event_time"]].join(first_view, on="visitorid")
    first_cart = carts.loc[carts.event_time > carts.view_time].groupby("visitorid").event_time.min().rename("cart_time")
    purchases = events.loc[events.event == "transaction", ["visitorid", "event_time"]].join(first_view, on="visitorid")
    any_purchase_after_view = purchases.loc[purchases.event_time > purchases.view_time, "visitorid"].nunique()
    purchases = purchases.join(first_cart, on="visitorid")
    ordered = purchases.loc[purchases.event_time > purchases.cart_time, "visitorid"].nunique()
    return {
        "view": int(first_view.size),
        "view_to_cart": int(first_cart.size),
        "view_cart_to_purchase": int(ordered),
        "view_to_purchase_any": int(any_purchase_after_view),
    }
