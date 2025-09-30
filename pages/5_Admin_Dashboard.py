import streamlit as st
from db.supabase_client import supabase
import json
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("📊 Admin Dashboard – Candidate Overview")

# Fetch candidates
response = supabase.table("candidates").select("*").execute()
candidates = response.data if response.data else []

if not candidates:
    st.warning("⚠️ No candidate records found.")
    st.stop()

# Flatten function for export
def flatten_candidate(c):
    eval_data = None
    try:
        if c.get("s1_evaluation"):
            eval_data = c["s1_evaluation"]
            if isinstance(eval_data, str):
                eval_data = json.loads(eval_data)
    except:
        eval_data = None

    return {
        "Candidate ID": c.get("candidate_id"),
        "Name": c.get("name"),
        "Email": c.get("email"),
        "Status": c.get("status"),
        "Final S1 Score": c.get("s1_score"),
        "S1 Result": "PASS" if c.get("status") == "s1_pass" else "FAIL" if c.get("status") == "s1_fail" else "N/A",
        "S1 Transcripts": c.get("s1_transcript"),
        "S1 Evaluation JSON": json.dumps(eval_data) if eval_data else None,
        "S2 Test Link": c.get("s2_question_id"),
        "S2 Answer": c.get("s2_answer"),
        "S2 Score": c.get("s2_score"),
        "Created At": c.get("created_at"),
    }

flat_data = [flatten_candidate(c) for c in candidates]
df = pd.DataFrame(flat_data)

# Show preview
st.dataframe(df, width="stretch")

# --- Export buttons ---
csv_data = df.to_csv(index=False).encode("utf-8")

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="Candidates")
excel_data = excel_buffer.getvalue()

st.download_button(
    label="⬇️ Download as CSV",
    data=csv_data,
    file_name="candidates_report.csv",
    mime="text/csv",
    key="csv_export",
    help="Download candidate data in CSV format",
)

st.download_button(
    label="⬇️ Download as Excel",
    data=excel_data,
    file_name="candidates_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="excel_export",
    help="Download candidate data in Excel format",
)




if "is_admin" not in st.session_state or not st.session_state["is_admin"]:
    st.error("⛔ Unauthorized – Please login as Admin")
    st.stop()

