import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="IPL Match Analytics",
    page_icon="🏏",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

DB = "../data/ipl.db"


@st.cache_resource
def get_connection():

    return sqlite3.connect(
        DB,
        check_same_thread=False
    )


con = get_connection()


# ============================================================
# SQL HELPER
# ============================================================

@st.cache_data
def q(sql, params=()):

    return pd.read_sql_query(
        sql,
        con,
        params=params
    )


# ============================================================
# TITLE
# ============================================================

st.title("🏏 IPL Match Analytics")

st.caption(
    "For the match analyst — deciding what happened in a match "
    "and what the league trend means."
)


# ============================================================
# COMMON DATA
# ============================================================

seasons_df = q("""
    SELECT DISTINCT season_year
    FROM matches_clean
    WHERE season_year IS NOT NULL
    ORDER BY season_year
""")


seasons = seasons_df["season_year"].tolist()


# ============================================================
# TAB CREATION
# ============================================================

tab1, tab2 = st.tabs([
    "📊 Competition Overview",
    "🏏 Match Detail"
])


# ============================================================
# TAB 1
# OVERVIEW — THE WHOLE COMPETITION
# ============================================================

with tab1:

    st.header("Competition Overview")

    st.write(
        "This page shows how the IPL has changed across seasons, "
        "how successful chasing has been, and how scoring has evolved."
    )


    # ========================================================
    # FILTER
    # ========================================================

    selected_seasons = st.multiselect(
        "Season",
        options=seasons,
        default=seasons
    )


    # If nothing selected
    if not selected_seasons:
        st.warning("Please select at least one season.")
        st.stop()


    # ========================================================
    # PARAMETER STRING
    # ========================================================

    season_placeholders = ",".join(
        ["?"] * len(selected_seasons)
    )


    # ========================================================
    # CARD 1
    # SCALE OF DATA
    # ========================================================

    scale_df = q("""
        SELECT
            COUNT(DISTINCT match_id) AS total_matches,
            COUNT(DISTINCT season_year) AS total_seasons
        FROM matches_clean
    """)


    total_matches = int(
        scale_df.iloc[0]["total_matches"]
    )

    total_seasons = int(
        scale_df.iloc[0]["total_seasons"]
    )


    # ========================================================
    # CARD 2
    # TOTAL RUNS
    # ========================================================

    total_runs_df = q(f"""
        SELECT
            SUM(total_runs) AS total_runs
        FROM v_ball
        WHERE season_year IN ({season_placeholders})
    """, tuple(selected_seasons))


    total_runs = int(
        total_runs_df.iloc[0]["total_runs"] or 0
    )


    # ========================================================
    # CARD 3
    # CHASE TEST
    # ========================================================

    chase_test_df = q(f"""
        WITH match_results AS (

            SELECT
                match_id,
                winner,
                team1,
                team2
            FROM matches_clean
            WHERE season_year IN ({season_placeholders})
        )

        SELECT

            COUNT(*) AS total_matches,

            SUM(
                CASE
                    WHEN winner = team2 THEN 1
                    ELSE 0
                END
            ) AS chase_wins

        FROM match_results

        WHERE winner IS NOT NULL
    """, tuple(selected_seasons))


    chase_total = int(
        chase_test_df.iloc[0]["total_matches"] or 0
    )

    chase_wins = int(
        chase_test_df.iloc[0]["chase_wins"] or 0
    )


    if chase_total > 0:

        chase_rate = chase_wins / chase_total

        # One-sample proportion test against 50%
        z_stat = (
            (chase_rate - 0.50)
            /
            ((0.50 * 0.50 / chase_total) ** 0.5)
        )

        p_value = 2 * (
            1 - stats.norm.cdf(abs(z_stat))
        )

    else:

        chase_rate = 0
        p_value = 1


    # ========================================================
    # THREE METRIC CARDS
    # ========================================================

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Matches in competition",
            f"{total_matches:,}"
        )

        st.caption(
            f"Across {total_seasons} seasons"
        )


    with col2:

        st.metric(
            "Total runs",
            f"{total_runs:,}"
        )

        st.caption(
            "Selected seasons"
        )


    with col3:

        st.metric(
            "Chase win rate",
            f"{chase_rate:.1%}"
        )

        st.caption(
            f"95% expectation test p={p_value:.4f}"
        )


    st.divider()


    # ========================================================
    # VISUAL 1 — HERO
    # AVERAGE INNINGS SCORE BY SEASON
    # ========================================================

    avg_score_df = q(f"""

        SELECT

            season_year,

            ROUND(
                AVG(first_innings_runs),
                2
            ) AS average_innings_score,

            COUNT(*) AS match_count

        FROM v_match_totals

        WHERE innings = 1

        AND season_year IN ({season_placeholders})

        GROUP BY season_year

        ORDER BY season_year

    """, tuple(selected_seasons))


    if not avg_score_df.empty:

        league_average = avg_score_df[
            "average_innings_score"
        ].mean()


        fig = px.line(
            avg_score_df,
            x="season_year",
            y="average_innings_score",
            markers=True,
            title=(
                "Average first-innings score shows how "
                "the scoring environment has changed"
            ),
            labels={
                "season_year": "Season",
                "average_innings_score":
                    "Average innings score"
            }
        )


        fig.add_hline(
            y=league_average,
            line_dash="dash",
            annotation_text=(
                f"League average: {league_average:.1f}"
            )
        )


        fig.update_layout(
            height=500
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


        st.caption(
            f"n = {len(avg_score_df):,} seasons"
        )


    # ========================================================
    # VISUAL 2 — CHASE WIN RATE BY TARGET BAND
    # ========================================================

    target_df = q(f"""

        WITH match_data AS (

            SELECT

                match_id,

                first_innings_runs,

                winner,

                team2

            FROM v_match_totals

            WHERE innings = 1

            AND season_year IN ({season_placeholders})

        )

        SELECT

            CASE

                WHEN first_innings_runs < 120
                    THEN 'Below 120'

                WHEN first_innings_runs < 150
                    THEN '120–149'

                WHEN first_innings_runs < 180
                    THEN '150–179'

                WHEN first_innings_runs < 200
                    THEN '180–199'

                ELSE '200+'

            END AS target_band,

            COUNT(*) AS matches,

            SUM(
                CASE
                    WHEN winner = team2
                    THEN 1
                    ELSE 0
                END
            ) AS chase_wins,

            ROUND(
                100.0 *
                SUM(
                    CASE
                        WHEN winner = team2
                        THEN 1
                        ELSE 0
                    END
                )
                / COUNT(*),
                2
            ) AS chase_win_rate

        FROM match_data

        WHERE winner IS NOT NULL

        GROUP BY target_band

        ORDER BY
            CASE target_band

                WHEN 'Below 120' THEN 1
                WHEN '120–149' THEN 2
                WHEN '150–179' THEN 3
                WHEN '180–199' THEN 4
                WHEN '200+' THEN 5

            END

    """, tuple(selected_seasons))


    fig = px.bar(
        target_df,
        x="target_band",
        y="chase_win_rate",
        text="chase_win_rate",
        title=(
            "Chasing becomes harder as the target rises"
        ),
        labels={
            "target_band": "Target band",
            "chase_win_rate": "Chase win rate (%)"
        }
    )


    fig.add_hline(
        y=50,
        line_dash="dash",
        annotation_text="50% even contest"
    )


    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.caption(
        "Each bar shows the number of matches behind the rate."
    )


    # ========================================================
    # VISUAL 3 — SIXES BY SEASON
    # ========================================================

    sixes_df = q(f"""

        SELECT

            season_year,

            SUM(
                CASE
                    WHEN batsman_runs = 6
                    THEN 1
                    ELSE 0
                END
            ) AS sixes,

            COUNT(DISTINCT match_id) AS matches

        FROM v_ball

        WHERE season_year IN ({season_placeholders})

        GROUP BY season_year

        ORDER BY season_year

    """, tuple(selected_seasons))


    fig = px.bar(
        sixes_df,
        x="season_year",
        y="sixes",
        title=(
            "Six-hitting has changed across IPL seasons"
        ),
        labels={
            "season_year": "Season",
            "sixes": "Sixes"
        }
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.caption(
        "n = matches shown for each season."
    )


    # ========================================================
    # VISUAL 4 — WINS BY MARGIN TYPE
    # ========================================================

    margin_df = q(f"""

        SELECT

            CASE

                WHEN win_by_runs > 0
                    THEN 'Won by runs'

                WHEN win_by_wickets > 0
                    THEN 'Won by wickets'

                ELSE 'Other / No result'

            END AS margin_type,

            COUNT(*) AS matches

        FROM matches_clean

        WHERE season_year IN ({season_placeholders})

        GROUP BY margin_type

    """, tuple(selected_seasons))


    fig = px.bar(
        margin_df,
        x="margin_type",
        y="matches",
        text="matches",
        title=(
            "Wins are split between defending and chasing"
        ),
        labels={
            "margin_type": "Result type",
            "matches": "Matches"
        }
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # ========================================================
    # VISUAL 5 — WICKETS PER MATCH BY SEASON
    # OWN VISUAL
    # ========================================================

    wickets_df = q(f"""

        SELECT

            season_year,

            ROUND(
                AVG(total_wickets),
                2
            ) AS wickets_per_match,

            COUNT(*) AS matches

        FROM v_match_totals

        WHERE season_year IN ({season_placeholders})

        GROUP BY season_year

        ORDER BY season_year

    """, tuple(selected_seasons))


    fig = px.line(
        wickets_df,
        x="season_year",
        y="wickets_per_match",
        markers=True,
        title=(
            "Wickets per match show how match endings "
            "have changed"
        ),
        labels={
            "season_year": "Season",
            "wickets_per_match":
                "Average wickets per match"
        }
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# TAB 2
# MATCH — ONE GAME AT A TIME
# ============================================================

with tab2:

    st.header("Match Detail")

    st.write(
        "Select a season and team first, then choose one match. "
        "Every card and visual below responds to that selection."
    )


    # ========================================================
    # FILTER 1 — SEASON
    # ========================================================

    detail_season = st.selectbox(
        "1️⃣ Select Season",
        options=seasons
    )


    # ========================================================
    # FILTER 2 — TEAM
    # ========================================================

    teams_df = q("""
        SELECT DISTINCT team1 AS team
        FROM matches_clean

        UNION

        SELECT DISTINCT team2 AS team
        FROM matches_clean

        ORDER BY team
    """)


    teams = teams_df["team"].dropna().tolist()


    detail_team = st.selectbox(
        "2️⃣ Select Team",
        options=teams
    )


    # ========================================================
    # FILTER 3 — MATCH
    # ========================================================

    match_list_df = q("""

        SELECT

            match_id,

            team1,

            team2,

            venue_clean,

            season_year

        FROM matches_clean

        WHERE season_year = ?

        AND (
            team1 = ?
            OR team2 = ?
        )

        ORDER BY match_id DESC

    """, (
        detail_season,
        detail_team,
        detail_team
    ))


    if match_list_df.empty:

        st.warning(
            "No matches found for this season and team."
        )

        st.stop()


    # Human-readable match label

    match_list_df["match_label"] = (
        match_list_df["team1"]
        + " vs "
        + match_list_df["team2"]
        + " — "
        + match_list_df["venue_clean"].fillna("Unknown venue")
        + " — "
        + match_list_df["season_year"].astype(str)
    )


    selected_match_label = st.selectbox(
        "3️⃣ Select Match",
        options=match_list_df["match_label"].tolist()
    )


    selected_match_id = match_list_df.loc[
        match_list_df["match_label"] == selected_match_label,
        "match_id"
    ].iloc[0]


    # ========================================================
    # SELECTED MATCH INFORMATION
    # ========================================================

    match_info = q("""

        SELECT

            match_id,
            season_year,
            team1,
            team2,
            toss_winner,
            toss_decision,
            winner,
            win_by_runs,
            win_by_wickets,
            player_of_match,
            venue_clean

        FROM matches_clean

        WHERE match_id = ?

    """, (selected_match_id,))


    match = match_info.iloc[0]


    # ========================================================
    # RESULT TEXT
    # ========================================================

    winner = match["winner"]

    win_by_runs = match["win_by_runs"] or 0

    win_by_wickets = match["win_by_wickets"] or 0


    if pd.isna(winner):

        result_text = "No result"

    elif win_by_runs > 0:

        result_text = (
            f"{winner} won by {int(win_by_runs)} runs"
        )

    elif win_by_wickets > 0:

        result_text = (
            f"{winner} won by {int(win_by_wickets)} wickets"
        )

    else:

        result_text = f"{winner} won"


    # ========================================================
    # INNINGS SCORES
    # ========================================================

    innings_df = q("""

        SELECT

            innings,
            batting_team,
            SUM(total_runs) AS runs,
            SUM(total_wickets) AS wickets

        FROM v_ball

        WHERE match_id = ?

        GROUP BY
            innings,
            batting_team

        ORDER BY innings

    """, (selected_match_id,))


    # ========================================================
    # THREE METRIC CARDS
    # ========================================================

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Match Result",
            result_text
        )


    with col2:

        if len(innings_df) >= 1:

            first_team = innings_df.iloc[0]["batting_team"]
            first_runs = int(
                innings_df.iloc[0]["runs"]
            )
            first_wickets = int(
                innings_df.iloc[0]["wickets"]
            )

            st.metric(
                "First Innings",
                f"{first_team}: {first_runs}/{first_wickets}"
            )

        else:

            st.metric(
                "First Innings",
                "No data"
            )


    with col3:

        if len(innings_df) >= 2:

            second_team = innings_df.iloc[1]["batting_team"]
            second_runs = int(
                innings_df.iloc[1]["runs"]
            )
            second_wickets = int(
                innings_df.iloc[1]["wickets"]
            )

            st.metric(
                "Second Innings",
                f"{second_team}: {second_runs}/{second_wickets}"
            )

        else:

            st.metric(
                "Second Innings",
                "No data"
            )


    st.divider()


    # ========================================================
    # VISUAL 1 — HERO
    # RUNS PER OVER
    # ========================================================

    over_df = q("""

        SELECT

            innings,

            batting_team,

            over,

            SUM(total_runs) AS runs

        FROM v_ball

        WHERE match_id = ?

        GROUP BY
            innings,
            batting_team,
            over

        ORDER BY
            innings,
            over

    """, (selected_match_id,))


    if not over_df.empty:

        over_df["innings_label"] = (
            over_df["batting_team"]
            + " — Innings "
            + over_df["innings"].astype(str)
        )


        fig = px.line(
            over_df,
            x="over",
            y="runs",
            color="innings_label",
            markers=True,
            title=(
                "The innings turned at the overs "
                "where scoring separated"
            ),
            labels={
                "over": "Over",
                "runs": "Runs in over",
                "innings_label": "Innings"
            }
        )


        fig.update_layout(
            height=500
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


        st.caption(
            f"n = {over_df['over'].nunique()} overs represented."
        )


    # ========================================================
    # VISUAL 2 — FOURS AND SIXES
    # ========================================================

    boundary_df = q("""

        SELECT

            batting_team,

            SUM(
                CASE
                    WHEN batsman_runs = 4
                    THEN 1
                    ELSE 0
                END
            ) AS fours,

            SUM(
                CASE
                    WHEN batsman_runs = 6
                    THEN 1
                    ELSE 0
                END
            ) AS sixes

        FROM v_ball

        WHERE match_id = ?

        GROUP BY batting_team

    """, (selected_match_id,))


    if not boundary_df.empty:

        boundary_long = boundary_df.melt(
            id_vars=["batting_team"],
            value_vars=["fours", "sixes"],
            var_name="boundary",
            value_name="count"
        )


        fig = px.bar(
            boundary_long,
            x="batting_team",
            y="count",
            color="boundary",
            barmode="group",
            text="count",
            title=(
                "The two innings produced different "
                "boundary profiles"
            ),
            labels={
                "batting_team": "Team",
                "count": "Boundaries",
                "boundary": "Boundary type"
            }
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # ========================================================
    # VISUAL 3 — TOP BATTERS
    # ========================================================

    top_batters_df = q("""

        SELECT

            batter,

            SUM(batsman_runs) AS runs,

            COUNT(*) AS balls,

            SUM(
                CASE
                    WHEN batsman_runs = 4
                    THEN 1
                    ELSE 0
                END
            ) AS fours,

            SUM(
                CASE
                    WHEN batsman_runs = 6
                    THEN 1
                    ELSE 0
                END
            ) AS sixes

        FROM v_ball

        WHERE match_id = ?

        GROUP BY batter

        ORDER BY runs DESC

        LIMIT 10

    """, (selected_match_id,))


    # ========================================================
    # TOP BOWLERS
    # ========================================================

    top_bowlers_df = q("""

        SELECT

            bowler,

            SUM(
                CASE
                    WHEN wicket_type IS NOT NULL
                    AND wicket_type NOT IN (
                        'retired hurt',
                        'obstructing the field'
                    )
                    THEN 1
                    ELSE 0
                END
            ) AS wickets,

            SUM(total_runs) AS runs_conceded,

            COUNT(*) AS balls

        FROM v_ball

        WHERE match_id = ?

        GROUP BY bowler

        ORDER BY wickets DESC,
                 runs_conceded ASC

        LIMIT 10

    """, (selected_match_id,))


    # ========================================================
    # VISUAL 4 — PLAYER TABLE
    # ========================================================

    st.subheader(
        "The leading players show whether the Player of the Match "
        "award matches the performance"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.write("### 🏏 Top Run Scorers")

        st.dataframe(
            top_batters_df,
            use_container_width=True,
            hide_index=True
        )


    with col2:

        st.write("### 🎯 Top Wicket Takers")

        st.dataframe(
            top_bowlers_df,
            use_container_width=True,
            hide_index=True
        )


    st.caption(
        f"Player of the Match: {match['player_of_match']}"
    )


    # ========================================================
    # VISUAL 5 — TOSS
    # ========================================================

    toss_df = pd.DataFrame({

        "Item": [
            "Toss Winner",
            "Toss Decision",
            "Match Winner",
            "Venue"
        ],

        "Value": [
            match["toss_winner"],
            match["toss_decision"],
            match["winner"],
            match["venue_clean"]
        ]

    })


    st.subheader(
        "The toss choice and match result put the game in context"
    )


    st.dataframe(
        toss_df,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # ADDITIONAL VISUAL — PHASE SPLIT
    # ========================================================

    phase_df = q("""

        SELECT

            batting_team,

            CASE

                WHEN over < 6
                    THEN 'Powerplay'

                WHEN over < 15
                    THEN 'Middle'

                ELSE 'Death'

            END AS phase,

            SUM(total_runs) AS runs

        FROM v_ball

        WHERE match_id = ?

        GROUP BY
            batting_team,
            phase

        ORDER BY
            batting_team,
            phase

    """, (selected_match_id,))


    if not phase_df.empty:

        fig = px.bar(
            phase_df,
            x="phase",
            y="runs",
            color="batting_team",
            barmode="group",
            text="runs",
            title=(
                "The scoring split shows where each innings "
                "built or lost momentum"
            ),
            labels={
                "phase": "Innings phase",
                "runs": "Runs",
                "batting_team": "Team"
            }
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "IPL Cricket Analytics — Domain C: Matches"
)