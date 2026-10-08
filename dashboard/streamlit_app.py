import sqlite3
import math

import pandas as pd
import streamlit as st
import plotly.express as px


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="IPL Match Analytics",
    page_icon="🏏",
    layout="wide"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

DB = r'C:\Users\Scalefusion admin\OneDrive\Documents\OJT- SEM 3\project_3.1 sem 3\data\raw\ipl.db'


@st.cache_resource
def get_connection():
    return sqlite3.connect(
        DB,
        check_same_thread=False
    )


con = get_connection()


# ============================================================
# SQL QUERY FUNCTION
# ============================================================

@st.cache_data
def q(sql, params=()):
    return pd.read_sql_query(
        sql,
        con,
        params=params
    )


# ============================================================
# DATABASE TEST
# ============================================================

try:

    test_df = q("""
        SELECT name
        FROM sqlite_master
        WHERE type IN ('table', 'view')
    """)

except Exception as e:

    st.error("Database connection failed.")

    st.code(str(e))

    st.info(
        "Check that ipl.db is inside the data folder "
        "and app.py is inside the dashboard folder."
    )

    st.stop()


# ============================================================
# TITLE
# ============================================================

st.title("🏏 IPL Match Analytics")

st.write(
    "For the match analyst — deciding what happened "
    "in a match and across the league."
)

st.caption(
    "Domain C — Matches"
)


# ============================================================
# CHECK REQUIRED TABLES / VIEWS
# ============================================================

available_objects = set(
    test_df["name"].tolist()
)

required_objects = [
    "matches_clean",
    "v_ball",
    "v_match_totals"
]

missing_objects = [
    obj
    for obj in required_objects
    if obj not in available_objects
]


if missing_objects:

    st.error(
        "The following required database objects are missing:"
    )

    for obj in missing_objects:
        st.write(f"- `{obj}`")

    st.write("Available tables/views:")

    st.dataframe(
        test_df,
        use_container_width=True,
        hide_index=True
    )

    st.stop()


# ============================================================
# SEASON LIST
# ============================================================

try:

    seasons_df = q("""
        SELECT DISTINCT season_year
        FROM matches_clean
        WHERE season_year IS NOT NULL
        ORDER BY season_year
    """)

    seasons = seasons_df[
        "season_year"
    ].tolist()

except Exception as e:

    st.error("Could not read season_year from matches_clean.")

    st.code(str(e))

    st.stop()


if not seasons:

    st.error("No seasons were found in the database.")

    st.stop()


# ============================================================
# TWO TABS
# ============================================================

tab1, tab2 = st.tabs(
    [
        "📊 Competition Overview",
        "🏏 Match Detail"
    ]
)


# ################################################################
# TAB 1
# COMPETITION OVERVIEW
# ################################################################

with tab1:

    st.header(
        "Overview — The Whole Competition"
    )

    st.write(
        "League-wide trends showing how IPL scoring, "
        "chasing and match results have changed."
    )


    # ============================================================
    # SEASON FILTER
    # ============================================================

    selected_seasons = st.multiselect(
        "Season",
        options=seasons,
        default=seasons,
        key="overview_seasons"
    )


    if not selected_seasons:

        st.warning(
            "Please select at least one season."
        )

        st.stop()


    # SQL placeholders
    season_placeholders = ",".join(
        ["?"] * len(selected_seasons)
    )


    # ============================================================
    # CARD 1
    # TOTAL MATCHES + SEASONS
    # ============================================================

    scale_df = q("""
        SELECT
            COUNT(DISTINCT match_id) AS total_matches,
            COUNT(DISTINCT season_year) AS total_seasons
        FROM matches_clean
    """)


    total_matches = int(
        scale_df.iloc[0]["total_matches"] or 0
    )

    total_seasons = int(
        scale_df.iloc[0]["total_seasons"] or 0
    )


    # ============================================================
    # CARD 2
    # TOTAL RUNS
    # ============================================================

    try:

        total_runs_df = q(
            f"""
            SELECT
                SUM(total_runs) AS total_runs
            FROM v_ball
            WHERE season_year IN ({season_placeholders})
            """,
            tuple(selected_seasons)
        )

        total_runs = int(
            total_runs_df.iloc[0]["total_runs"] or 0
        )

    except Exception:

        total_runs = 0


    # ============================================================
    # CARD 3
    # CHASE WIN RATE
    # ============================================================

    try:

        chase_df = q(
            f"""
            SELECT

                COUNT(*) AS total_matches,

                SUM(
                    CASE
                        WHEN winner = team2
                        THEN 1
                        ELSE 0
                    END
                ) AS chase_wins

            FROM matches_clean

            WHERE season_year IN ({season_placeholders})

            AND winner IS NOT NULL
            """,
            tuple(selected_seasons)
        )

        chase_total = int(
            chase_df.iloc[0]["total_matches"] or 0
        )

        chase_wins = int(
            chase_df.iloc[0]["chase_wins"] or 0
        )

    except Exception:

        chase_total = 0
        chase_wins = 0


    if chase_total > 0:

        chase_rate = (
            chase_wins / chase_total
        )

        # Test against 50%
        z_stat = (
            (chase_rate - 0.50)
            /
            math.sqrt(
                (0.50 * 0.50)
                /
                chase_total
            )
        )

        # Two-sided normal approximation
        p_value = math.erfc(
            abs(z_stat) / math.sqrt(2)
        )

    else:

        chase_rate = 0
        p_value = 1.0


    # ============================================================
    # THREE METRIC CARDS
    # ============================================================

    card1, card2, card3 = st.columns(3)


    with card1:

        st.metric(
            "Matches Played",
            f"{total_matches:,}"
        )

        st.caption(
            f"Scale: {total_seasons} seasons"
        )


    with card2:

        st.metric(
            "Total Runs",
            f"{total_runs:,}"
        )

        st.caption(
            "Selected seasons"
        )


    with card3:

        st.metric(
            "Chase Win Rate",
            f"{chase_rate:.1%}"
        )

        st.caption(
            f"n = {chase_total:,} | p = {p_value:.4f}"
        )


    st.divider()


    # ============================================================
    # HERO VISUAL
    # AVERAGE FIRST INNINGS SCORE BY SEASON
    # ============================================================

    st.subheader(
        "Average first-innings score shows how the scoring environment has changed"
    )


    try:

        avg_score_df = q(
            f"""
            SELECT

                season_year,

                ROUND(
                    AVG(total_runs),
                    2
                ) AS average_innings_score,

                COUNT(DISTINCT match_id) AS matches

            FROM v_ball

            WHERE innings = 1

            AND season_year IN ({season_placeholders})

            GROUP BY season_year

            ORDER BY season_year
            """,
            tuple(selected_seasons)
        )

    except Exception as e:

        avg_score_df = pd.DataFrame()

        st.error(
            "Could not create average innings score chart."
        )

        st.code(str(e))


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
                "Average first-innings score by season"
            ),
            labels={
                "season_year": "Season",
                "average_innings_score":
                    "Average score"
            }
        )


        fig.add_hline(
            y=league_average,
            line_dash="dash",
            annotation_text=(
                f"League average: "
                f"{league_average:.1f}"
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


    # ============================================================
    # SUPPORTING VISUAL
    # CHASE WIN RATE BY TARGET BAND
    # ============================================================

    st.subheader(
        "Higher targets make successful chasing harder"
    )


    try:

        target_df = q(
            f"""
            WITH match_data AS (

                SELECT

                    match_id,

                    MAX(
                        CASE
                            WHEN innings = 1
                            THEN total_runs
                            ELSE 0
                        END
                    ) AS first_innings_runs

                FROM v_ball

                WHERE season_year IN ({season_placeholders})

                GROUP BY match_id

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

                COUNT(*) AS matches

            FROM match_data

            GROUP BY target_band

            ORDER BY
                CASE target_band

                    WHEN 'Below 120' THEN 1
                    WHEN '120–149' THEN 2
                    WHEN '150–179' THEN 3
                    WHEN '180–199' THEN 4
                    WHEN '200+' THEN 5

                END
            """,
            tuple(selected_seasons)
        )

    except Exception:

        target_df = pd.DataFrame()


    if not target_df.empty:

        # Calculate chase rate separately
        # using match results

        target_results = q(
            f"""
            SELECT

                m.match_id,

                m.team2,

                m.winner,

                SUM(
                    CASE
                        WHEN v.innings = 1
                        THEN v.total_runs
                        ELSE 0
                    END
                ) AS first_innings_runs

            FROM matches_clean m

            JOIN v_ball v
                ON m.match_id = v.match_id

            WHERE m.season_year IN ({season_placeholders})

            GROUP BY
                m.match_id,
                m.team2,
                m.winner
            """,
            tuple(selected_seasons)
        )


        if not target_results.empty:

            target_results["target_band"] = pd.cut(
                target_results[
                    "first_innings_runs"
                ],
                bins=[
                    -1,
                    119,
                    149,
                    179,
                    199,
                    float("inf")
                ],
                labels=[
                    "Below 120",
                    "120–149",
                    "150–179",
                    "180–199",
                    "200+"
                ]
            )


            chase_band_df = (
                target_results
                .groupby(
                    "target_band",
                    observed=False
                )
                .agg(
                    matches=("match_id", "count"),
                    chase_wins=(
                        "winner",
                        lambda x: (
                            x.notna().sum()
                        )
                    )
                )
                .reset_index()
            )


            # Correct chase wins using team2
            target_results["chase_win"] = (
                target_results["winner"]
                ==
                target_results["team2"]
            )


            chase_band_df = (
                target_results
                .groupby(
                    "target_band",
                    observed=False
                )
                .agg(
                    matches=("match_id", "count"),
                    chase_wins=("chase_win", "sum")
                )
                .reset_index()
            )


            chase_band_df["chase_win_rate"] = (
                100
                *
                chase_band_df["chase_wins"]
                /
                chase_band_df["matches"]
            )


            fig = px.bar(
                chase_band_df,
                x="target_band",
                y="chase_win_rate",
                text="chase_win_rate",
                title=(
                    "Chase win rate falls across higher target bands"
                ),
                labels={
                    "target_band": "Target band",
                    "chase_win_rate":
                        "Chase win rate (%)"
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
                "Each bar is backed by the number of matches shown."
            )


    # ============================================================
    # VISUAL 3
    # SIXES BY SEASON
    # ============================================================

    st.subheader(
        "Six-hitting has changed across IPL seasons"
    )


    try:

        sixes_df = q(
            f"""
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
            """,
            tuple(selected_seasons)
        )

    except Exception:

        sixes_df = pd.DataFrame()


    if not sixes_df.empty:

        fig = px.bar(
            sixes_df,
            x="season_year",
            y="sixes",
            text="sixes",
            title=(
                "Sixes hit by season"
            ),
            labels={
                "season_year": "Season",
                "sixes": "Sixes"
            }
        )


        fig.update_traces(
            textposition="outside"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


        st.caption(
            "n = matches represented in each season."
        )


    # ============================================================
    # VISUAL 4
    # WIN MARGIN TYPE
    # ============================================================

    st.subheader(
        "IPL matches are decided by defending or chasing"
    )


    try:

        margin_df = q(
            f"""
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

            """,
            tuple(selected_seasons)
        )

    except Exception:

        margin_df = pd.DataFrame()


    if not margin_df.empty:

        fig = px.bar(
            margin_df,
            x="margin_type",
            y="matches",
            text="matches",
            title=(
                "Matches are split between defending and chasing"
            ),
            labels={
                "margin_type": "Result type",
                "matches": "Matches"
            }
        )


        fig.update_traces(
            textposition="outside"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # ============================================================
    # VISUAL 5
    # WICKETS PER MATCH
    # ============================================================

    st.subheader(
        "Wickets per match show how match endings have changed"
    )


    try:

        wickets_df = q(
            f"""
            SELECT

                season_year,

                ROUND(
                    AVG(wickets),
                    2
                ) AS wickets_per_match,

                COUNT(*) AS matches

            FROM (

                SELECT

                    season_year,

                    match_id,

                    COUNT(
                        CASE
                            WHEN wicket_type IS NOT NULL
                            THEN 1
                        END
                    ) AS wickets

                FROM v_ball

                WHERE season_year IN ({season_placeholders})

                GROUP BY
                    season_year,
                    match_id

            )

            GROUP BY season_year

            ORDER BY season_year
            """,
            tuple(selected_seasons)
        )

    except Exception:

        wickets_df = pd.DataFrame()


    if not wickets_df.empty:

        fig = px.line(
            wickets_df,
            x="season_year",
            y="wickets_per_match",
            markers=True,
            title=(
                "Average wickets per match by season"
            ),
            labels={
                "season_year": "Season",
                "wickets_per_match":
                    "Wickets per match"
            }
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ################################################################
# TAB 2
# MATCH DETAIL
# ################################################################

with tab2:

    st.header(
        "Match Detail — One Game at a Time"
    )

    st.write(
        "Select a season and team first, then choose "
        "one match. Every element responds to that match."
    )


    # ============================================================
    # FILTER 1 — SEASON
    # ============================================================

    detail_season = st.selectbox(
        "1️⃣ Select Season",
        options=seasons,
        key="detail_season"
    )


    # ============================================================
    # FILTER 2 — TEAM
    # ============================================================

    try:

        teams_df = q("""
            SELECT team1 AS team
            FROM matches_clean

            UNION

            SELECT team2 AS team
            FROM matches_clean

            ORDER BY team
        """)

        teams = (
            teams_df["team"]
            .dropna()
            .tolist()
        )

    except Exception:

        teams = []


    if not teams:

        st.error(
            "No teams were found in matches_clean."
        )

        st.stop()


    detail_team = st.selectbox(
        "2️⃣ Select Team",
        options=teams,
        key="detail_team"
    )


    # ============================================================
    # FILTER 3 — MATCH
    # ============================================================

    try:

        match_list_df = q(
            """
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
            """,
            (
                detail_season,
                detail_team,
                detail_team
            )
        )

    except Exception as e:

        st.error(
            "Could not load matches."
        )

        st.code(str(e))

        st.stop()


    if match_list_df.empty:

        st.warning(
            "No matches found for this season and team."
        )

        st.stop()


    # Human-readable match name
    match_list_df["match_label"] = (
        match_list_df["team1"].astype(str)
        + " vs "
        + match_list_df["team2"].astype(str)
        + " — "
        + match_list_df[
            "venue_clean"
        ].fillna("Unknown venue").astype(str)
        + " — "
        + match_list_df[
            "season_year"
        ].astype(str)
    )


    selected_match_label = st.selectbox(
        "3️⃣ Select Match",
        options=match_list_df[
            "match_label"
        ].tolist(),
        key="selected_match"
    )


    selected_match_id = match_list_df.loc[
        match_list_df[
            "match_label"
        ] == selected_match_label,
        "match_id"
    ].iloc[0]


    # ============================================================
    # SELECTED MATCH INFORMATION
    # ============================================================

    match_info = q(
        """
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
        """,
        (selected_match_id,)
    )


    if match_info.empty:

        st.error(
            "Match information could not be found."
        )

        st.stop()


    match = match_info.iloc[0]


    # ============================================================
    # RESULT
    # ============================================================

    winner = match["winner"]

    win_by_runs = (
        match["win_by_runs"]
        if pd.notna(match["win_by_runs"])
        else 0
    )

    win_by_wickets = (
        match["win_by_wickets"]
        if pd.notna(match["win_by_wickets"])
        else 0
    )


    if pd.isna(winner):

        result_text = "No result"

    elif win_by_runs > 0:

        result_text = (
            f"{winner} won by "
            f"{int(win_by_runs)} runs"
        )

    elif win_by_wickets > 0:

        result_text = (
            f"{winner} won by "
            f"{int(win_by_wickets)} wickets"
        )

    else:

        result_text = (
            f"{winner} won"
        )


    # ============================================================
    # INNINGS SCORE
    # ============================================================

    try:

        innings_df = q(
            """
            SELECT

                innings,

                batting_team,

                SUM(total_runs) AS runs,

                COUNT(
                    CASE
                        WHEN wicket_type IS NOT NULL
                        THEN 1
                    END
                ) AS wickets

            FROM v_ball

            WHERE match_id = ?

            GROUP BY
                innings,
                batting_team

            ORDER BY innings
            """,
            (selected_match_id,)
        )

    except Exception:

        innings_df = pd.DataFrame()


    # ============================================================
    # THREE DETAIL CARDS
    # ============================================================

    card1, card2, card3 = st.columns(3)


    with card1:

        st.metric(
            "Match Result",
            result_text
        )


    with card2:

        if len(innings_df) >= 1:

            first_team = innings_df.iloc[0][
                "batting_team"
            ]

            first_runs = int(
                innings_df.iloc[0]["runs"]
            )

            first_wickets = int(
                innings_df.iloc[0]["wickets"]
            )

            st.metric(
                "First Innings",
                (
                    f"{first_team}: "
                    f"{first_runs}/"
                    f"{first_wickets}"
                )
            )

        else:

            st.metric(
                "First Innings",
                "No data"
            )


    with card3:

        if len(innings_df) >= 2:

            second_team = innings_df.iloc[1][
                "batting_team"
            ]

            second_runs = int(
                innings_df.iloc[1]["runs"]
            )

            second_wickets = int(
                innings_df.iloc[1]["wickets"]
            )

            st.metric(
                "Second Innings",
                (
                    f"{second_team}: "
                    f"{second_runs}/"
                    f"{second_wickets}"
                )
            )

        else:

            st.metric(
                "Second Innings",
                "No data"
            )


    st.divider()


    # ============================================================
    # HERO VISUAL
    # RUNS PER OVER
    # ============================================================

    st.subheader(
        "The innings turned at the overs where scoring separated"
    )


    try:

        over_df = q(
            """
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
            """,
            (selected_match_id,)
        )

    except Exception:

        over_df = pd.DataFrame()


    if not over_df.empty:

        over_df["innings_label"] = (
            over_df["batting_team"].astype(str)
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
                "Runs per over reveal where the match changed"
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


    # ============================================================
    # VISUAL 2
    # FOURS AND SIXES
    # ============================================================

    st.subheader(
        "The two innings produced different boundary profiles"
    )


    try:

        boundary_df = q(
            """
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
            """,
            (selected_match_id,)
        )

    except Exception:

        boundary_df = pd.DataFrame()


    if not boundary_df.empty:

        boundary_long = boundary_df.melt(
            id_vars=[
                "batting_team"
            ],
            value_vars=[
                "fours",
                "sixes"
            ],
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
                "Fours and sixes explain how the innings scored"
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


        st.caption(
            f"n = {len(boundary_long):,} boundary groups."
        )


    # ============================================================
    # TOP BATTERS
    # ============================================================

    st.subheader(
        "The leading batters show who contributed most with the bat"
    )


    try:

        top_batters_df = q(
            """
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
            """,
            (selected_match_id,)
        )

    except Exception:

        top_batters_df = pd.DataFrame()


    # ============================================================
    # TOP BOWLERS
    # ============================================================

    try:

        top_bowlers_df = q(
            """
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

            ORDER BY
                wickets DESC,
                runs_conceded ASC

            LIMIT 10
            """,
            (selected_match_id,)
        )

    except Exception:

        top_bowlers_df = pd.DataFrame()


    # ============================================================
    # DISPLAY PLAYER TABLES
    # ============================================================

    player_col1, player_col2 = st.columns(2)


    with player_col1:

        st.write(
            "### 🏏 Top Run Scorers"
        )

        if not top_batters_df.empty:

            st.dataframe(
                top_batters_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No batting data available."
            )


    with player_col2:

        st.write(
            "### 🎯 Top Wicket Takers"
        )

        if not top_bowlers_df.empty:

            st.dataframe(
                top_bowlers_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No bowling data available."
            )


    st.caption(
        "Player of the Match: "
        + str(match["player_of_match"])
    )


    # ============================================================
    # TOSS INFORMATION
    # ============================================================

    st.subheader(
        "The toss choice and match result put the game in context"
    )


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


    st.dataframe(
        toss_df,
        use_container_width=True,
        hide_index=True
    )


    # ============================================================
    # PHASE ANALYSIS
    # ============================================================

    st.subheader(
        "The scoring split shows where each innings built or lost momentum"
    )


    try:

        phase_df = q(
            """
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
            """,
            (selected_match_id,)
        )

    except Exception:

        phase_df = pd.DataFrame()


    if not phase_df.empty:

        fig = px.bar(
            phase_df,
            x="phase",
            y="runs",
            color="batting_team",
            barmode="group",
            text="runs",
            title=(
                "Scoring by phase shows where the match momentum moved"
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


        st.caption(
            f"n = {len(phase_df):,} team-phase observations."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "IPL Cricket Analytics | Domain C — Matches"
)
