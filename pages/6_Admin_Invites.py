import streamlit as st
import pandas as pd
import secrets
from modules.auth import create_candidate_account
from modules.emailer import send_invite

st.set_page_config(page_title="Admin – CSV Invites", layout="wide")
st.title("📨 Admin – Upload CSV & Send Invites")

st.markdown("""
### 📌 Instructions
- Upload a CSV file with columns: **candidate_id, name, email**
- Example:
candidate_id,name,email
C-001,Jane Doe,jane@example.com
C-002,John Smith,john@example.com
- If `candidate_id` is left blank, the system will auto-generate one.
- For prototype, process **10–20 candidates at once**.
""")

uploaded = st.file_uploader("Upload candidates.csv", type=["csv"])

if "invite_df" not in st.session_state:
    st.session_state["invite_df"] = None

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded).fillna("")
        missing_cols = [c for c in ["candidate_id", "name", "email"] if c not in df.columns]
        if missing_cols:
            st.error(f"❌ CSV missing required columns: {missing_cols}")
        else:
            def ensure_id(x):
                return str(x).strip() if str(x).strip() else f"C-{secrets.token_hex(3).upper()}"
            df["candidate_id"] = df["candidate_id"].apply(ensure_id)

            st.session_state["invite_df"] = df
            st.success("✅ CSV parsed successfully. Preview below:")
            st.dataframe(df, width="stretch")
    except Exception as e:
        st.error(f"❌ Failed to parse CSV: {e}")

if st.session_state["invite_df"] is not None:
    col1, col2 = st.columns([1, 1])
    with col1:
        do_create = st.button("1️⃣ Create/Update Accounts (No Emails)")
    with col2:
        do_send = st.button("2️⃣ Create/Update + Send Invites")

    results = []
    if do_create or do_send:
        df = st.session_state["invite_df"]
        with st.spinner("Processing candidates..."):
            for _, row in df.iterrows():
                cid = str(row["candidate_id"]).strip()
                name = str(row["name"]).strip()
                email = str(row["email"]).strip()

                try:
                    creds = create_candidate_account(cid, name, email)
                    if do_send:
                        send_invite(
                            email=email,
                            name=name,
                            candidate_id=creds["candidate_id"],
                            password=creds["password"],
                            token=creds["token"]
                        )
                    results.append({
                        "candidate_id": creds["candidate_id"],
                        "name": name,
                        "email": email,
                        "email_sent": "Yes" if do_send else "No",
                        "status": "✅ OK"
                    })
                except Exception as e:
                    results.append({
                        "candidate_id": cid,
                        "name": name,
                        "email": email,
                        "email_sent": "No",
                        "status": f"❌ ERROR: {e}"
                    })

        st.subheader("📊 Run Results")
        st.dataframe(pd.DataFrame(results), width="stretch")
        st.success("✅ Done")


if "is_admin" not in st.session_state or not st.session_state["is_admin"]:
    st.error("⛔ Unauthorized – Please login as Admin")
    st.stop()
