# modules/evaluator.py
from __future__ import annotations

import os
import json
import inspect
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from db.queries import save_section1  # keep import for static tools; real call uses dynamic import

__all__ = ["evaluate_section1"]

# -------------------------
# Internal state (lazy init)
# -------------------------
_GENAI = None
_MODEL = None
_MODEL_ID = None

_PREFERRED_MODELS = (
    "gemini-2.5-pro",        # best reasoning
    "gemini-2.5-flash",      # fast/cheaper
    "gemini-2.0-flash-lite", # lightweight fallback
)

# -------------------------
# Utilities
# -------------------------
def _strip_code_fences(text: str) -> str:
    """Remove ```json ...``` or ``` ...``` fences if present."""
    if not text:
        return ""
    t = text.strip()
    if not t.startswith("```"):
        return t
    parts = t.split("```", 2)
    if len(parts) == 3:
        body = parts[1]
        # Drop leading "json\n" if present
        return body.split("\n", 1)[-1] if body.lower().startswith("json") else body
    return parts[-1]

def _extract_first_json_object(s: str) -> Optional[str]:
    """
    Return the first top-level {...} JSON object substring using a brace stack.
    Handles quotes and escapes so braces inside strings don't break the count.
    """
    if not s:
        return None
    s = _strip_code_fences(s)

    depth = 0
    start = -1
    in_string = False
    escape = False
    for i, ch in enumerate(s):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        else:
            if ch == '"':
                in_string = True
                continue
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
                continue
            if ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start != -1:
                        return s[start : i + 1]
                continue
    return None

def _parse_json(text: str) -> Dict[str, Any]:
    """Try strict json.loads, else extract first JSON block via brace matching."""
    t = _strip_code_fences(text or "")
    try:
        return json.loads(t)
    except Exception:
        block = _extract_first_json_object(t)
        if block:
            return json.loads(block)
        raise ValueError("Model did not return valid JSON.")

def _coerce_scores(d: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure integer 0–10 for the five sub-scores; boolean for overall_pass; short feedback."""
    def clamp(v):
        try:
            v = int(round(float(v)))
        except Exception:
            v = 0
        return max(0, min(10, v))

    for k in ("fluency", "grammar", "vocabulary", "coherence", "relevance"):
        d[k] = clamp(d.get(k, 0))
    d["overall_pass"] = bool(d.get("overall_pass", False))
    d["feedback"] = str(d.get("feedback", "")).strip()
    return d

def _ensure_model():
    """
    Import and configure google.generativeai lazily.
    Never raise at import-time of this module.
    """
    global _GENAI, _MODEL, _MODEL_ID
    if _MODEL is not None:
        return

    # Lazy import to prevent import-time failure if package missing.
    import google.generativeai as genai  # type: ignore

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in environment (.env).")

    genai.configure(api_key=api_key)

    # Try to pick an available model; if listing fails, pick first preferred.
    try:
        available = {m.name.split("/")[-1] for m in genai.list_models()}
    except Exception:
        available = set()

    for mid in _PREFERRED_MODELS:
        if not available or mid in available:
            _MODEL_ID = mid
            break

    _MODEL = genai.GenerativeModel(
        _MODEL_ID,
        generation_config={
            "response_mime_type": "application/json",  # ask for raw JSON
            "temperature": 0.2,
            "top_p": 0.95,
        },
    )
    _GENAI = genai

# -------------------------
# DB call adapter
# -------------------------
def _save_section1_adapted(
    *,
    candidate_id: str,
    transcript: str,
    result_json: Dict[str, Any],
    avg_score: int
):
    """
    Adapt our values to your DB signature:
      transcripts   ← transcript (str)
      evaluations   ← result_json (dict)
      final_score   ← avg_score (int)
      status        ← "pass" if overall_pass else "fail"
    Only passes args that the actual function accepts.
    """
    from db import queries  # import here to avoid circulars
    fn = queries.save_section1
    sig = inspect.signature(fn)
    params = set(sig.parameters.keys())

    # Compute required fields per your signature
    payload = {
        "candidate_id": candidate_id,
        "transcripts": transcript,
        "evaluations": result_json,
        "final_score": avg_score,
        "status": "pass" if bool(result_json.get("overall_pass")) else "fail",
    }

    # Filter to accepted keys (so we don't crash if your function differs slightly)
    filtered = {k: v for k, v in payload.items() if k in params}

    # Verify required ones are present, else raise a clear error
    missing = [k for k in ("transcripts", "evaluations", "final_score", "status") if k in params and k not in filtered]
    if missing:
        raise TypeError(f"save_section1 is missing required keys after adaptation: {missing}")

    return fn(**filtered)

# -------------------------
# Public API
# -------------------------
def evaluate_section1(
    candidate_id: str,
    transcript: str,
    question: str,
    expected_answer: str,
    non_negotiables: str = ""
) -> Dict[str, Any]:
    """
    Evaluate candidate's spoken answer using Gemini 2.x and persist to DB.
    Returns the structured dict.
    """
    _ensure_model()

    prompt = f"""
You are an English interview evaluator.

Return ONLY a JSON object with keys:
{{
  "fluency": 1-10,
  "grammar": 1-10,
  "vocabulary": 1-10,
  "coherence": 1-10,
  "relevance": 1-10,
  "overall_pass": true/false,
  "feedback": "short constructive feedback"
}}

Definitions:
- fluency: flow, pacing, hesitations
- grammar: correctness of structures, tenses
- vocabulary: range/precision for the topic
- coherence: logical organization, clarity
- relevance: alignment with the asked question and expected answer

Question:
{question}

Candidate Response:
{transcript}

Expected Answer (guideline):
{expected_answer}

Non-negotiables (if any):
{non_negotiables}
""".strip()

    resp = _MODEL.generate_content(prompt)
    result = _parse_json(getattr(resp, "text", "") or "")
    result = _coerce_scores(result)

    avg_score = int(
        (result["fluency"] +
         result["grammar"] +
         result["vocabulary"] +
         result["coherence"] +
         result["relevance"]) / 5
    )

    # Save to DB with your required names
    _save_section1_adapted(
        candidate_id=candidate_id,
        transcript=transcript,
        result_json=result,
        avg_score=avg_score,
    )

    return {
        **result,
        "final_score": avg_score,
        "status": "pass" if result.get("overall_pass") else "fail",
    }
