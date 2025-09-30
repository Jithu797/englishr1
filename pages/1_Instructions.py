import streamlit as st
from utils.helpers import go_fullscreen
st.title("Instructions & Consent")

st.markdown("""
### 📌 Instructions
1. Ensure your microphone and camera are working.  
2. The interview is monitored and recorded.  
3. Section 1 will be a voice interview.  
4. Section 2 will be a written task.  

By continuing, you consent to the use of your data for evaluation.
""")

if st.button("✅ I Agree & Start Interview"):
    st.session_state["consent"] = True
    go_fullscreen()
    st.success("Fullscreen enabled! Now go to Section 1.")
