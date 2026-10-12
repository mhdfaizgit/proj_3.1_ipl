import sqlite3                  # the same driver the notebooks use
from pathlib import Path

import pandas as pd             # only to hold the rows a query returns
import plotly.express as px     # every chart on the page is drawn with this
import streamlit as st          # the page itself

st.set_page_config(page_title="IPL Match Analytics", page_icon="🏏", layout="wide")


# -----------------------------------------------------------------------------
# Database + one query helper
# -----------------------------------------------------------------------------
# app.py lives in dashboard/, so ipl.db is found by going one folder up.
# A relative path (not C:\Users\...) means it also works after you deploy.
DB = Path(__file__).resolve().parent.parent / "data" / "raw" / "ipl.db"


@st.cache_data                  # run each query once, not on every click
def q(sql, params=()):          # one helper for every query on the page
    with sqlite3.connect(DB) as con:        # opened and closed per call
        return pd.read_sql_query(sql, con, params=params)


# -----------------------------------------------------------------------------
# Sidebar filters (these control EVERYTHING on the page)
# -----------------------------------------------------------------------------
bounds = q("SELECT MIN(season_year) AS lo, MAX(season_year) AS hi FROM matches_clean").iloc[0]
first_season, last_season = int(bounds["lo"]), int(bounds["hi"])

with st.sidebar:
    st.header("Filters")

    lo, hi = st.select_slider(
        "Season",
        options=list(range(first_season, last_season + 1)),
        value=(first_season, last_season),
    )

    teams = q("""
        SELECT team1 AS t FROM matches_clean
        UNION
        SELECT team2 FROM matches_clean
        ORDER BY t
    """)["t"].dropna()

    team = st.selectbox("Team", ["All teams"] + list(teams))


# Every query below uses these two pieces, so the filters apply everywhere.
# "m" is always the alias for matches_clean in the queries.
WHERE = "m.season_year BETWEEN ? AND ?"
PARAMS = (lo, hi)
if team != "All teams":
    WHERE += " AND (m.team1 = ? OR m.team2 = ?)"
    PARAMS = (lo, hi, team, team)


# -----------------------------------------------------------------------------
# Title
# -----------------------------------------------------------------------------
st.title("IPL Match Analytics")
st.caption(
    "For the match analyst, understanding what happened in a match "
    "and what usually happens across the league."
)

overview_tab, match_tab = st.tabs(["Overview — Whole Competition", "Match — One Game at a Time"])


# =============================================================================
# TAB 1 — OVERVIEW
# =============================================================================
with overview_tab:
    st.subheader("Overview — the competition across seasons")

    n_matches = int(q(f"SELECT COUNT(*) AS n FROM matches_clean m WHERE {WHERE}", PARAMS).iloc[0, 0])
    if n_matches == 0:
        st.warning("No matches for this season / team selection.")
        st.stop()

    total_runs = q(f"""
        SELECT COALESCE(SUM(i.runs), 0) AS total_runs
        FROM v_innings i
        JOIN matches_clean m ON m.match_id = i.match_id
        WHERE {WHERE}
    """, PARAMS).iloc[0, 0]

    chase_rate = q(f"""
        SELECT 100.0 * AVG(mt.chase_won) AS rate
        FROM v_match_totals mt
        JOIN matches_clean m ON m.match_id = mt.match_id
        WHERE {WHERE}
    """, PARAMS).iloc[0, 0]
    chase_rate = float(chase_rate) if chase_rate is not None else 0.0

    # ---- three number cards ----
    c1, c2, c3 = st.columns(3)
    c1.metric("Matches", f"{n_matches:,}")
    c2.metric("Total runs", f"{int(total_runs):,}")
    c3.metric("Chase win rate", f"{chase_rate:.1f}%")

    # ---- chart 1: average innings score by season (hero) ----
    avg_score = q(f"""
        SELECT m.season_year, AVG(i.runs) AS avg_score
        FROM matches_clean m
        JOIN v_innings i ON i.match_id = m.match_id
        WHERE {WHERE}
        GROUP BY m.season_year
        ORDER BY m.season_year
    """, PARAMS)

    fig_hero = px.line(
        avg_score, x="season_year", y="avg_score", markers=True,
        labels={"season_year": "Season", "avg_score": "Average innings score"},
    )
    fig_hero.add_hline(
        y=float(avg_score["avg_score"].mean()),
        line_dash="dash",
        annotation_text="average of the selected seasons",
    )

    # ---- chart 2: chase win rate by target band ----
    band = q(f"""
        SELECT CASE WHEN mt.first_innings_runs < 140 THEN '<140'
                    WHEN mt.first_innings_runs < 170 THEN '140-169'
                    WHEN mt.first_innings_runs < 200 THEN '170-199'
                    ELSE '200+' END AS band,
               COUNT(*) AS matches,
               ROUND(100.0 * AVG(mt.chase_won), 1) AS chase_pct,
               MIN(mt.first_innings_runs) AS sort_key
        FROM v_match_totals mt
        JOIN matches_clean m ON m.match_id = mt.match_id
        WHERE {WHERE}
        GROUP BY band
        ORDER BY sort_key
    """, PARAMS)

    fig_band = px.bar(band, x="band", y="chase_pct", text="matches")
    fig_band.update_traces(textposition="inside", texttemplate="%{text} matches")
    fig_band.update_xaxes(categoryorder="array", categoryarray=band["band"])
    fig_band.add_hline(y=50, line_dash="dash", annotation_text="50% = even contest")
    fig_band.update_layout(
        xaxis_title="Target the chasing team faced",
        yaxis_title="How often the chase won (%)",
        showlegend=False,
    )

    left, right = st.columns([2, 1])
    with left:
        st.markdown("**Average innings score across seasons**")
        st.plotly_chart(fig_hero, use_container_width=True)
    with right:
        st.markdown("**Chasing gets harder as the target rises**")
        st.plotly_chart(fig_band, use_container_width=True)
        st.caption("Bands with few matches can swing a lot; check the match counts.")

    st.divider()
    col1, col2, col3 = st.columns(3)

    # ---- chart 3: sixes by season ----
    with col1:
        sixes = q(f"""
            SELECT m.season_year, COUNT(*) AS sixes
            FROM deliveries d
            JOIN matches_clean m ON m.match_id = d.match_id
            WHERE d.batter_runs = 6 AND d.is_super_over = 0 AND {WHERE}
            GROUP BY m.season_year
            ORDER BY m.season_year
        """, PARAMS)
        fig = px.bar(sixes, x="season_year", y="sixes",
                     labels={"season_year": "Season", "sixes": "Sixes"})
        st.markdown("**Sixes hit by season**")
        st.plotly_chart(fig, use_container_width=True)

    # ---- chart 4: wins by runs vs wickets ----
    with col2:
        margins = q(f"""
            SELECT CASE WHEN x.win_by_runs > 0 THEN 'Wins by runs'
                        WHEN x.win_by_wickets > 0 THEN 'Wins by wickets' END AS margin_type,
                   COUNT(*) AS matches
            FROM matches_clean m
            JOIN matches x ON x.match_id = m.match_id
            WHERE m.result = 'win' AND {WHERE}
            GROUP BY margin_type
        """, PARAMS).dropna(subset=["margin_type"])
        fig = px.bar(margins, x="margin_type", y="matches", text="matches",
                     labels={"margin_type": "Winning method", "matches": "Matches"})
        st.markdown("**Wins by runs vs wins by wickets**")
        st.plotly_chart(fig, use_container_width=True)

    # ---- chart 5: toss decision by season ----
    with col3:
        toss = q(f"""
            SELECT m.season_year, m.toss_decision, COUNT(*) AS matches
            FROM matches_clean m
            WHERE {WHERE}
            GROUP BY m.season_year, m.toss_decision
            ORDER BY m.season_year
        """, PARAMS)
        fig = px.bar(toss, x="season_year", y="matches", color="toss_decision",
                     barmode="stack",
                     labels={"season_year": "Season", "matches": "Matches",
                             "toss_decision": "Toss choice"})
        st.markdown("**What toss winners choose, by season**")
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# TAB 2 — MATCH DETAIL
# =============================================================================
with match_tab:
    st.subheader("Match — one game at a time")
    st.caption("The match list below follows the Season and Team filters in the sidebar.")

    matches = q(f"""
        SELECT m.match_id, m.season_year, m.team1, m.team2, m.venue_clean
        FROM matches_clean m
        WHERE {WHERE}
        ORDER BY m.season_year, m.match_id
    """, PARAMS)

    # A readable label for each match, mapped back to its id.
    labels = {
        f"{r.team1} vs {r.team2} — {r.venue_clean} ({r.season_year})": r.match_id
        for r in matches.itertuples()
    }
    chosen = st.selectbox("Pick a match", list(labels.keys()))
    match_id = int(labels[chosen])

    info = q("""
        SELECT m.venue_clean, m.city_clean, m.result, m.match_winner,
               m.player_of_match, m.toss_winner, m.toss_decision,
               x.win_by_runs, x.win_by_wickets
        FROM matches_clean m
        JOIN matches x ON x.match_id = m.match_id
        WHERE m.match_id = ?
    """, (match_id,)).iloc[0]

    innings = q("""
        SELECT innings, batting_team, runs, wickets
        FROM v_innings
        WHERE match_id = ?
        ORDER BY innings
    """, (match_id,))
    team_of = dict(zip(innings["innings"], innings["batting_team"]))   # innings number -> team

    def score_text(n):
        row = innings[innings["innings"] == n]
        if row.empty:
            return "Not played"
        r = row.iloc[0]
        return f"{r['batting_team']}: {int(r['runs'])}/{int(r['wickets'])}"

    # Result sentence
    if info["result"] == "win" and info["win_by_runs"] and info["win_by_runs"] > 0:
        result_text = f"{info['match_winner']} won by {int(info['win_by_runs'])} runs"
    elif info["result"] == "win" and info["win_by_wickets"] and info["win_by_wickets"] > 0:
        result_text = f"{info['match_winner']} won by {int(info['win_by_wickets'])} wickets"
    else:
        result_text = str(info["result"]).title() if info["result"] else "No result"

    # st.markdown is used (not st.metric) so long team names are never cut off.
    a, b, c = st.columns(3)
    a.markdown(f"**Result**\n\n{result_text}")
    b.markdown(f"**First innings**\n\n{score_text(1)}")
    c.markdown(f"**Second innings**\n\n{score_text(2)}")
    st.caption(
        f"Ground: {info['venue_clean']} · City: {info['city_clean']} · "
        f"Toss: {info['toss_winner']} chose to {info['toss_decision']} · "
        f"Player of the match: {info['player_of_match'] or 'Not recorded'}"
    )

    # ---- chart 1: runs per over (hero) ----
    runs_over = q("""
        SELECT innings, over_number + 1 AS over_number, SUM(total_runs) AS runs
        FROM v_ball
        WHERE match_id = ? AND innings IN (1, 2)
        GROUP BY innings, over_number
        ORDER BY innings, over_number
    """, (match_id,))
    runs_over["team"] = runs_over["innings"].map(team_of)

    fig_over = px.line(
        runs_over, x="over_number", y="runs", color="team", markers=True,
        labels={"over_number": "Over", "runs": "Runs in over", "team": "Batting team"},
    )

    # ---- chart 2: fours and sixes ----
    boundaries = q("""
        SELECT innings,
               SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) AS fours,
               SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) AS sixes
        FROM v_ball
        WHERE match_id = ? AND innings IN (1, 2)
        GROUP BY innings
        ORDER BY innings
    """, (match_id,))
    boundaries["team"] = boundaries["innings"].map(team_of)
    boundary_long = boundaries.melt(
        id_vars=["innings", "team"], value_vars=["fours", "sixes"],
        var_name="boundary", value_name="count",
    )
    fig_bound = px.bar(
        boundary_long, x="team", y="count", color="boundary", barmode="group", text="count",
        labels={"team": "Batting team", "count": "Boundaries", "boundary": "Type"},
    )

    left, right = st.columns([2, 1])
    with left:
        st.markdown("**Runs per over for both innings**")
        st.plotly_chart(fig_over, use_container_width=True)
    with right:
        st.markdown("**Fours and sixes by innings**")
        st.plotly_chart(fig_bound, use_container_width=True)

    st.divider()
    col1, col2, col3 = st.columns(3)

    # ---- table: top run-scorers and wicket-takers ----
    with col1:
        batters = q("""
            SELECT batter, SUM(batter_runs) AS runs, SUM(is_legal) AS balls
            FROM v_ball
            WHERE match_id = ?
            GROUP BY batter
            ORDER BY runs DESC, balls DESC
            LIMIT 5
        """, (match_id,))
        bowlers = q("""
            SELECT bowler, SUM(bowler_wicket) AS wickets, SUM(bowler_runs) AS runs_conceded
            FROM v_ball
            WHERE match_id = ?
            GROUP BY bowler
            ORDER BY wickets DESC, runs_conceded ASC
            LIMIT 5
        """, (match_id,))
        st.markdown("**Top run-scorers**")
        st.dataframe(batters, hide_index=True, use_container_width=True)
        st.markdown("**Top wicket-takers**")
        st.dataframe(bowlers, hide_index=True, use_container_width=True)

    # ---- chart 4: runs by phase ----
    with col2:
        phase = q("""
            SELECT innings, phase, SUM(total_runs) AS runs
            FROM v_ball
            WHERE match_id = ? AND innings IN (1, 2)
            GROUP BY innings, phase
            ORDER BY innings,
                     CASE phase WHEN 'Powerplay' THEN 1 WHEN 'Middle' THEN 2 ELSE 3 END
        """, (match_id,))
        phase["team"] = phase["innings"].map(team_of)
        fig_phase = px.bar(
            phase, x="phase", y="runs", color="team", barmode="group",
            labels={"phase": "Innings phase", "runs": "Runs", "team": "Batting team"},
        )
        st.markdown("**Where each innings scored its runs**")
        st.plotly_chart(fig_phase, use_container_width=True)

    # ---- chart 5: wickets by over ----
    with col3:
        wickets = q("""
            SELECT innings, over_number + 1 AS over_number, SUM(bowler_wicket) AS wickets
            FROM v_ball
            WHERE match_id = ? AND innings IN (1, 2)
            GROUP BY innings, over_number
            HAVING SUM(bowler_wicket) > 0
            ORDER BY innings, over_number
        """, (match_id,))
        st.markdown("**When the wickets fell**")
        if wickets.empty:
            st.info("No bowler-credited wickets in this match.")
        else:
            wickets["team"] = wickets["innings"].map(team_of)
            fig_w = px.bar(
                wickets, x="over_number", y="wickets", color="team", barmode="group",
                labels={"over_number": "Over", "wickets": "Wickets", "team": "Batting team"},
            )
            fig_w.update_yaxes(dtick=1)
            st.plotly_chart(fig_w, use_container_width=True)

