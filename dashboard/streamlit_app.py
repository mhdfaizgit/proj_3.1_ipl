import math
import sqlite3
from html import escape
from pathlib import Path
from typing import Any, cast

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# -----------------------------------------------------------------------------
# Page setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="IPL Cricket Analytics — Matches",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_CANDIDATES = [
    PROJECT_ROOT / "data" / "ipl.db",
    PROJECT_ROOT / "data" / "raw" / "ipl.db",
    PROJECT_ROOT / "data" / "processed" / "ipl.db",
]
DB = next((path for path in DB_CANDIDATES if path.exists()), DB_CANDIDATES[0])


# -----------------------------------------------------------------------------
# SQLite helpers
# All dashboard numbers come from SQL through q().
# -----------------------------------------------------------------------------
def _binom_two_sided(k, n, p):
    """Exact two-sided binomial p-value, used inside SQLite SQL."""
    if n <= 0 or k < 0 or k > n:
        return None
    if not 0 <= p <= 1:
        return None

    # For p=0.5, calculate the two-sided exact probability by recurrence.
    # The dashboard's tested finding uses H0: chase probability = 0.5.
    if p == 0.5:
        log2 = math.log(2.0)
        logs = []
        for x in range(n + 1):
            logs.append(
                math.lgamma(n + 1)
                - math.lgamma(x + 1)
                - math.lgamma(n - x + 1)
                - n * log2
            )
        observed = logs[k]
        total = sum(math.exp(v) for v in logs if v <= observed + 1e-12)
        return min(1.0, total)

    # General fallback.
    logs = []
    for x in range(n + 1):
        if p in (0, 1):
            prob = 1.0 if ((p == 1 and x == n) or (p == 0 and x == 0)) else 0.0
            logs.append(math.log(prob) if prob else -math.inf)
        else:
            logs.append(
                math.lgamma(n + 1)
                - math.lgamma(x + 1)
                - math.lgamma(n - x + 1)
                + x * math.log(p)
                + (n - x) * math.log1p(-p)
            )
    observed = logs[k]
    return min(1.0, sum(math.exp(v) for v in logs if v <= observed + 1e-12))


def _wilson_low(k, n, z=1.959963984540054):
    if n <= 0:
        return None
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (centre - spread) / den


def _wilson_high(k, n, z=1.959963984540054):
    if n <= 0:
        return None
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (centre + spread) / den


@st.cache_resource

def get_connection():
    if not DB.exists():
        raise FileNotFoundError(
            f"Database not found at {DB}. Put ipl.db in the project's data/ folder."
        )
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.create_function("binom_pvalue", 3, _binom_two_sided)
    conn.create_function("wilson_low", 2, _wilson_low)
    conn.create_function("wilson_high", 2, _wilson_high)
    return conn


@st.cache_data(ttl=300)
def q(sql, params=()):
    conn = get_connection()
    return pd.read_sql_query(sql, conn, params=params)


# -----------------------------------------------------------------------------
# Common query helpers
# -----------------------------------------------------------------------------
def season_clause(column, seasons):
    """Return a parameterized season predicate and its parameters."""
    if not seasons:
        return "1 = 0", []
    placeholders = ",".join("?" for _ in seasons)
    return f"{column} IN ({placeholders})", list(seasons)


def fmt_int(value):
    return f"{int(round(value)):,}"


def fmt_float(value, digits=2):
    return f"{float(value):.{digits}f}"


def as_int(value: Any) -> int:
    return int(cast(int, value)) if value is not None else 0


def as_float(value: Any) -> float:
    return float(cast(float, value)) if value is not None else 0.0


STAT_CARD_CSS = """
<style>
div[data-testid="stHorizontalBlock"] > div {
    align-items: stretch !important;
}
.stat-card {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: flex-start;
    height: 100%;
    min-height: 110px;
    padding: 0.75rem 0.85rem;
    border-radius: 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.02);
    box-sizing: border-box;
    white-space: normal;
    overflow-wrap: anywhere;
    word-wrap: break-word;
}
.stat-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.65);
    line-height: 1.2;
    letter-spacing: 0.02em;
    margin-bottom: 0.35rem;
}
.stat-value {
    font-size: clamp(1.1rem, 2vw, 1.8rem);
    font-weight: 700;
    line-height: 1.2;
    color: #f0f2f6;
    white-space: normal;
    word-wrap: break-word;
    overflow-wrap: anywhere;
    max-width: 100%;
}
</style>
"""


def render_stat(label: str, value: str):
    if not getattr(st, "_stat_cards_css_loaded", False):
        st.markdown(STAT_CARD_CSS, unsafe_allow_html=True)
        st._stat_cards_css_loaded = True

    st.markdown(
        """
        <div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
        </div>
        """.format(
            label=escape(str(label)),
            value=escape(str(value)),
        ),
        unsafe_allow_html=True,
    )


def chart_title(text: str):
    st.markdown(
        f'<div class="chart-title">{escape(text)}</div>',
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    .chart-title {
        min-height: 3em;
        margin: 0 0 0.5rem;
        color: var(--text-color, #f0f2f6);
        font-size: 1.06rem;
        font-weight: 600;
        line-height: 1.4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Dashboard title / reader sentence
# -----------------------------------------------------------------------------
st.title("IPL Match Analytics")
st.caption(
    "For the match analyst, understanding what happened in a match and what usually happens across the league."
)

try:
    conn = get_connection()
except Exception as exc:
    st.error(str(exc))
    st.stop()


# -----------------------------------------------------------------------------
# Tabs required by Domain C
# -----------------------------------------------------------------------------
overview_tab, match_tab = st.tabs(["Overview — Whole Competition", "Match — One Game at a Time"])


# =============================================================================
# TAB 1 — OVERVIEW
# =============================================================================
with overview_tab:
    st.subheader("Overview — the competition across seasons")

    seasons_df = q(
        """
        SELECT DISTINCT season_year
        FROM matches_clean
        WHERE season_year IS NOT NULL
        ORDER BY season_year
        """
    )
    all_seasons = seasons_df["season_year"].astype(int).tolist()

    selected_seasons = st.multiselect(
        "Season filter — matches_clean.season_year",
        options=all_seasons,
        default=all_seasons,
        help="Select one or more seasons. Every filtered visual and the tested card responds to this control.",
    )

    if not selected_seasons:
        st.warning("Select at least one season.")
        st.stop()

    season_sql, season_params = season_clause("m.season_year", selected_seasons)

    # -------------------------------------------------------------------------
    # Three metric cards
    # -------------------------------------------------------------------------
    scale = q(
        """
        SELECT COUNT(*) AS matches,
               COUNT(DISTINCT season_year) AS seasons
        FROM matches_clean
        """
    ).iloc[0]

    total_runs = q(
        """
        SELECT COALESCE(SUM(runs), 0) AS total_runs
        FROM v_innings
        """
    ).iloc[0, 0]

    chase_stats = q(
        f"""
        SELECT SUM(mt.chase_won) AS chase_wins,
               COUNT(*) AS n,
               100.0 * SUM(mt.chase_won) / NULLIF(COUNT(*), 0) AS chase_rate,
               100.0 * wilson_low(SUM(mt.chase_won), COUNT(*)) AS ci_low,
               100.0 * wilson_high(SUM(mt.chase_won), COUNT(*)) AS ci_high,
               binom_pvalue(SUM(mt.chase_won), COUNT(*), 0.5) AS p_value
        FROM v_match_totals mt
        JOIN matches_clean m ON m.match_id = mt.match_id
        WHERE {season_sql}
        """,
        season_params,
    ).iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Competition scale",
        fmt_int(scale["matches"]),
        f"{fmt_int(scale['seasons'])} seasons",
        help="Static scale card: before any season filter, as required by the specification.",
    )
    c2.metric("Total runs in the data", fmt_int(total_runs))
    c3.metric(
        "Chase win rate",
        f"{chase_stats['chase_rate']:.2f}%",
        f"95% CI {chase_stats['ci_low']:.2f}–{chase_stats['ci_high']:.2f}%",
    )
    st.caption(
        f"Tested finding: exact two-sided binomial test, H₀ = 50% chase wins; "
        f"n = {fmt_int(chase_stats['n'])}, chase wins = {fmt_int(chase_stats['chase_wins'])}, "
        f"p = {chase_stats['p_value']:.5f}."
    )

    # -------------------------------------------------------------------------
    # Visual 1 — HERO: average innings score by season
    # -------------------------------------------------------------------------
    avg_score = q(
        f"""
        SELECT m.season_year,
               AVG(i.runs) AS avg_score,
               COUNT(DISTINCT m.match_id) AS match_count
        FROM matches_clean m
        JOIN v_innings i ON i.match_id = m.match_id
        WHERE {season_sql}
        GROUP BY m.season_year
        ORDER BY m.season_year
        """,
        season_params,
    )

    league_avg = q(
        f"""
        SELECT AVG(i.runs) AS league_avg
        FROM matches_clean m
        JOIN v_innings i ON i.match_id = m.match_id
        WHERE {season_sql}
        """,
        season_params,
    ).iloc[0, 0]

    fig_hero = px.line(
        avg_score,
        x="season_year",
        y="avg_score",
        markers=True,
        labels={"season_year": "Season", "avg_score": "Average innings score"},
    )
    league_avg_value = as_float(league_avg)
    fig_hero.add_hline(
        y=league_avg_value,
        line_dash="dash",
        annotation_text=f"Selected-period average: {league_avg_value:.1f}",
        annotation_position="top left",
    )
    fig_hero.update_layout(
        margin=dict(l=20, r=20, t=65, b=20),
        height=420,
    )

    margin_season_sql, margin_season_params = season_clause("c.season_year", selected_seasons)

    # -------------------------------------------------------------------------
    # Visual 2 — chase win rate by target band
    # -------------------------------------------------------------------------
    target_band = q(
        f"""
        SELECT CASE
                   WHEN mt.first_innings_runs < 140 THEN '<140'
                   WHEN mt.first_innings_runs < 170 THEN '140–169'
                   WHEN mt.first_innings_runs < 200 THEN '170–199'
                   ELSE '200+'
               END AS target_band,
               SUM(mt.chase_won) AS chase_wins,
               COUNT(*) AS match_count,
               100.0 * SUM(mt.chase_won) / NULLIF(COUNT(*), 0) AS chase_rate
        FROM v_match_totals mt
        JOIN matches_clean m ON m.match_id = mt.match_id
        WHERE {season_sql}
        GROUP BY target_band
        ORDER BY CASE target_band
                   WHEN '<140' THEN 1
                   WHEN '140–169' THEN 2
                   WHEN '170–199' THEN 3
                   ELSE 4
                 END
        """,
        season_params,
    )

    fig_band = px.bar(
        target_band,
        x="target_band",
        y="chase_rate",
        text=target_band["chase_rate"].map(lambda x: f"{x:.1f}%"),
        labels={"target_band": "First-innings target", "chase_rate": "Chase win rate (%)"},
    )
    fig_band.add_hline(
        y=50,
        line_dash="dash",
        annotation_text="50% even contest",
        annotation_position="top left",
    )
    fig_band.update_layout(
        margin=dict(l=20, r=20, t=65, b=20),
        height=420,
    )

    hero_col, support_col = st.columns([2, 1])
    with hero_col:
        chart_title(
            "Average innings score changes across seasons — line chart, dashed line is the selected-period average"
        )
        st.plotly_chart(fig_hero, use_container_width=True)
        st.caption(
            "n = "
            + ", ".join(
                f"{as_int(r.season_year)}: {as_int(r.match_count)} matches" for r in avg_score.itertuples()
            )
        )
    with support_col:
        chart_title("Chasing becomes less successful as the target rises — bar chart, reference = 50%")
        st.plotly_chart(fig_band, use_container_width=True)
        st.caption(
            "n by target band = "
            + ", ".join(
                f"{r.target_band}: {as_int(r.match_count)}" for r in target_band.itertuples()
            )
        )

    # -------------------------------------------------------------------------
    # Context row — exactly three additional visuals
    # -------------------------------------------------------------------------
    st.divider()
    ctx1, ctx2, ctx3 = st.columns(3)

    # Visual 3 — sixes by season
    with ctx1:
        sixes = q(
            f"""
            SELECT m.season_year,
                   SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END) AS sixes,
                   COUNT(DISTINCT m.match_id) AS match_count
            FROM deliveries d
            JOIN matches_clean m ON m.match_id = d.match_id
            WHERE d.is_super_over = 0 AND {season_sql}
            GROUP BY m.season_year
            ORDER BY m.season_year
            """,
            season_params,
        )
        fig = px.bar(
            sixes,
            x="season_year",
            y="sixes",
            labels={"season_year": "Season", "sixes": "Sixes"},
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            height=300,
        )
        chart_title("Sixes hit by season — showing how the scoring environment has changed")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "n = "
            + ", ".join(
                f"{as_int(r.season_year)}: {as_int(r.match_count)} matches" for r in sixes.itertuples()
            )
        )

    # Visual 4 — wins by margin
    with ctx2:
        margins = q(
            f"""
            SELECT CASE
                     WHEN c.result = 'win' AND m.win_by_runs > 0 THEN 'Wins by runs'
                     WHEN c.result = 'win' AND m.win_by_wickets > 0 THEN 'Wins by wickets'
                   END AS margin_type,
                   COUNT(*) AS match_count
            FROM matches_clean c
            JOIN matches m ON m.match_id = c.match_id
            WHERE {margin_season_sql} AND c.result = 'win'
            GROUP BY margin_type
            ORDER BY margin_type
            """,
            margin_season_params,
        )
        fig = px.bar(
            margins,
            x="margin_type",
            y="match_count",
            text="match_count",
            labels={"margin_type": "Winning method", "match_count": "Matches"},
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            height=300,
        )
        chart_title("Winning margins split between runs and wickets")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("n = decisive matches in the selected season(s)")

    # Visual 5 — toss decision by season
    with ctx3:
        toss = q(
            f"""
            SELECT m.season_year,
                   m.toss_decision,
                   COUNT(*) AS match_count
            FROM matches_clean m
            WHERE {season_sql}
            GROUP BY m.season_year, m.toss_decision
            ORDER BY m.season_year, m.toss_decision
            """,
            season_params,
        )
        fig = px.bar(
            toss,
            x="season_year",
            y="match_count",
            color="toss_decision",
            barmode="stack",
            labels={"season_year": "Season", "match_count": "Matches", "toss_decision": "Toss choice"},
        )
        fig.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            height=300,
        )
        chart_title("Toss winners increasingly choose to field — stacked count by season")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("n = matches in the selected season(s)")


# =============================================================================
# TAB 2 — MATCH DETAIL
# =============================================================================
with match_tab:
    st.subheader("Match — one game at a time")

    detail_seasons = q(
        "SELECT DISTINCT season_year FROM matches_clean ORDER BY season_year"
    )["season_year"].astype(int).tolist()

    d1, d2 = st.columns(2)
    with d1:
        selected_season = st.selectbox(
            "Season filter — matches_clean.season_year",
            detail_seasons,
            index=len(detail_seasons) - 1,
        )

    teams_df = q(
        """
        SELECT DISTINCT team
        FROM (
            SELECT team1 AS team FROM matches_clean
            UNION
            SELECT team2 AS team FROM matches_clean
        )
        WHERE team IS NOT NULL AND TRIM(team) <> ''
        ORDER BY team
        """
    )
    team_options = ["All teams"] + teams_df["team"].tolist()

    with d2:
        selected_team = st.selectbox(
            "Team filter — matches_clean.team1 / team2",
            team_options,
        )

    # Parameterized match-list query. The visible label is human-readable.
    if selected_team == "All teams":
        match_rows = q(
            """
            SELECT match_id, season_year, team1, team2, venue_clean, city_clean
            FROM matches_clean
            WHERE season_year = ?
            ORDER BY match_id
            """,
            (selected_season,),
        )
    else:
        match_rows = q(
            """
            SELECT match_id, season_year, team1, team2, venue_clean, city_clean
            FROM matches_clean
            WHERE season_year = ?
              AND (team1 = ? OR team2 = ?)
            ORDER BY match_id
            """,
            (selected_season, selected_team, selected_team),
        )

    if match_rows.empty:
        st.warning("No matches are available for this season/team selection.")
        st.stop()

    match_rows["label"] = match_rows.apply(
        lambda r: f"{r['team1']} vs {r['team2']} — {r['venue_clean']} ({as_int(r['season_year'])})",
        axis=1,
    )
    label_to_id = dict(zip(match_rows["label"], match_rows["match_id"]))

    selected_label = st.selectbox(
        "Match selector — narrowed by the two filters above",
        list(label_to_id.keys()),
    )
    selected_match_id = int(label_to_id[selected_label])

    # -------------------------------------------------------------------------
    # Match cards
    # -------------------------------------------------------------------------
    match_info = q(
        """
        SELECT c.match_id,
               c.season_year,
               c.venue_clean,
               c.city_clean,
               c.team1,
               c.team2,
               c.result,
               c.match_winner,
               c.player_of_match,
               c.toss_winner,
               c.toss_decision,
               m.win_by_runs,
               m.win_by_wickets
        FROM matches_clean c
        JOIN matches m ON m.match_id = c.match_id
        WHERE c.match_id = ?
        """,
        (selected_match_id,),
    ).iloc[0]

    innings = q(
        """
        SELECT innings, batting_team, runs, wickets, legal_balls
        FROM v_innings
        WHERE match_id = ?
        ORDER BY innings
        """,
        (selected_match_id,),
    )

    first = innings[innings["innings"] == 1]
    second = innings[innings["innings"] == 2]

    def innings_text(frame):
        if frame.empty:
            return "Not played"