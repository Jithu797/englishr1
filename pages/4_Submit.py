import streamlit as st
import time

st.title("Submit Interview")

# --- Read session info ---
candidate_id = st.session_state.get("candidate_id", "test123")
s1_results = st.session_state.get("s1_results", [])
s2_link = st.session_state.get("s2_test_link")
s2_status = st.session_state.get("status")  # set to "submitted" by Section 2 page
final_submitted = st.session_state.get("final_submitted", False)

# --- Completion checklist (non-blocking) ---
st.subheader("✅ Completion Checklist")

# Section 1 status (we can't know total questions here, so show what's available)
s1_done = bool(s1_results)  # at least one answer recorded
s1_msg = "Completed (answers recorded)" if s1_done else "Not completed yet"
st.write(f"- **Section 1:** {s1_msg}")

# Section 2 status based on your current code
s2_done = (s2_status == "submitted")
s2_msg = "Submitted" if s2_done else "Not confirmed yet"
st.write(f"- **Section 2:** {s2_msg}")

# Quick links
cols_nav = st.columns(2)
with cols_nav[0]:
    try:
        st.page_link("pages/2_Section1.py", label="⬅️ Go to Section 1")
    except Exception:
        pass
with cols_nav[1]:
    try:
        st.page_link("pages/3_Section2.py", label="Go to Section 2 ➜")
    except Exception:
        pass

st.divider()

# --- Finalize controls ---
if final_submitted:
    st.success("🎉 Your responses have already been finalized and submitted.")
    st.stop()

st.write("When you're ready, confirm and submit your interview for review.")
confirm = st.checkbox("I confirm that the information provided is accurate and I'm ready to submit.")

# Always show the button (no hard block)
if st.button("Finalize & Submit", type="primary", disabled=not confirm):
    # Package a payload you can push to Supabase later
    final_payload = {
        "candidate_id": candidate_id,
        "section1": {
            "answers": s1_results,   # each item contains transcript & evaluation
        },
        "section2": {
            "test_link": s2_link,
            "status": "submitted" if s2_done else "pending",
        },
        "submitted_at": int(time.time()),
    }

    # Keep it in session for now; you can read this in a backend/save step
    st.session_state["final_payload"] = final_payload
    st.session_state["final_submitted"] = True

    # If you already have a DB function, you can safely call it here:
    # from db.queries import save_final_submission
    # save_final_submission(candidate_id, final_payload)

    st.success("✅ Your responses have been submitted successfully.")
    st.balloons()
    st.rerun()
