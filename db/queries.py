from db.supabase_client import supabase
import json

def save_section1(candidate_id: str, transcripts: list, evaluations: list, final_score: float, status: str):
    """Save Section 1 voice interview results."""
    supabase.table("candidates").update({
        "s1_transcript": json.dumps(transcripts),
        "s1_evaluation": json.dumps(evaluations),
        "s1_score": final_score,
        "status": status
    }).eq("candidate_id", candidate_id).execute()


def save_section2(candidate_id: str, question_id: str, answer: str, score: float = None):
    """Save Section 2 written test results."""
    supabase.table("candidates").update({
        "s2_question_id": question_id,
        "s2_answer": answer,
        "s2_score": score,
        "status": "s2_done"
    }).eq("candidate_id", candidate_id).execute()
