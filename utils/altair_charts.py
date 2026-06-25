"""Code to help with altair charts. A lot of this was vibe coded."""

import math

import altair as alt
import pandas as pd
import streamlit as st

from .constants import get_leaderboard_color, DEFAULT_COLOR
from .prettify import prettify_colnames


def _find_time_column(df: pd.DataFrame):
    candidates = ["minute_ts", "fetched_at", "timestamp", "time", "datetime", "date"]
    for col in candidates:
        if col in df.columns:
            # try to convert to datetime, return if successful
            ser = pd.to_datetime(df[col], errors="coerce", utc=True)
            if ser.notna().any():
                return col
    return None


def _melt_measure_columns(df: pd.DataFrame):
    # Prefer multiple *_ms columns if present; else fall back to a single duration_ms column
    ms_cols = [c for c in df.columns if c.endswith("_ms")]
    if len(ms_cols) > 1:
        melted = df.melt(
            id_vars=[c for c in df.columns if c not in ms_cols],
            value_vars=ms_cols,
            var_name="series",
            value_name="value_ms",
        )
        # Clean series names: remove trailing _ms and prettify
        melted["series"] = (
            melted["series"]
            .str.replace("_ms$", "", regex=True)
            .map(_standardize_series_label)
        )
        return melted, "series", "value_ms"
    # Single metric case
    value_col = (
        "duration_ms"
        if "duration_ms" in df.columns
        else (ms_cols[0] if ms_cols else None)
    )
    if value_col is None:
        return None, None, None
    out = df.copy()
    out["series"] = _standardize_series_label("duration")
    out["value_ms"] = out[value_col]
    return out, "series", "value_ms"


def _standardize_series_label(raw: str) -> str:
    s = str(raw).strip().replace("-", " ").replace(".", " ")
    s_lower = s.lower()

    # Heuristics to map to Top N naming
    def to_top(n: str) -> str:
        return f"Top {n}"

    if (
        any(tok in s_lower for tok in ["top1", "top 1", "rank1", "rank 1", "r1", "1 "])
        or s_lower.endswith(" 1")
        or s_lower.endswith("1")
    ):
        return to_top("1")
    if (
        any(tok in s_lower for tok in ["top2", "top 2", "rank2", "rank 2", "r2", "2 "])
        or s_lower.endswith(" 2")
        or s_lower.endswith("2")
    ):
        return to_top("2")
    if (
        any(tok in s_lower for tok in ["top3", "top 3", "rank3", "rank 3", "r3", "3 "])
        or s_lower.endswith(" 3")
        or s_lower.endswith("3")
    ):
        return to_top("3")
    if (
        any(
            tok in s_lower
            for tok in ["top10", "top 10", "rank10", "rank 10", "r10", "10 "]
        )
        or s_lower.endswith(" 10")
        or s_lower.endswith("10")
    ):
        return to_top("10")
    if (
        any(
            tok in s_lower
            for tok in ["top100", "top 100", "rank100", "rank 100", "r100", "100 "]
        )
        or s_lower.endswith(" 100")
        or s_lower.endswith("100")
    ):
        return to_top("100")
    return prettify_colnames(s)


def _series_color(label: str) -> str:
    mapping = {
        "Top 1": "#FFD700",  # gold
        "Top 2": "#C0C0C0",  # silver
        "Top 3": "#CD7F32",  # bronze
        "Top 10": "#636363",
        "Top 100": "#636363",
    }
    return mapping.get(label, DEFAULT_COLOR)


def _series_dash(label: str):
    # Dotted for Top 100, solid otherwise
    if label == "Top 100":
        return [4, 4]
    return [1, 0]


def _format_ms(ms):
    try:
        ms = float(ms)
    except Exception:
        return ""
    if not math.isfinite(ms):
        return ""
    if ms < 0:
        ms = 0.0
    total_seconds = int(ms // 1000)
    millis = int(ms % 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}.{millis:03d}"
    return f"{minutes}:{seconds:02d}.{millis:03d}"


@st.cache_data(ttl=300)
def _build_over_time_chart(df, leaderboard_name, hide_top_100):
    if "leaderboard_name" not in df.columns:
        return None, "No leaderboard_name column found in over-time dataset."

    sdf = df[df["leaderboard_name"] == leaderboard_name].copy()
    if sdf.empty:
        return None, "No data available for this leaderboard."

    time_col = _find_time_column(sdf)
    if not time_col:
        return None, "No time column found to plot over time."
    sdf[time_col] = pd.to_datetime(sdf[time_col], errors="coerce", utc=True)
    sdf = sdf.dropna(subset=[time_col])
    if sdf.empty:
        return None, "No valid timestamps to plot."

    max_ts = sdf[time_col].max()
    cutoff = max_ts - pd.Timedelta(days=14)
    sdf = sdf[sdf[time_col] >= cutoff]
    if sdf.empty:
        return None, "No data in the last 14 days."

    melted, series_col, value_col = _melt_measure_columns(sdf)
    if melted is None:
        return None, "No duration columns found to plot."

    if series_col and hide_top_100:
        melted = melted[melted[series_col] != "Top 100"]
        if melted.empty:
            return None, "No data to plot after filtering Top 100."

    melted["value_hms"] = melted[value_col].apply(_format_ms)

    y_max = None
    if series_col:
        latest = melted.sort_values(time_col).groupby(series_col, as_index=False).last()
        base_row = latest[latest[series_col] == "Top 1"]
        if not base_row.empty:
            base_val = float(base_row[value_col].iloc[0])
        else:
            base_val = float(latest[value_col].min())
        y_max = max(0.0, base_val * 3.0)
    else:
        last_val = float(melted.sort_values(time_col)[value_col].iloc[-1])
        y_max = max(0.0, last_val * 3.0)

    domain_max = float((max_ts + pd.Timedelta(hours=1)).timestamp() * 1000)
    base = alt.Chart(melted).encode(
        x=alt.X(f"{time_col}:T", title="Time", scale=alt.Scale(domainMax=domain_max))
    )

    ms_label_expr = (
        "floor(datum.value/3600000) > 0 ? "
        "floor(datum.value/3600000) + ':' + "
        "(floor((datum.value%3600000)/60000) < 10 ? '0' : '') + floor((datum.value%3600000)/60000) + ':' + "
        "(floor((datum.value%60000)/1000) < 10 ? '0' : '') + floor((datum.value%60000)/1000) : "
        "floor(datum.value/60000) + ':' + (floor((datum.value%60000)/1000) < 10 ? '0' : '') + floor((datum.value%60000)/1000)"
    )

    y_enc = alt.Y(
        f"{value_col}:Q",
        title="Duration",
        axis=alt.Axis(labelExpr=ms_label_expr),
        scale=alt.Scale(domainMin=0, domainMax=y_max),
    )

    hover = alt.selection_point(
        nearest=True, on="mouseover", fields=[time_col], empty=False
    )
    zoom_x = alt.selection_interval(bind="scales", encodings=["x"])

    series_values = melted[series_col].unique().tolist() if series_col else ["duration"]
    if len(series_values) == 1:
        color_value = get_leaderboard_color(leaderboard_name)
        line = base.mark_line().encode(
            y=y_enc,
            color=alt.value(color_value),
        )

        rule = (
            alt.Chart(melted)
            .mark_rule(color="gray")
            .encode(
                x=alt.X(f"{time_col}:T"),
                opacity=alt.condition(hover, alt.value(0.5), alt.value(0)),
                tooltip=[
                    alt.Tooltip(f"{time_col}:T", title="Time", format="%Y-%m-%d %H:%M"),
                    alt.Tooltip("value_hms:N", title="Duration"),
                ],
            )
            .add_params(hover)
        )

        chart = (line + rule).properties(height=300).add_params(zoom_x)
    else:
        domain = series_values
        color_range = [_series_color(lbl) for lbl in domain]
        dash_range = [_series_dash(lbl) for lbl in domain]

        line = base.mark_line().encode(
            y=y_enc,
            color=alt.Color(
                f"{series_col}:N",
                title="Series",
                scale=alt.Scale(domain=domain, range=color_range),
            ),
            strokeDash=alt.StrokeDash(
                f"{series_col}:N", scale=alt.Scale(domain=domain, range=dash_range)
            ),
        )

        def ms_expr(field):
            return (
                f"isValid(datum['{field}']) ? (floor(datum['{field}']/3600000) > 0 ? "
                f"floor(datum['{field}']/3600000) + ':' + "
                f"(floor((datum['{field}']%3600000)/60000) < 10 ? '0' : '') + floor((datum['{field}']%3600000)/60000) + ':' + "
                f"(floor((datum['{field}']%60000)/1000) < 10 ? '0' : '') + floor((datum['{field}']%60000)/1000) + '.' + "
                f"((floor(datum['{field}']%1000) < 10) ? '00' : (floor(datum['{field}']%1000) < 100 ? '0' : '')) + floor(datum['{field}']%1000) : "
                f"floor(datum['{field}']/60000) + ':' + (floor((datum['{field}']%60000)/1000) < 10 ? '0' : '') + floor((datum['{field}']%60000)/1000) + '.' + "
                f"((floor(datum['{field}']%1000) < 10) ? '00' : (floor(datum['{field}']%1000) < 100 ? '0' : '')) + floor(datum['{field}']%1000)) : ''"
            )

        calc_map = {f"{sv}_hms": ms_expr(sv) for sv in domain}

        rule = (
            alt.Chart(melted)
            .transform_pivot(series_col, value=value_col, groupby=[time_col])
            .transform_calculate(**calc_map)
            .mark_rule(color="gray")
            .encode(
                x=alt.X(f"{time_col}:T"),
                opacity=alt.condition(hover, alt.value(0.5), alt.value(0)),
                tooltip=[
                    alt.Tooltip(f"{time_col}:T", title="Time", format="%Y-%m-%d %H:%M")
                ]
                + [alt.Tooltip(f"{sv}_hms:N", title=str(sv)) for sv in domain],
            )
            .add_params(hover)
        )

        chart = (line + rule).properties(height=300).add_params(zoom_x)

    return chart, None


def display_over_time_chart(
    df: pd.DataFrame, leaderboard_name: str, hide_top_100: bool = True
):
    chart, error = _build_over_time_chart(df, leaderboard_name, hide_top_100)
    if error:
        st.info(error)
        return
    st.altair_chart(chart, use_container_width=True)
