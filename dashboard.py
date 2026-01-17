import streamlit as st
import pandas as pd
import psycopg2
import os
from core.config import Config
from onchain.script.strike_bounty import strike_bounty  # Import your Web3 logic

# ⚙️ Page Configuration
st.set_page_config(
    page_title="Autonomous Bounty Hunter Dashboard", 
    page_icon="🛡️", 
    layout="wide"
)

# 🔗 Database Connection
@st.cache_resource
def get_db_connection():
    return psycopg2.connect(Config.DATABASE_URL)

conn = get_db_connection()

# 🔄 Auto-refresh UI every 60 seconds
st.fragment(run_every="60s")
def main():
    st.title("🛡️ Autonomous Bounty Hunter")
    st.markdown("### Real-Time Security Operations Dashboard")

    # 📊 Load Data
    query = "SELECT id, repo, vuln_type, pr_url, commit_hash, status, timestamp, secret_hash FROM findings"
    df = pd.read_sql(query, conn)

    # 📈 Summary Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Vulnerabilities", len(df))
    c2.metric("Active PRs", len(df[df['status'] == 'PR_Submitted']))
    c3.metric("Bounties Claimed", len(df[df['status'] == 'Revealed']), delta="Live", delta_color="normal")

    # 🎯 Action Center (The "Striker")
    st.divider()
    st.subheader("🎯 Ready to Strike")
    
    # We look for PRs that are submitted but not yet 'Revealed' on-chain
    pending = df[df['status'] == 'PR_Submitted']
    
    if pending.empty:
        st.info("No bounties currently eligible for striking. The agent is still hunting.")
    else:
        for _, row in pending.iterrows():
            with st.expander(f"📦 {row['repo']} - {row['vuln_type']}"):
                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.write(f"**PR Link:** {row['pr_url']}")
                    st.write(f"**Commit Hash:** `{row['commit_hash']}`")
                with col_btn:
                    if st.button("Claim Bounty", key=f"strike_{row['id']}"):
                        with st.spinner("Broadcasting to Blockchain..."):
                            try:
                                # Trigger Web3 transaction
                                tx_hash = strike_bounty(row['id'], row['secret_hash'])
                                
                                # Update Database
                                with conn.cursor() as cur:
                                    cur.execute(
                                        "UPDATE findings SET status = 'Revealed' WHERE id = %s", 
                                        (row['id'],)
                                    )
                                conn.commit()
                                
                                st.success(f"Success! Tx: {tx_hash[:10]}...")
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Transaction Failed: {e}")

    # 📜 Latest Activity Feed
    st.divider()
    st.subheader("🕵️ Recent Hunt Activity")
    
    # Using column_config to make the PR links clickable in the table
    st.dataframe(
        df.sort_values(by='timestamp', ascending=False),
        column_config={
            "pr_url": st.column_config.LinkColumn("Pull Request"),
            "commit_hash": st.column_config.TextColumn("On-Chain Proof"),
        },
        hide_index=True,
        use_container_width=True
    )

if __name__ == "__main__":
    main()