"""Compute decentralisation metrics over rolling time windows."""
import pandas as pd

from .decentralisation import all_metrics


def metrics_over_time(attributed, period="M", unknown="exclude"):
    """Long-format metric time series.

    Parameters
    ----------
    attributed : DataFrame with columns [timestamp, pool]
    period : "D", "W", or "M" -- temporal granularity (the RQ3 knob)
    unknown : "exclude" (U2) or "single" (U1) -- treatment of unattributed blocks (a D3 axis)
    """
    df = attributed.copy()
    df["window"] = pd.to_datetime(df["timestamp"]).dt.to_period(period).dt.to_timestamp()
    if unknown == "exclude":
        df = df[df["pool"] != "unknown"]
    rows = []
    for window, group in df.groupby("window"):
        counts = group["pool"].value_counts().to_dict()
        for name, value in all_metrics(counts).items():
            rows.append({"window": window, "metric": name, "value": value,
                         "period": period, "unknown": unknown})
    return pd.DataFrame(rows)
