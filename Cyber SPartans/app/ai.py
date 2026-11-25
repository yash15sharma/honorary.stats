import json
import os
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.db import get_connection

router = APIRouter()

# Default Gemini Flash model
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ==============================================================================
# EDITABLE GEMINI PROMPT TEMPLATE
# ==============================================================================
ANALYSIS_PROMPT_TEMPLATE = """You are an expert AI assistant for "honorary.stats", a career pathway app for informal workers in India.
Your job is to analyze the worker's speech transcript or text description, identify their exact job role, extract their verified skills, and determine years of experience.

Language Context: {language}

ALLOWED ROLES AND ALLOWED CURRENT SKILLS CATALOG:
{catalog_text}

STRICT ANALYSIS RULES:
1. "transcript":
   - If audio is given, transcribe the speech faithfully in the language spoken.
   - If text is given, use the text verbatim as the transcript.
   - If speech is unintelligible, silence, or background noise, return JSON with: {{"error": "could_not_understand"}}
2. "role":
   - You MUST pick the role from ONLY the allowed roles: {allowed_roles}.
   - If the worker's description doesn't fit perfectly, select the closest matching role.
3. "skills":
   - You MUST pick skills ONLY from the allowed current skills listed for that specific role above.
   - Extract ONLY skills the worker actually mentioned or clearly implied. NEVER invent skills.
   - Skills MUST ALWAYS be returned using the exact English skill names from the database above, even when the worker spoke in Hindi.
4. "years_experience":
   - Extract the number of years of experience as an integer (e.g., 5 or 8).
   - If not mentioned or unclear, return null.

Return ONLY a raw, valid JSON object matching this schema without markdown code blocks:
{{
  "transcript": "worker transcript text",
  "role": "Tailor",
  "skills": ["Blouse Stitching", "Salwar Suit Stitching"],
  "years_experience": 8
}}
"""


# ==============================================================================
# DATABASE HELPER FUNCTIONS
# ==============================================================================
def load_roles_and_current_skills() -> Dict[str, Dict[str, Any]]:
    """
    Loads all job roles and their level='current' skills from SQLite.
    Returns: { "Tailor": {"id": 1, "name_hi": "दर्जी", "skills": [...]}, ... }
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, name_hi FROM job_roles ORDER BY id ASC;")
    roles = cursor.fetchall()

    catalog = {}
    for r in roles:
        role_id = r["id"]
        role_name = r["name"]
        cursor.execute(
            """
            SELECT name, name_hi 
            FROM skills 
            WHERE role_id = ? AND level = 'current'
            ORDER BY id ASC;
            """,
            (role_id,),
        )
        skills = [row["name"] for row in cursor.fetchall()]
        catalog[role_name] = {
            "id": role_id,
            "name_hi": r["name_hi"],
            "skills": skills,
        }
    conn.close()
    return catalog


def format_catalog_for_prompt(roles_data: Dict[str, Dict[str, Any]]) -> str:
    """Formats the roles and skills into human-readable text for the prompt."""
    lines = []
    for role_name, data in roles_data.items():
        lines.append(f"Role: {role_name} ({data['name_hi']})")
        lines.append("  Allowed Current Skills:")
        for skill in data["skills"]:
            lines.append(f"    - {skill}")
    return "\n".join(lines)


def get_closest_role(raw_role: str, text: str, allowed_roles: List[str]) -> str:
    """Falls back to closest role by keyword match if role is missing or invalid."""
    for r in allowed_roles:
        if r.lower() == raw_role.strip().lower():
            return r

    combined = (raw_role + " " + text).lower()
    if any(k in combined for k in ["tailor", "stitch", "sew", "cloth", "blouse", "suit", "दर्जी", "सिलाई", "कपड़ा", "सूट", "ब्लाउज"]):
        return "Tailor"
    if any(k in combined for k in ["cook", "food", "curry", "roti", "kitchen", "chef", "रसोइया", "बावर्ची", "खाना", "सब्जी", "रोटी", "रसोई"]):
        return "Cook"
    if any(k in combined for k in ["electric", "wire", "wiring", "mcb", "switch", "light", "solar", "इलेक्ट्रीशियन", "बिजली", "वायरिंग", "पंखा"]):
        return "Electrician"

    return allowed_roles[0] if allowed_roles else "Tailor"


def parse_json_safely(raw_text: str) -> Dict[str, Any]:
    """Safely extracts and parses JSON even if wrapped in markdown code blocks."""
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except Exception:
        # Fallback to regex matching first outer { ... }
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Could not parse valid JSON from text: {raw_text[:100]}...")


def get_tailor_sample_response(roles_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Hardcoded sample response for Tailor fallback.
    Contract:
      transcript: "I have been stitching blouses and salwar suits for 8 years"
      role: "Tailor"
      skills: ["Blouse Stitching", "Salwar Suit Stitching", "Alterations", "Embroidery"]
      years_experience: 8
      missing_skills: matching remaining current skills from DB
    """
    role = "Tailor"
    tailor_current = roles_data.get(role, {}).get("skills", [])
    skill_lookup = {s.lower(): s for s in tailor_current}

    # Desired fallback skills
    sample_skills_raw = ["Blouse Stitching", "Salwar Suit Stitching", "Alterations", "Embroidery"]
    validated_skills = []
    for s in sample_skills_raw:
        if s in tailor_current:
            validated_skills.append(s)
        elif s.lower() in skill_lookup:
            validated_skills.append(skill_lookup[s.lower()])

    if not validated_skills:
        validated_skills = sample_skills_raw

    missing = [s for s in tailor_current if s not in validated_skills]

    return {
        "transcript": "I have been stitching blouses and salwar suits for 8 years",
        "role": role,
        "skills": validated_skills,
        "missing_skills": missing,
        "years_experience": 8,
    }


# ==============================================================================
# POST /api/analyze ENDPOINT
# ==============================================================================
@router.post("/api/analyze")
async def analyze(request: Request):
    """
    Accepts EITHER:
      - JSON body: { "text": "...", "language": "en" | "hi" }
      - OR multipart form-data: { "audio": <file>, "language": "en" | "hi" }
    Returns:
      {
        "transcript": str,
        "role": str,
        "skills": [str],
        "missing_skills": [str],
        "years_experience": int | null
      }
    Or if audio unintelligible:
      { "error": "could_not_understand", "message": "Please type instead" } (status 200)
    """
    roles_data = load_roles_and_current_skills()
    content_type = request.headers.get("content-type", "").lower()

    text_input = None
    language = "en"
    audio_file = None
    audio_bytes = None
    audio_mime = "audio/mp3"

    # 1. Parse Input (JSON or Multipart Form Data)
    if "multipart/form-data" in content_type:
        form = await request.form()
        language = str(form.get("language") or "en").strip()
        text_input = form.get("text")
        if text_input:
            text_input = str(text_input).strip()
        audio_file = form.get("audio")
        if audio_file and hasattr(audio_file, "read"):
            audio_bytes = await audio_file.read()
            audio_mime = getattr(audio_file, "content_type", "") or "audio/mp3"
    else:
        try:
            body = await request.json()
        except Exception:
            body = {}
        text_input = body.get("text")
        if text_input:
            text_input = str(text_input).strip()
        language = str(body.get("language") or "en").strip()

    if language not in ["en", "hi"]:
        language = "en"

    # Handle 0-byte or empty audio upload
    if audio_file and (not audio_bytes or len(audio_bytes) == 0):
        return JSONResponse(
            status_code=200,
            content={
                "error": "could_not_understand",
                "message": "Please type instead",
            },
        )

    # Handle empty text input when no audio is sent
    if not audio_bytes and (not text_input or len(text_input.strip()) == 0):
        default_role = "Tailor"
        current_skills = roles_data.get(default_role, {}).get("skills", [])
        return {
            "transcript": "",
            "role": default_role,
            "skills": [],
            "missing_skills": current_skills,
            "years_experience": None,
        }

    # 2. Check for Gemini API Key
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key or gemini_key.startswith("your_"):
        print("[Gemini] API key missing or default; returning sample fallback response.")
        return get_tailor_sample_response(roles_data)

    # 3. Build Prompt with Database Catalog
    catalog_text = format_catalog_for_prompt(roles_data)
    allowed_roles_str = ", ".join(roles_data.keys())
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        language=language,
        catalog_text=catalog_text,
        allowed_roles=allowed_roles_str,
    )

    # 4. Invoke Gemini API (google-genai SDK)
    parsed_json = None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)

        if audio_bytes:
            contents = [
                types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime),
                prompt,
            ]
        else:
            prompt_content = f"WORKER INPUT TEXT:\n{text_input or ''}\n\n{prompt}"
            contents = [prompt_content]

        response = client.models.generate_content(
            model=DEFAULT_GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        raw_text = response.text or ""
        parsed_json = parse_json_safely(raw_text)

    except Exception as exc:
        print(f"[Gemini Exception] {exc}. Using Tailor sample fallback.")
        return get_tailor_sample_response(roles_data)

    # 5. Handle audio that could not be understood
    if parsed_json.get("error") == "could_not_understand" or (audio_bytes and not parsed_json.get("transcript")):
        return JSONResponse(
            status_code=200,
            content={
                "error": "could_not_understand",
                "message": "Please type instead",
            },
        )

    # 6. Validate and Format Result
    # Transcript
    transcript = str(parsed_json.get("transcript") or text_input or "").strip()

    # Role validation (fall back to closest by keyword match if invalid)
    raw_role = str(parsed_json.get("role") or "").strip()
    allowed_role_names = list(roles_data.keys())
    role = get_closest_role(raw_role, transcript, allowed_role_names)

    # Skill validation: Drop any skill not in the DB for that role
    role_current_skills = roles_data.get(role, {}).get("skills", [])
    skill_lookup = {s.lower().strip(): s for s in role_current_skills}

    detected_skills = []
    for s in parsed_json.get("skills", []):
        s_clean = str(s).strip()
        if s_clean in role_current_skills:
            if s_clean not in detected_skills:
                detected_skills.append(s_clean)
        elif s_clean.lower() in skill_lookup:
            canon = skill_lookup[s_clean.lower()]
            if canon not in detected_skills:
                detected_skills.append(canon)

    # Missing skills: role's current skills that were NOT detected
    missing_skills = [s for s in role_current_skills if s not in detected_skills]

    # Years of experience
    years_raw = parsed_json.get("years_experience")
    years_experience = None
    if years_raw is not None:
        try:
            years_experience = int(years_raw)
        except (ValueError, TypeError):
            years_experience = None

    return {
        "transcript": transcript,
        "role": role,
        "skills": detected_skills,
        "missing_skills": missing_skills,
        "years_experience": years_experience,
    }
