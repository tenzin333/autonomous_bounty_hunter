from onchain.script.strike_bounty import strike_bounty  # Import your logic

# ... (your existing metrics and dataframe code) ...

st.divider()
st.subheader("🎯 Action Center")

# Filter for items that are potentially ready to be struck
# We check if status is 'PR_Submitted' (or your equivalent for 'not yet struck')
pending_actions = df[df['status'] == 'PR_Submitted']

if pending_actions.empty:
    st.write("No pending bounties to strike. Keep hunting!")
else:
    for _, row in pending_actions.iterrows():
        with st.expander(f"Action Required: {row['repo']} - {row['vuln_type']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**PR URL:** {row['pr_url']}")
                st.write(f"**On-chain Hash:** `{row['commit_hash']}`")
            
            with col2:
                # This button triggers your Web3 logic!
                if st.button("Strike Bounty", key=f"btn_{row['id']}"):
                    with st.spinner("Executing Smart Contract Call..."):
                        try:
                            # 1. Call the function
                            tx_hash = strike_bounty(row['id'], "YOUR_SECRET_OR_LOGIC")
                            
                            # 2. Update the Database so it disappears from 'Pending'
                            with conn.cursor() as cur:
                                cur.execute(
                                    "UPDATE findings SET status = 'Revealed' WHERE id = %s", 
                                    (row['id'],)
                                )
                            conn.commit()
                            
                            st.success(f"Claimed! Tx: {tx_hash[:10]}...")
                            st.balloons()
                            st.rerun() # Refresh UI to update metrics
                        except Exception as e:
                            st.error(f"Error: {e}")