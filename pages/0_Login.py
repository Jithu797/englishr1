import streamlit as st
import hashlib
from db.supabase_client import supabase

st.set_page_config(page_title="Login", page_icon="🔑", layout="centered")
st.title("🔑 Login")

role = st.radio("Login as:", ["Candidate", "Admin"])

if role == "Admin":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login as Admin"):
        if username and password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            res = supabase.table("admins").select("*").eq("username", username).eq("password_hash", password_hash).execute()
            if res.data:
                st.session_state["is_admin"] = True
                st.success("✅ Admin login successful! Redirecting...")
                st.switch_page("pages/5_Admin_Dashboard.py")
            else:
                st.error("❌ Invalid admin credentials")

else:  # Candidate login
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login as Candidate"):
        if email and password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            res = supabase.table("candidates").select("*").eq("email", email).eq("password_hash", password_hash).execute()
            if res.data:
                st.session_state["candidate_id"] = res.data[0]["candidate_id"]
                st.success("✅ Candidate login successful! Redirecting...")
                st.switch_page("pages/2_Section1.py")
            else:
                st.error("❌ Invalid candidate credentials")
