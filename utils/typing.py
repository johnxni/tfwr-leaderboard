import pandas as pd


def _add_duration_cols(df):
    ms_cols = [col for col in df.columns if col.endswith("_ms")]
    for ms_col in ms_cols:
        col = ms_col[:-3]  # remove _ms suffix
        df[col] = pd.to_timedelta(df[ms_col], unit="ms")


def ms_to_str(ms):
    if ms is None or pd.isna(ms):
        return ""
    ms = int(ms)

    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    try:
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
        return f"{m:02d}:{s:02d}.{ms:03d}"
    except Exception as e:
        print("LOOK HERE", ms, h, m, s, ms)
        raise e


def gap_ms_to_str(ms):
    return f"+{ms_to_str(ms)}" if ms and ms > 0 else ""