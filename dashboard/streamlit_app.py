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
# CHECK DATABASE CONNECTION
# ============================================================

try:

    objects_df = q("""
        SELECT
            name,
            type
        FROM sqlite_master
        WHERE type IN ('table', 'view')
        ORDER BY name
    """)

except Exception as e:

    st.error("❌ Database connection failed")

    st.code(str(e))

    st.info(
        "Make sure your project structure is:\n\n"
        "proj_3.1_ipl/\n"
        "├── data/ipl.db\n"
        "└── dashboard/app.py"
    )

    st.stop()


# ============================================================
# REQUIRED OBJECTS
# ============================================================

available_objects = set(
    objects_df["name"].tolist()
)

required_objects = [
    "matches_clean",
    "v_ball"
]

missing_objects = [
    x
    for x in required_objects
    if x not in available_objects
]

if missing_objects:

    st.error("❌ Required database objects are missing")

    for item in missing_objects:
        st.write(f"- `{item}`")

    st.write("### Available objects")

    st.dataframe(
        objects_df,
        use_container_width=True,
        hide_index=True
    )

    st.stop()


# ============================================================
# CHECK MATCHES_CLEAN COLUMNS
# ============================================================

try:

    matches_columns_df = q("""
        PRAGMA table_info(matches_clean)
    """)

    matches_columns = set(
        matches_columns_df["name"].tolist()
    )

except Exception as e:

    st.error(
        "Could not read matches_clean structure."
    )

    st.code(str(e))

    st.stop()


required_match_columns = [
    "match_id",
    "venue_clean",
    "city_clean",
    "season_year",
    "team1",
    "team2",
    "result",
    "match_winner",
    "player_of_match",
    "toss_winner",
    "toss_decision"
]

missing_match_columns = [
    col
    for col in required_match_columns
    if col not in matches_columns
]

if missing_match_columns:

    st.error(
        "❌ Your matches_clean table is missing columns:"
    )

    for col in missing_match_columns:
        st.write(f"- `{col}`")

    st.write("### Actual matches_clean columns")

    st.dataframe(
        matches_columns_df,
        use_container_width=True,
        hide_index=True
    )

    st.stop()


# ============================================================
# CHECK V_BALL COLUMNS
# ============================================================

try:

    ball_columns_df = q("""
        PRAGMA table_info(v_ball)
    """)

    ball_columns = set(
        ball_columns_df["name"].tolist()
    )

except Exception as e:

    st.error(
        "Could not read v_ball structure."
    )

    st.code(str(e))

    st.stop()


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🏏 IPL Match Analytics")

st.write(
    "Match analysis dashboard for understanding "
    "IPL scoring, results, chasing, players, toss "
    "and match momentum."
)

st.caption(
    "Domain C — Matches"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🏏 IPL Filters")

    st.write(
        "Use the controls below to explore the IPL data."
    )

    st.divider()

    st.caption(
        "Database: data/ipl.db"
    )

    st.caption(
        "Dashboard: dashboard/app.py"
    )


# ============================================================
# GET SEASONS
# ============================================================

try:

    seasons_df = q("""
        SELECT DISTINCT
            season_year
        FROM matches_clean
        WHERE season_year IS NOT NULL
        ORDER BY season_year
    """)

    seasons = (
        seasons_df["season_year"]
        .dropna()
        .tolist()
    )

except Exception as e:

    st.error(
        "Could not load seasons."
    )

    st.code(str(e))

    st.stop()


if len(seasons) == 0:

    st.error(
        "No seasons found in matches_clean."
    )

    st.stop()


# ============================================================
# TWO MAIN TABS
# ============================================================

overview_tab, detail_tab = st.tabs(
    [
        "📊 Competition Overview",
        "🏏 Match Detail"
    ]
)


# ################################################################
# TAB 1
# COMPETITION OVERVIEW
# ################################################################

with overview_tab:

    st.header(
        "Competition Overview"
    )

    st.write(
        "League-wide trends showing how IPL scoring, "
        "chasing and match outcomes have changed."
    )


    # ========================================================
    # SEASON FILTER
    # ========================================================

    selected_seasons = st.multiselect(
        "Select Season(s)",
        options=seasons,
        default=seasons,
        key="overview_seasons"
    )


    if not selected_seasons:

        st.warning(
            "Please select at least one season."
        )

        st.stop()


    placeholders = ",".join(
        ["?"] * len(selected_seasons)
    )


    # ========================================================
    # KPI 1 — MATCHES
    # ========================================================

    matches_count_df = q(
        f"""
        SELECT
            COUNT(DISTINCT match_id) AS total_matches
        FROM matches_clean
        WHERE season_year IN ({placeholders})
        """,
        tuple(selected_seasons)
    )

    total_matches = int(
        matches_count_df.iloc[0]["total_matches"]
        or 0
    )


    # ========================================================
    # KPI 2 — TOTAL RUNS
    # ========================================================

    total_runs = 0

    if "season_year" in ball_columns and "total_runs" in ball_columns:

        try:

            runs_df = q(
                f"""
                SELECT
                    SUM(total_runs) AS total_runs
                FROM v_ball
                WHERE season_year IN ({placeholders})
                """,
                tuple(selected_seasons)
            )

            total_runs = int(
                runs_df.iloc[0]["total_runs"]
                or 0
            )

        except Exception:

            total_runs = 0


    # ========================================================
    # KPI 3 — CHASE WIN RATE
    # ========================================================

    chase_rate = 0.0
    chase_wins = 0
    chase_matches = 0
    p_value = 1.0

    required_chase_columns = {
        "match_id",
        "innings",
        "batting_team",
        "match_winner"
    }

    if required_chase_columns.issubset(
        ball_columns.union(
            matches_columns
        )
    ):

        try:

            chase_df = q(
                f"""
                WITH innings_two AS (

                    SELECT
                        match_id,
                        batting_team AS chasing_team

                    FROM v_ball

                    WHERE innings = 2

                    GROUP BY
                        match_id,
                        batting_team

                )

                SELECT

                    i.match_id,

                    i.chasing_team,

                    m.match_winner

                FROM innings_two i

                JOIN matches_clean m
                    ON i.match_id = m.match_id

                WHERE m.season_year
                    IN ({placeholders})

                AND m.match_winner IS NOT NULL
                """,
                tuple(selected_seasons)
            )


            if not chase_df.empty:

                chase_df["chase_win"] = (
                    chase_df["chasing_team"]
                    ==
                    chase_df["match_winner"]
                )

                chase_matches = len(
                    chase_df
                )

                chase_wins = int(
                    chase_df["chase_win"].sum()
                )

                if chase_matches > 0:

                    chase_rate = (
                        chase_wins
                        /
                        chase_matches
                    )


                    # ------------------------------------------------
                    # Approximate two-sided test against 50%
                    # ------------------------------------------------

                    z_stat = (
                        (chase_rate - 0.50)
                        /
                        math.sqrt(
                            (0.50 * 0.50)
                            /
                            chase_matches
                        )
                    )

                    p_value = math.erfc(
                        abs(z_stat)
                        /
                        math.sqrt(2)
                    )

        except Exception:

            chase_rate = 0.0
            chase_wins = 0
            chase_matches = 0


    # ========================================================
    # THREE KPI CARDS
    # ========================================================

    card1, card2, card3 = st.columns(3)


    with card1:

        st.metric(
            "🏏 Matches Played",
            f"{total_matches:,}"
        )

        st.caption(
            f"{len(selected_seasons)} season(s) selected"
        )


    with card2:

        st.metric(
            "🏃 Total Runs",
            f"{total_runs:,}"
        )

        st.caption(
            "Selected seasons"
        )


    with card3:

        st.metric(
            "🎯 Chase Win Rate",
            f"{chase_rate:.1%}"
        )

        st.caption(
            f"n = {chase_matches:,} | "
            f"p = {p_value:.4f}"
        )


    st.divider()


    # ========================================================
    # HERO VISUAL
    # AVERAGE FIRST INNINGS SCORE
    # ========================================================

    st.subheader(
        "📈 Average first-innings score by season"
    )

    if {
        "season_year",
        "innings",
        "total_runs",
        "match_id"
    }.issubset(ball_columns):

        try:

            avg_score_df = q(
                f"""
                SELECT

                    season_year,

                    match_id,

                    SUM(total_runs)
                        AS innings_runs

                FROM v_ball

                WHERE innings = 1

                AND season_year
                    IN ({placeholders})

                GROUP BY
                    season_year,
                    match_id
                """,
                tuple(selected_seasons)
            )


            if not avg_score_df.empty:

                season_score_df = (
                    avg_score_df
                    .groupby("season_year")
                    .agg(
                        average_score=(
                            "innings_runs",
                            "mean"
                        ),
                        matches=(
                            "match_id",
                            "nunique"
                        )
                    )
                    .reset_index()
                )


                season_score_df[
                    "average_score"
                ] = season_score_df[
                    "average_score"
                ].round(2)


                league_average = (
                    season_score_df[
                        "average_score"
                    ].mean()
                )


                fig = px.line(
                    season_score_df,
                    x="season_year",
                    y="average_score",
                    markers=True,
                    text="average_score",
                    title=(
                        "Average first-innings score "
                        "shows the scoring environment"
                    ),
                    labels={
                        "season_year": "Season",
                        "average_score":
                            "Average score"
                    }
                )


                fig.add_hline(
                    y=league_average,
                    line_dash="dash",
                    annotation_text=(
                        f"Overall average: "
                        f"{league_average:.1f}"
                    )
                )


                fig.update_traces(
                    texttemplate="%{text:.1f}",
                    textposition="top center"
                )


                fig.update_layout(
                    height=500
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


                st.caption(
                    "n = matches used in each season."
                )

        except Exception as e:

            st.warning(
                "Average score chart could not be created."
            )

            st.code(str(e))

    else:

        st.info(
            "v_ball does not contain the columns "
            "required for this chart."
        )


    # ========================================================
    # CHASE WIN RATE BY TARGET BAND
    # ========================================================

    st.subheader(
        "🎯 Chase win rate by first-innings target"
    )


    if {
        "match_id",
        "innings",
        "total_runs",
        "batting_team"
    }.issubset(ball_columns):

        try:

            target_df = q(
                f"""
                WITH first_innings AS (

                    SELECT

                        match_id,

                        SUM(total_runs)
                            AS first_innings_runs

                    FROM v_ball

                    WHERE innings = 1

                    GROUP BY match_id

                ),

                second_innings AS (

                    SELECT

                        match_id,

                        batting_team
                            AS chasing_team

                    FROM v_ball

                    WHERE innings = 2

                    GROUP BY
                        match_id,
                        batting_team

                )

                SELECT

                    f.match_id,

                    f.first_innings_runs,

                    s.chasing_team,

                    m.match_winner

                FROM first_innings f

                JOIN second_innings s
                    ON f.match_id = s.match_id

                JOIN matches_clean m
                    ON f.match_id = m.match_id

                WHERE m.season_year
                    IN ({placeholders})

                AND m.match_winner IS NOT NULL
                """,
                tuple(selected_seasons)
            )


            if not target_df.empty:

                target_df["target_band"] = pd.cut(
                    target_df[
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


                target_df["chase_win"] = (
                    target_df["chasing_team"]
                    ==
                    target_df["match_winner"]
                )


                target_band_df = (
                    target_df
                    .groupby(
                        "target_band",
                        observed=False
                    )
                    .agg(
                        matches=(
                            "match_id",
                            "count"
                        ),
                        chase_wins=(
                            "chase_win",
                            "sum"
                        )
                    )
                    .reset_index()
                )


                target_band_df[
                    "chase_win_rate"
                ] = (
                    target_band_df[
                        "chase_wins"
                    ]
                    /
                    target_band_df[
                        "matches"
                    ]
                    *
                    100
                )


                fig = px.bar(
                    target_band_df,
                    x="target_band",
                    y="chase_win_rate",
                    text="chase_win_rate",
                    title=(
                        "Chasing becomes harder "
                        "as the target increases"
                    ),
                    labels={
                        "target_band":
                            "First-innings score",
                        "chase_win_rate":
                            "Chase win rate (%)"
                    }
                )


                fig.add_hline(
                    y=50,
                    line_dash="dash",
                    annotation_text="50%"
                )


                fig.update_traces(
                    texttemplate="%{text:.1f}%",
                    textposition="outside"
                )


                fig.update_layout(
                    height=500
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


                st.caption(
                    "n = matches in each target band."
                )

        except Exception as e:

            st.warning(
                "Target-band analysis could not be created."
            )

            st.code(str(e))


    # ========================================================
    # SIXES BY SEASON
    # ========================================================

    st.subheader(
        "💥 Sixes by season"
    )


    if {
        "season_year",
        "batsman_runs"
    }.issubset(ball_columns):

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
                    ) AS sixes

                FROM v_ball

                WHERE season_year
                    IN ({placeholders})

                GROUP BY season_year

                ORDER BY season_year
                """,
                tuple(selected_seasons)
            )


            if not sixes_df.empty:

                fig = px.bar(
                    sixes_df,
                    x="season_year",
                    y="sixes",
                    text="sixes",
                    title=(
                        "Total sixes hit by season"
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

        except Exception as e:

            st.warning(
                "Sixes chart could not be created."
            )

            st.code(str(e))


    # ========================================================
    # MATCH RESULT DISTRIBUTION
    # ========================================================

    st.subheader(
        "🏆 Match result distribution"
    )


    try:

        result_df = q(
            f"""
            SELECT

                COALESCE(
                    result,
                    'Unknown'
                ) AS result,

                COUNT(*) AS matches

            FROM matches_clean

            WHERE season_year
                IN ({placeholders})

            GROUP BY result

            ORDER BY matches DESC
            """,
            tuple(selected_seasons)
        )


        if not result_df.empty:

            fig = px.bar(
                result_df,
                x="result",
                y="matches",
                text="matches",
                title=(
                    "How matches ended"
                ),
                labels={
                    "result": "Result",
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

    except Exception as e:

        st.warning(
            "Result chart could not be created."
        )

        st.code(str(e))


    # ========================================================
    # WICKETS PER MATCH
    # ========================================================

    st.subheader(
        "🎯 Average wickets per match"
    )


    if {
        "season_year",
        "match_id",
        "wicket_type"
    }.issubset(ball_columns):

        try:

            wicket_match_df = q(
                f"""
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

                WHERE season_year
                    IN ({placeholders})

                GROUP BY
                    season_year,
                    match_id
                """,
                tuple(selected_seasons)
            )


            if not wicket_match_df.empty:

                wicket_season_df = (
                    wicket_match_df
                    .groupby("season_year")
                    .agg(
                        wickets_per_match=(
                            "wickets",
                            "mean"
                        ),
                        matches=(
                            "match_id",
                            "nunique"
                        )
                    )
                    .reset_index()
                )


                wicket_season_df[
                    "wickets_per_match"
                ] = wicket_season_df[
                    "wickets_per_match"
                ].round(2)


                fig = px.line(
                    wicket_season_df,
                    x="season_year",
                    y="wickets_per_match",
                    markers=True,
                    text="wickets_per_match",
                    title=(
                        "Average wickets per match "
                        "by season"
                    ),
                    labels={
                        "season_year": "Season",
                        "wickets_per_match":
                            "Wickets per match"
                    }
                )


                fig.update_traces(
                    textposition="top center"
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        except Exception as e:

            st.warning(
                "Wicket chart could not be created."
            )

            st.code(str(e))


# ################################################################
# TAB 2
# MATCH DETAIL
# ################################################################

with detail_tab:

    st.header(
        "Match Detail"
    )

    st.write(
        "Select a season, team and match to analyse "
        "one IPL game."
    )


    # ========================================================
    # FILTER 1 — SEASON
    # ========================================================

    detail_season = st.selectbox(
        "1️⃣ Select Season",
        options=seasons,
        key="detail_season"
    )


    # ========================================================
    # FILTER 2 — TEAM
    # ========================================================

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

    except Exception as e:

        st.error(
            "Could not load teams."
        )

        st.code(str(e))

        st.stop()


    if not teams:

        st.error(
            "No teams found."
        )

        st.stop()


    detail_team = st.selectbox(
        "2️⃣ Select Team",
        options=teams,
        key="detail_team"
    )


    # ========================================================
    # FILTER 3 — MATCH
    # ========================================================

    try:

        match_list_df = q(
            """
            SELECT

                match_id,

                team1,

                team2,

                venue_clean,

                city_clean,

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


    # ========================================================
    # CREATE MATCH LABEL
    # ========================================================

    match_list_df["match_label"] = (

        match_list_df[
            "team1"
        ].astype(str)

        + " vs "

        + match_list_df[
            "team2"
        ].astype(str)

        + " — "

        + match_list_df[
            "venue_clean"
        ].fillna(
            "Unknown Venue"
        ).astype(str)

        + " — "

        + match_list_df[
            "city_clean"
        ].fillna(
            "Unknown City"
        ).astype(str)
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
        ]
        ==
        selected_match_label,
        "match_id"
    ].iloc[0]


    # ========================================================
    # MATCH INFORMATION
    # ========================================================

    try:

        match_info = q(
            """
            SELECT

                match_id,

                season_year,

                team1,

                team2,

                venue_clean,

                city_clean,

                result,

                match_winner,

                player_of_match,

                toss_winner,

                toss_decision

            FROM matches_clean

            WHERE match_id = ?
            """,
            (selected_match_id,)
        )

    except Exception as e:

        st.error(
            "Could not load selected match."
        )

        st.code(str(e))

        st.stop()


    if match_info.empty:

        st.error(
            "Match information not found."
        )

        st.stop()


    match = match_info.iloc[0]


    # ========================================================
    # INNINGS SCORE
    # ========================================================

    innings_df = pd.DataFrame()


    required_innings_columns = {
        "match_id",
        "innings",
        "batting_team",
        "total_runs"
    }


    if required_innings_columns.issubset(
        ball_columns
    ):

        try:

            innings_df = q(
                """
                SELECT

                    innings,

                    batting_team,

                    SUM(total_runs)
                        AS runs,

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


    # ========================================================
    # THREE MATCH CARDS
    # ========================================================

    card1, card2, card3 = st.columns(3)


    with card1:

        st.metric(
            "🏆 Match Result",
            str(match["result"])
        )


    with card2:

        if len(innings_df) >= 1:

            first_team = (
                innings_df.iloc[0][
                    "batting_team"
                ]
            )

            first_runs = int(
                innings_df.iloc[0][
                    "runs"
                ]
            )

            first_wickets = int(
                innings_df.iloc[0][
                    "wickets"
                ]
            )

            st.metric(
                "1st Innings",
                (
                    f"{first_team}: "
                    f"{first_runs}/"
                    f"{first_wickets}"
                )
            )

        else:

            st.metric(
                "1st Innings",
                "No data"
            )


    with card3:

        if len(innings_df) >= 2:

            second_team = (
                innings_df.iloc[1][
                    "batting_team"
                ]
            )

            second_runs = int(
                innings_df.iloc[1][
                    "runs"
                ]
            )

            second_wickets = int(
                innings_df.iloc[1][
                    "wickets"
                ]
            )

            st.metric(
                "2nd Innings",
                (
                    f"{second_team}: "
                    f"{second_runs}/"
                    f"{second_wickets}"
                )
            )

        else:

            st.metric(
                "2nd Innings",
                "No data"
            )


    st.divider()


    # ========================================================
    # MATCH SUMMARY
    # ========================================================

    st.subheader(
        "📋 Match Summary"
    )


    summary_df = pd.DataFrame({

        "Information": [

            "Season",

            "Teams",

            "Venue",

            "City",

            "Toss Winner",

            "Toss Decision",

            "Match Winner",

            "Player of the Match",

            "Result"

        ],

        "Details": [

            match["season_year"],

            (
                f"{match['team1']} "
                f"vs "
                f"{match['team2']}"
            ),

            match["venue_clean"],

            match["city_clean"],

            match["toss_winner"],

            match["toss_decision"],

            match["match_winner"],

            match["player_of_match"],

            match["result"]

        ]

    })


    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # RUNS PER OVER
    # ========================================================

    st.subheader(
        "📈 Runs per over"
    )


    required_over_columns = {
        "match_id",
        "innings",
        "batting_team",
        "over",
        "total_runs"
    }


    if required_over_columns.issubset(
        ball_columns
    ):

        try:

            over_df = q(
                """
                SELECT

                    innings,

                    batting_team,

                    over,

                    SUM(total_runs)
                        AS runs

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


            if not over_df.empty:

                over_df[
                    "innings_label"
                ] = (

                    over_df[
                        "batting_team"
                    ].astype(str)

                    + " — Innings "

                    + over_df[
                        "innings"
                    ].astype(str)
                )


                fig = px.line(
                    over_df,
                    x="over",
                    y="runs",
                    color="innings_label",
                    markers=True,
                    title=(
                        "Runs scored in each over"
                    ),
                    labels={
                        "over": "Over",
                        "runs": "Runs",
                        "innings_label":
                            "Innings"
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
                    "n = overs represented in the selected match."
                )

        except Exception as e:

            st.warning(
                "Runs-per-over chart failed."
            )

            st.code(str(e))


    # ========================================================
    # BOUNDARIES
    # ========================================================

    st.subheader(
        "💥 Fours and sixes"
    )


    if {
        "match_id",
        "batting_team",
        "batsman_runs"
    }.issubset(ball_columns):

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


            if not boundary_df.empty:

                boundary_long = (
                    boundary_df
                    .melt(
                        id_vars=[
                            "batting_team"
                        ],
                        value_vars=[
                            "fours",
                            "sixes"
                        ],
                        var_name="boundary_type",
                        value_name="count"
                    )
                )


                fig = px.bar(
                    boundary_long,
                    x="batting_team",
                    y="count",
                    color="boundary_type",
                    barmode="group",
                    text="count",
                    title=(
                        "Boundary profile of the two innings"
                    ),
                    labels={
                        "batting_team": "Team",
                        "count": "Boundaries",
                        "boundary_type":
                            "Boundary"
                    }
                )


                fig.update_traces(
                    textposition="outside"
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        except Exception as e:

            st.warning(
                "Boundary chart failed."
            )

            st.code(str(e))


    # ========================================================
    # TOP BATTERS
    # ========================================================

    st.subheader(
        "🏏 Top run scorers"
    )


    required_batting_columns = {
        "match_id",
        "batter",
        "batsman_runs"
    }


    if required_batting_columns.issubset(
        ball_columns
    ):

        try:

            batter_df = q(
                """
                SELECT

                    batter,

                    SUM(batsman_runs)
                        AS runs,

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


            if not batter_df.empty:

                st.dataframe(
                    batter_df,
                    use_container_width=True,
                    hide_index=True
                )


                fig = px.bar(
                    batter_df,
                    x="batter",
                    y="runs",
                    text="runs",
                    title=(
                        "Top batters by runs"
                    ),
                    labels={
                        "batter": "Batter",
                        "runs": "Runs"
                    }
                )


                fig.update_traces(
                    textposition="outside"
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        except Exception as e:

            st.warning(
                "Batter analysis failed."
            )

            st.code(str(e))


    # ========================================================
    # TOP BOWLERS
    # ========================================================

    st.subheader(
        "🎯 Top wicket takers"
    )


    required_bowling_columns = {
        "match_id",
        "bowler",
        "wicket_type"
    }


    if required_bowling_columns.issubset(
        ball_columns
    ):

        try:

            bowler_df = q(
                """
                SELECT

                    bowler,

                    SUM(
                        CASE
                            WHEN wicket_type IS NOT NULL
                            AND LOWER(wicket_type)
                                NOT IN (
                                    'retired hurt',
                                    'obstructing the field'
                                )
                            THEN 1
                            ELSE 0
                        END
                    ) AS wickets,

                    SUM(total_runs)
                        AS runs_conceded,

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


            if not bowler_df.empty:

                st.dataframe(
                    bowler_df,
                    use_container_width=True,
                    hide_index=True
                )


                fig = px.bar(
                    bowler_df,
                    x="bowler",
                    y="wickets",
                    text="wickets",
                    title=(
                        "Top bowlers by wickets"
                    ),
                    labels={
                        "bowler": "Bowler",
                        "wickets": "Wickets"
                    }
                )


                fig.update_traces(
                    textposition="outside"
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        except Exception as e:

            st.warning(
                "Bowler analysis failed."
            )

            st.code(str(e))


    # ========================================================
    # PHASE ANALYSIS
    # ========================================================

    st.subheader(
        "⚡ Scoring by match phase"
    )


    if {
        "match_id",
        "over",
        "batting_team",
        "total_runs"
    }.issubset(ball_columns):

        try:

            phase_df = q(
                """
                SELECT

                    batting_team,

                    CASE

                        WHEN over < 6
                            THEN 'Powerplay'

                        WHEN over < 15
                            THEN 'Middle Overs'

                        ELSE 'Death Overs'

                    END AS phase,

                    SUM(total_runs)
                        AS runs

                FROM v_ball

                WHERE match_id = ?

                GROUP BY

                    batting_team,

                    phase

                ORDER BY

                    batting_team,

                    CASE

                        WHEN phase = 'Powerplay'
                            THEN 1

                        WHEN phase = 'Middle Overs'
                            THEN 2

                        ELSE 3

                    END
                """,
                (selected_match_id,)
            )


            if not phase_df.empty:

                fig = px.bar(
                    phase_df,
                    x="phase",
                    y="runs",
                    color="batting_team",
                    barmode="group",
                    text="runs",
                    title=(
                        "Runs scored in each innings phase"
                    ),
                    labels={
                        "phase": "Phase",
                        "runs": "Runs",
                        "batting_team":
                            "Batting Team"
                    }
                )


                fig.update_traces(
                    textposition="outside"
                )


                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        except Exception as e:

            st.warning(
                "Phase analysis failed."
            )

            st.code(str(e))


    # ========================================================
    # TOSS ANALYSIS
    # ========================================================

    st.subheader(
        "🪙 Toss information"
    )


    toss_df = pd.DataFrame({

        "Information": [

            "Toss Winner",

            "Toss Decision",

            "Match Winner",

            "Player of the Match"

        ],

        "Value": [

            match["toss_winner"],

            match["toss_decision"],

            match["match_winner"],

            match["player_of_match"]

        ]

    })


    st.dataframe(
        toss_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🏏 IPL Match Analytics Dashboard | "
    "Domain C — Matches"
)