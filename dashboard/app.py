
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Match Strategy",
    page_icon="🏏",
    layout="wide"
)

# Database path
DB = r"C:\Users\Scalefusion admin\OneDrive\Documents\OJT- SEM 3\project_3.1 sem 3\data\raw\ipl.db"


# Query helper
@st.cache_data
def q(sql, params=()):
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query(sql, con, params=params)


# Check database connection
try:
    q("SELECT 1")

except Exception as e:
    st.error("Database connection failed.")
    st.code(str(e))
    st.stop()


# Page title
st.title("🏏 IPL Match Strategy Dashboard")
st.write(
    "Analyze IPL matches, target scores, and successful chases."
)


# Sidebar filters
with st.sidebar:
    st.header("Filters")

    lo, hi = st.select_slider(
        "Season",
        options=list(range(2008, 2027)),
        value=(2008, 2026)
    )

    teams = q("""
        SELECT team1 AS team
        FROM matches_clean

        UNION

        SELECT team2 AS team
        FROM matches_clean

        ORDER BY team
    """)["team"].dropna().tolist()

    team = st.selectbox(
        "Team",
        ["All teams"] + teams
    )


# SQL conditions for selected season and team
conditions = ["m.season_year BETWEEN ? AND ?"]
params = [lo, hi]

if team != "All teams":
    conditions.append(
        "(m.team1 = ? OR m.team2 = ?)"
    )
    params.extend([team, team])

where_clause = " AND ".join(conditions)


# Chart 1: Chase success by target band
band = q(f"""
    WITH match_data AS (
        SELECT
            v.match_id,
            MAX(
                CASE
                    WHEN v.innings = 1
                    THEN v.total_runs
                END
            ) AS first_innings_runs
        FROM v_ball v
        GROUP BY v.match_id
    ),

    chase_data AS (
        SELECT
            v.match_id,
            v.batting_team AS chasing_team
        FROM v_ball v
        WHERE v.innings = 2
        GROUP BY v.match_id, v.batting_team
    )

    SELECT
        CASE
            WHEN md.first_innings_runs < 140
                THEN 'Under 140'
            WHEN md.first_innings_runs < 180
                THEN '140–179'
            ELSE '180+'
        END AS band,

        COUNT(*) AS matches,

        ROUND(
            100.0 * AVG(
                CASE
                    WHEN m.match_winner = cd.chasing_team
                    THEN 1.0
                    ELSE 0.0
                END
            ),
            1
        ) AS chase_pct,

        MIN(md.first_innings_runs) AS sort_key

    FROM match_data md

    JOIN chase_data cd
        ON md.match_id = cd.match_id

    JOIN matches_clean m
        ON md.match_id = m.match_id

    WHERE {where_clause}
      AND md.first_innings_runs IS NOT NULL
      AND m.match_winner IS NOT NULL

    GROUP BY band

    ORDER BY sort_key
""", tuple(params))


# Display chart
if not band.empty:

    fig = px.bar(
        band,
        x="band",
        y="chase_pct",
        text="matches",
        labels={
            "band": "First-innings target",
            "chase_pct": "Successful chases (%)"
        }
    )

    fig.update_traces(
        textposition="inside",
        texttemplate="%{text} matches"
    )

    fig.update_xaxes(
        categoryorder="array",
        categoryarray=band["band"].tolist()
    )

    fig.add_hline(
        y=54.5,
        line_dash="dash",
        annotation_text="Reference rate: 54.5%"
    )

    fig.update_layout(
        xaxis_title="First-innings score band",
        yaxis_title="Successful chases (%)",
        showlegend=False
    )

    st.subheader(
        "Chasing success changes with the target"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "Bar labels show the number of matches. "
        "The dashed line is a reference rate, not a "
        "calculated league average."
    )

    st.dataframe(
        band[["band", "matches", "chase_pct"]],
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning(
        "No match data found for these filters. "
        "Check the selected seasons, team, and database."
    )
