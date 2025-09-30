import streamlit as st
import random
from db.queries import save_section2

st.title("Section 2: Written Assessment")

# ✅ Allow entry regardless of Section 1 status (just warn)
if not st.session_state.get("s1_results"):
    st.warning("⚠️ Section 1 isn’t completed yet. You can still proceed with Section 2.")

# 🎯 Available test links
tests = [
    "https://forms.gle/AQKxkAJb5VFjuqLq8",
    "https://forms.gle/YYnNF9dVe1cHnDh9A",
    "https://forms.gle/JiCFCWMSozAcCksK7",
]

# Candidate id (fallback for prototype)
candidate_id = st.session_state.get("candidate_id", "test123")

# 📌 Assign a test only once per session (simple)
if "s2_test_link" not in st.session_state:
    # If you prefer stable assignment per candidate (survives reloads),
    # uncomment the next 2 lines and comment the random.choice line.
    # rng = random.Random(hash(str(candidate_id)) & 0xFFFFFFFF)
    # st.session_state["s2_test_link"] = rng.choice(tests)
    st.session_state["s2_test_link"] = random.choice(tests)

# 📌 Display instructions
st.subheader("📝 Assessment Instructions")
st.markdown("""
Welcome to **Step 2 of your interview process**.

1. Ensure your internet connection is stable.  
2. If asked by the interviewer, be ready to share your screen.  
3. Click the link below to open your assigned test.  
4. After you submit the test, return here and confirm your submission.  
""")

# 🔗 Show assigned test link
st.markdown(f"👉 [Open your test in a new tab]({st.session_state['s2_test_link']})")

# Optional: navigation back to Section 1
cols = st.columns(2)
with cols[0]:
    try:
        st.page_link("pages/2_Section1.py", label="⬅️ Back to Section 1")
    except Exception:
        pass

# ✅ Confirmation button after candidate submits
with cols[1]:
    submitted = st.button("✅ I have submitted the form", type="primary", use_container_width=True)

if submitted:
    # Save a simple status; adjust signature if your DB expects different args
    save_section2(candidate_id, st.session_state["s2_test_link"], "Submitted via Google Form")
    st.session_state["status"] = "submitted"

    st.success("🎉 Thank you! Your Section 2 submission is recorded.")
    st.balloons()
