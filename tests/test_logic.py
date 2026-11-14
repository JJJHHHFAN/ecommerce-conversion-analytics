import pandas as pd
import unittest

from src.logic import build_snapshot, ordered_funnel


class LogicTests(unittest.TestCase):
  def test_snapshot_uses_only_past_features_and_future_labels(self):
    events = pd.DataFrame(
        {
            "visitorid": [1, 1, 1, 2, 2],
            "event": ["view", "addtocart", "transaction", "view", "transaction"],
            "itemid": [10, 10, 10, 20, 20],
            "event_time": pd.to_datetime(
                ["2015-06-01", "2015-06-03", "2015-06-06", "2015-06-02", "2015-06-20"], utc=True
            ),
        }
    )
    snap = build_snapshot(events, pd.Timestamp("2015-06-05", tz="UTC"), history_days=7, horizon_days=7)
    by_user = snap.set_index("visitorid")
    self.assertEqual(by_user.loc[1, "view_count"], 1)
    self.assertEqual(by_user.loc[1, "cart_count"], 1)
    self.assertEqual(by_user.loc[1, "transaction_count"], 0)
    self.assertEqual(by_user.loc[1, "label"], 1)
    self.assertEqual(by_user.loc[2, "label"], 0)


  def test_ordered_funnel_requires_chronological_steps(self):
    events = pd.DataFrame(
        {
            "visitorid": [1, 1, 1, 2, 2, 3, 3],
            "event": ["view", "addtocart", "transaction", "transaction", "view", "view", "transaction"],
            "event_time": pd.to_datetime(
                ["2015-06-01", "2015-06-02", "2015-06-03", "2015-06-01", "2015-06-02", "2015-06-01", "2015-06-03"], utc=True
            ),
        }
    )
    result = ordered_funnel(events)
    self.assertEqual(result, {"view": 3, "view_to_cart": 1, "view_cart_to_purchase": 1, "view_to_purchase_any": 2})


if __name__ == "__main__":
    unittest.main()
