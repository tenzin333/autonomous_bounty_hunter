import streamlit as st
import pandas as pd
import psycopg2
import os
from core.config import Config

st.set_page_config(page_title="Gemini Bounty Center", layout="wide")

# Connect to the same DB the Agent uses
conn = psycopg2.connect(os.getenv("DATABASE_URL"))

st.title("Autonomous Bounty Hunter")
st.markdown("### Real-Time Security Operations Dashboard")

# Summary Metrics
df = pd.read_sql("SELECT * FROM findings", conn)
c1, c2, c3 = st.columns(3)
c1.metric("Total Vulnerabilities", len(df))
c2.metric("Active PRs", len(df[df['status'] == 'PR_Submitted']))
c3.metric("Bounties Claimed", len(df[df['status'] == 'Revealed']))

# Visualizing the Hunt
st.subheader("Latest Activity Feed")
st.dataframe(df.sort_values(by='timestamp', ascending=False), use_container_width=True)

# Interactive Map or Graph (Optional Portfolio Flair)
st.info("Agent is currently scanning")