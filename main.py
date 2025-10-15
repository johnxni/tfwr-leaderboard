import pandas as pd
import streamlit as st


from utils.altair_charts import display_over_time_chart
from utils.constants import (
    OVER_TIME_S3,
    GAPS_LATEST_S3,
    PERCENTILES_S3,
    TABS,
    COLORS,
    EMOJIS,
    DEFAULT_COLOR,
)
from utils.typing import (
    gap_ms_to_str,
    ms_to_str,
)
from utils.prettify import prettify_colnames, series_human_friendly_time, format_delta


def get_leaderboard_color(leaderboard_name):
    return COLORS.get(leaderboard_name.split()[0], DEFAULT_COLOR)


def get_emoji(leaderboard_name):
    return EMOJIS.get(leaderboard_name.split()[0], ":man_farmer:")


@st.cache_data(ttl=300)
def load_over_time():
    df = pd.read_csv(OVER_TIME_S3)
    df["time"] = pd.to_datetime(
        df["time"], format="mixed", errors="coerce", utc=True
    )
    return df, get_last_updated(df)


@st.cache_data(ttl=300)
def load_gaps_latest():
    df = pd.read_csv(GAPS_LATEST_S3)
    df["achieved_at"] = pd.to_datetime(
        df["achieved_at"], format="mixed", errors="coerce", utc=True
    )
    return df


@st.cache_data(ttl=300)
def load_percentiles():
    df = pd.read_csv(PERCENTILES_S3)
    records = df.to_dict(orient="records")
    data = {r["leaderboard_name"]: r for r in records}
    return data


def get_last_updated(df_over_time):
    last_updated_ts = df_over_time.groupby('leaderboard_name')['time'].max().to_dict()
    now = pd.to_datetime('now', utc=True)
    last_updated = {k: f'{ts} ({format_delta(now-ts)} ago)' for k, ts in last_updated_ts.items()}
    return last_updated


def display_dataframe(df, leaderboard_name):
    condition = df["leaderboard_name"] == leaderboard_name

    duration_cols = df.select_dtypes(include=["timedelta64[ns]"])
    column_config = {
        prettify_colnames(col): st.column_config.TimeColumn(format="HH:mm:ss.ms")
        for col in duration_cols.columns
    }

    display_columns = {col: prettify_colnames(col) for col in df.columns}
    st.dataframe(
        df[condition].rename(columns=display_columns), column_config=column_config
    )


def display_top3(df_snapshot, leaderboard_name):
    top_n = 3
    condition = (df_snapshot["leaderboard_name"] == leaderboard_name) & (
        df_snapshot["rank"] <= top_n
    )
    records = df_snapshot[condition].sort_values("rank").to_dict(orient="records")

    boxes = st.columns(top_n)
    icons = ["🥇", "🥈", "🥉"]
    for box, info, icon in zip(boxes, records, icons):
        with box:
            info_box(icon, info["steam_name"], ms_to_str(info["duration_ms"]))


def display_percentiles(percentiles):
    fields = [k for k in percentiles if k.startswith("p") and k.endswith("_ms")]
    boxes = st.columns(len(fields) + 1)
    for field, box in zip(fields, boxes):
        with box:
            perc = int(field.lstrip("p").rstrip("_ms"))
            title = f"Top {perc}%"
            time = ms_to_str(percentiles[field])
            if time.count(':') == 2:
                time = time[:-4]  # prevent '...' from showing
            st.metric(title, time, delta=None, border=False)

    with boxes[-1]:
        st.metric(
            label="Entries", value=percentiles["entry_count"], delta=None, border=False
        )


def display_leaderboard(df_leaderboard, leaderboard_name, top_n=100, height=1600):
    condition = (df_leaderboard["leaderboard_name"] == leaderboard_name) & (
        df_leaderboard["rank"] <= top_n
    )
    num_rows = df_leaderboard[condition].shape[0]

    df_leaderboard["Time"] = df_leaderboard["duration_ms"].apply(ms_to_str)
    df_leaderboard["Gap"] = df_leaderboard["gap_prev_ms"].apply(gap_ms_to_str)
    df_leaderboard["Gap To Leader"] = df_leaderboard["gap_leader_ms"].apply(
        gap_ms_to_str
    )
    df_leaderboard["Date"] = series_human_friendly_time(df_leaderboard["achieved_at"])

    out_cols = ["rank", "steam_name", "Time", "Gap", "Gap To Leader", "Date"]
    column_renames = {"rank": "Rank", "steam_name": "Player"}
    st.dataframe(
        df_leaderboard[condition][out_cols].rename(columns=column_renames),
        hide_index=True,
        height=height if num_rows >= 50 else 'auto',
    )


def info_box(icon, name, time, color="#262730"):
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            border-radius:12px;
            padding:12px;
            text-align:center;
            color:white;
            font-family:monospace;
        ">
            <div style="font-size:24px;">{icon}</div>
            <div style="font-size:18px;">{name}</div>
            <div style="font-size:14px; color:#bbb;">{time}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_last_updated(last_updated_string):
    st.markdown(
        f"""
        <div style="text-align:left; color:gray; font-size:0.8rem; margin-top:2rem;">
            Last updated: {last_updated_string}
        </div>
        """,
        unsafe_allow_html=True
    )


def _get_query_leaderboard():
    leaderboards = st.query_params.get_all('leaderboard')
    return leaderboards[0] if leaderboards else 'Overview'


def _set_query_leaderboard(value: str):
    st.query_params.from_dict({'leaderboard': value})


def main():
    st.set_page_config("TFWR Leaderboards", ":trophy:")

    df_over_time, last_updated = load_over_time()
    df_snapshot = load_gaps_latest()
    df_percentiles = load_percentiles()

    # Initialize from query param if provided
    qp_selected = _get_query_leaderboard()
    if "selected_leaderboard" not in st.session_state:
        st.session_state.selected_leaderboard = (
            qp_selected if qp_selected in TABS else TABS[0]
        )
    else:
        # If the query param differs and is valid, sync session state
        if qp_selected in TABS and qp_selected != st.session_state.selected_leaderboard:
            st.session_state.selected_leaderboard = qp_selected

    # Ensure URL stays in sync with selection as early as possible (covers initial bare URL)
    if _get_query_leaderboard() != st.session_state.selected_leaderboard:
        _set_query_leaderboard(st.session_state.selected_leaderboard)

    with st.sidebar:
        st.write("The Farmer Was Replaced Leaderboards")
        hide_top_100 = True
        for name in TABS:
            is_active = name == st.session_state.selected_leaderboard
            button_name = f"{get_emoji(name)} {name}"
            if st.button(
                button_name,
                type=("primary" if is_active else "secondary"),
                use_container_width=True,
                key=f"nav_{name}",
            ):
                st.session_state.selected_leaderboard = name
                _set_query_leaderboard(name)

    selected_leaderboard = st.session_state.selected_leaderboard
    if selected_leaderboard == 'Overview':
        for leaderboard_name in TABS[1:]:
            st.header(f"{get_emoji(leaderboard_name)} {leaderboard_name} Top 10")
            display_leaderboard(df_snapshot, leaderboard_name, top_n=10, height='auto')
            display_last_updated(last_updated[leaderboard_name])
            st.divider()

    else:
        st.header(f"{get_emoji(selected_leaderboard)} {selected_leaderboard} Leaderboards")
        display_top3(df_snapshot, selected_leaderboard)
        st.divider()

        display_percentiles(df_percentiles[selected_leaderboard])
        st.divider()

        st.subheader("Leaderboard History")
        display_over_time_chart(
            df_over_time, selected_leaderboard, hide_top_100=hide_top_100
        )

        st.subheader("Leaderboard")
        display_leaderboard(df_snapshot, selected_leaderboard)
        display_last_updated(last_updated[selected_leaderboard])


if __name__ == "__main__":
    main()
