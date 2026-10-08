import sqlite3                  # the same driver the notebooks use
import pandas as pd             # only to hold the rows a query returns
import plotly.express as px     # every chart on the page is drawn with this
import streamlit as st          # the page itself
st.set_page_config(page_title='Match strategy', layout='wide')   # wide, always
DB = r'C:\Users\Scalefusion admin\OneDrive\Documents\OJT- SEM 3\project_3.1 sem 3\data\raw\ipl.db'           # the same file the notebooks read
@st.cache_data                  # run each query once, not on every click
def q(sql, params=()):          # one helper for every query on the page
    with sqlite3.connect(DB) as con:        # opened and closed per call
        return pd.read_sql_query(sql, con, params=params)


st.title('Match strategy')                                   # a title, for now
st.write(q('SELECT COUNT(*) AS n FROM v_match_totals'))