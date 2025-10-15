from functools import lru_cache

import pandas as pd


@lru_cache
def prettify_colnames(col):
    # convert snake case to Title Case
    return col.replace("_", " ").title()


def format_delta(td):
    seconds = int(td.total_seconds())
    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        return f"{seconds // 60} minutes ago"
    elif seconds < 86400:
        return f"{seconds // 3600} hour(s) ago"
    else:
        return f"{seconds // 86400} day(s) ago"


def series_human_friendly_time(series):
    now = pd.to_datetime("now", utc=True)
    deltas = now - series

    formatted = (
        series.dt.strftime("%Y-%m-%d %H:%M:%S")
        + " ("
        + deltas.apply(format_delta)
        + ")"
    )
    return formatted
