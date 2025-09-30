import secrets, hashlib
from db.supabase_client import supabase

def create_candidate_account(candidate_id: str, name: str, email: str):
    """Create candidate with a password + login token. Returns creds for emailing."""
    password = secrets.token_urlsafe(8)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    token = secrets.token_urlsafe(32)

    # Upsert: if candidate exists, update creds; else insert
    existing = supabase.table("candidates").select("id").eq("email", email).execute()
    if existing.data:
        supabase.table("candidates").update({
            "candidate_id": candidate_id,
            "name": name,
            "password_hash": password_hash,
            "token": token,
            "status": "invited"
        }).eq("email", email).execute()
    else:
        supabase.table("candidates").insert({
            "candidate_id": candidate_id,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "token": token,
            "status": "invited"
        }).execute()

    return {"candidate_id": candidate_id, "email": email, "password": password, "token": token}
