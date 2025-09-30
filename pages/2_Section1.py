import streamlit as st
import tempfile
import json
import time
from modules.transcriber import transcribe_audio_local
from modules.evaluator import evaluate_section1

st.title("Section 1: Voice Interview")

# ✅ Consent check
if "consent" not in st.session_state or not st.session_state["consent"]:
    st.error("⚠️ Please complete the Instructions page first.")
    st.stop()

# ✅ Load questions
with open("data/section1_questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

# ✅ Track progress
if "s1_current_q" not in st.session_state:
    st.session_state["s1_current_q"] = 0
if "s1_results" not in st.session_state:
    st.session_state["s1_results"] = []
if "s1_timer_start" not in st.session_state:
    st.session_state["s1_timer_start"] = None

current_q_index = st.session_state["s1_current_q"]

# ✅ Progress bar for question index
total_qs = len(questions)
st.progress(current_q_index / total_qs)
st.caption(f"Question {current_q_index+1} of {total_qs}")

# ------- Silent countdown helpers -------
MAX_TIME = 120  # seconds

def _start_timer_if_needed():
    if st.session_state["s1_timer_start"] is None:
        st.session_state["s1_timer_start"] = time.time()

def _remaining_seconds() -> int:
    elapsed = int(time.time() - st.session_state["s1_timer_start"])
    return max(0, MAX_TIME - elapsed)

def _render_silent_countdown():
    """
    Visual countdown with no numbers:
    - Shrinking progress bar
    - Subtle status text (no explicit time)
    Auto-refresh every second until time is up.
    """
    rem = _remaining_seconds()
    pct = 0.0 if MAX_TIME == 0 else rem / MAX_TIME
    st.caption("⏳ Recording window")
    st.progress(pct)  # only visual; no seconds shown

    # gently hint when very low without showing numbers
    if rem == 0:
        st.error("⏱ Time is up! Please submit your answer now.")
    else:
        # Auto-refresh every second while counting down
        time.sleep(1)
        st.rerun()

# ---------------------------------------

# ✅ Question flow
if current_q_index < total_qs:
    q = questions[current_q_index]

    st.subheader(f"Q{q['id']}: {q['question']}")
    st.caption(f"What we are testing: {', '.join(q['what_we_are_testing'])}")

    # Timer lifecycle
    _start_timer_if_needed()
    remaining = _remaining_seconds()

    # Candidate records answer
    audio_file = st.audio_input("🎤 Record your response:")

    # Buttons row
    col1, col2 = st.columns(2)
    submit_clicked = col1.button("Submit Answer", type="primary", use_container_width=True)
    reset_clicked = col2.button("Restart Question", use_container_width=True)

    if reset_clicked:
        # Reset timer & any temp state for this question
        st.session_state["s1_timer_start"] = None
        st.rerun()

    # If user hasn't submitted yet, render the silent countdown
    if not submit_clicked:
        _render_silent_countdown()

    # Handle submission
    if submit_clicked:
        if remaining <= 0:
            st.error("❌ Answer not saved. Time limit exceeded.")
            st.stop()

        if not audio_file:
            st.error("Please record your response before submitting.")
            st.stop()

        # Save locally
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.write(audio_file.getbuffer())
        temp_file.close()

        audio_url = None  # skipping upload for prototype

        # Step 1: Transcription
        transcript = transcribe_audio_local(temp_file.name)
        st.markdown("**📝 Transcript:**")
        st.write(transcript)

        # Step 2: Gemini evaluation
        eval_result = evaluate_section1(
            st.session_state.get("candidate_id", "test123"),
            transcript,
            q["question"],
            " | ".join(q["expected_answer"]),
            q.get("non_negotiables", "")
        )

        # Save result
        st.session_state["s1_results"].append({
            "question_id": q["id"],
            "question": q["question"],
            "transcript": transcript,
            "evaluation": eval_result,
            "audio_url": audio_url
        })

        # Reset timer & go next
        st.session_state["s1_timer_start"] = None
        st.session_state["s1_current_q"] += 1
        st.rerun()

# ✅ End of section
else:
    st.success("🎉 You have completed all Section 1 questions!")
    st.subheader("📊 Summary of Your Interview")

    for r in st.session_state["s1_results"]:
        st.markdown(f"**Q{r['question_id']}: {r['question']}**")
        if r["audio_url"]:
            st.audio(r["audio_url"])
        st.markdown(f"Transcript: {r['transcript']}")
        st.json(r["evaluation"])
