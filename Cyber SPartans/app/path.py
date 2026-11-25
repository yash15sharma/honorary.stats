import json
import os
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from app.db import get_connection

router = APIRouter()

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def generate_fallback_summary(
    name: str,
    role: str,
    worker_skills: List[str],
    skill_gap: List[str],
    course_title: str,
    schemes: List[Dict[str, Any]],
    is_hindi: bool,
) -> str:
    """
    Builds a 3-sentence plain language summary in the worker's language
    when Gemini API is unavailable or fails.
    """
    skills_part = ", ".join(worker_skills[:2]) if worker_skills else (role if not is_hindi else "काम")
    gap_part = skill_gap[0] if skill_gap else ("उन्नत कौशल" if is_hindi else "advanced skills")
    scheme_part = schemes[0]["name"] if schemes else ("सरकारी योजनाओं" if is_hindi else "government schemes")

    if is_hindi:
        return (
            f"आपके पास {skills_part} का अच्छा व्यावहारिक हुनर और अनुभव है। "
            f"अपनी कमाई बढ़ाने के लिए आपका अगला कदम {gap_part} सीखना और {course_title} पूरा करना है। "
            f"आप {scheme_part} से सरकारी सहायता और मान्यता प्राप्त प्रमाण पत्र भी ले सकते हैं।"
        )
    else:
        return (
            f"You already possess proven practical skills in {skills_part}. "
            f"Your next step to boost your earnings is learning {gap_part} through the {course_title} program. "
            f"You can also access official funding and certification through {scheme_part}."
        )


def generate_gemini_summary(
    name: str,
    role_name: str,
    role_name_hi: str,
    worker_skills: List[str],
    skill_gap: List[str],
    next_course: Dict[str, Any],
    schemes: List[Dict[str, Any]],
    is_hindi: bool,
) -> str:
    """
    Calls Gemini to generate 3 short, simple sentences in the worker's language.
    Falls back gracefully if the key is missing or call fails.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key or gemini_key.startswith("your_"):
        return generate_fallback_summary(
            name, role_name, worker_skills, skill_gap, next_course["title"], schemes, is_hindi
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)
        target_lang = "Hindi" if is_hindi else "English"
        skills_str = ", ".join(worker_skills) if worker_skills else "Practical experience"
        gap_str = ", ".join(skill_gap) if skill_gap else "Advanced techniques"
        scheme_names = ", ".join([s["name"] for s in schemes])

        prompt = (
            f"You are a friendly, encouraging career counselor for informal Indian workers.\n"
            f"Write a personalized career path summary for {name}.\n"
            f"Role: {role_name} ({role_name_hi})\n"
            f"Current Skills: {skills_str}\n"
            f"Next Skills to Learn: {gap_str}\n"
            f"Recommended Course: {next_course['title']}\n"
            f"Recommended Schemes: {scheme_names}\n"
            f"Target Language: {target_lang}\n\n"
            f"CRITICAL REQUIREMENTS:\n"
            f"1. Exactly 3 short, simple, motivating sentences in {target_lang}.\n"
            f"2. Use grassroots, accessible vocabulary that an informal worker easily understands.\n"
            f"3. Sentence 1: Acknowledge what they are already skilled at.\n"
            f"4. Sentence 2: Explain their next skill learning step and course to increase income.\n"
            f"5. Sentence 3: Mention the government schemes available to assist them.\n"
            f"6. Return ONLY the 3 sentences as plain text. No bullet points, quotes, or headers."
        )

        response = client.models.generate_content(
            model=DEFAULT_GEMINI_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.3,
            ),
        )
        summary_text = (response.text or "").strip()
        # Clean up any quotes
        if summary_text.startswith('"') and summary_text.endswith('"'):
            summary_text = summary_text[1:-1].strip()

        if summary_text and len(summary_text) > 20:
            return summary_text

    except Exception as exc:
        print(f"[Gemini Summary Exception] {exc}. Using template fallback.")

    return generate_fallback_summary(
        name, role_name, worker_skills, skill_gap, next_course["title"], schemes, is_hindi
    )


# ==============================================================================
# GET /api/path/{card_id}
# ==============================================================================
@router.get("/api/path/{card_id}")
def get_path(card_id: str):
    """
    Returns the career pathway for a verified skill card:
    {
      "skill_gap": [str],
      "next_course": { "title": str, "provider": str, "duration": str, "link": str },
      "nearest_centre": { "name": str, "city": str, "link": str },
      "schemes": [ { "name": str, "reason": str, "link": str } ],
      "summary": str,
      "is_sample": true
    }
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Fetch skill card
    cursor.execute(
        """
        SELECT id, name, role_id, skills_json, years_experience, language, created_at
        FROM skill_cards
        WHERE id = ?;
        """,
        (card_id,),
    )
    card_row = cursor.fetchone()

    if not card_row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Skill card '{card_id}' not found. Please verify the card ID.",
        )

    role_id = card_row["role_id"]
    language = (card_row["language"] or "en").lower().strip()
    is_hindi = language == "hi"

    # 2. Fetch role details
    cursor.execute("SELECT id, name, name_hi FROM job_roles WHERE id = ?;", (role_id,))
    role_row = cursor.fetchone()
    role_name = role_row["name"] if role_row else "Worker"
    role_name_hi = role_row["name_hi"] if role_row else "कामगार"

    # 3. Parse current worker skills
    try:
        worker_skills = json.loads(card_row["skills_json"])
        if not isinstance(worker_skills, list):
            worker_skills = []
    except Exception:
        worker_skills = []
    worker_skills_lower = {s.lower().strip() for s in worker_skills}

    # 4. Compute skill_gap: Next-level skills that worker does not have yet
    # Compare using English names, return name_hi if language is 'hi'
    cursor.execute(
        """
        SELECT name, name_hi
        FROM skills
        WHERE role_id = ? AND level = 'next'
        ORDER BY id ASC;
        """,
        (role_id,),
    )
    next_skills_rows = cursor.fetchall()
    skill_gap = []
    for s_row in next_skills_rows:
        eng_name = s_row["name"]
        hi_name = s_row["name_hi"]
        if eng_name.lower().strip() not in worker_skills_lower:
            skill_gap.append(hi_name if is_hindi else eng_name)

    # 5. Fetch next course
    cursor.execute(
        """
        SELECT title, provider, duration, link, is_sample
        FROM courses
        WHERE role_id = ?
        LIMIT 1;
        """,
        (role_id,),
    )
    course_row = cursor.fetchone()
    if course_row:
        next_course = {
            "title": course_row["title"],
            "provider": course_row["provider"],
            "duration": course_row["duration"],
            "link": course_row["link"],
        }
        course_is_sample = bool(course_row["is_sample"])
    else:
        next_course = {
            "title": f"Advanced {role_name} Professional Certification",
            "provider": "Skill India Digital",
            "duration": "4 Weeks",
            "link": "https://www.skillindiadigital.gov.in",
        }
        course_is_sample = True

    # 6. Fetch nearest certification centre
    cursor.execute(
        """
        SELECT name, city, link, is_sample
        FROM centres
        WHERE role_id = ?
        LIMIT 1;
        """,
        (role_id,),
    )
    centre_row = cursor.fetchone()
    if centre_row:
        nearest_centre = {
            "name": centre_row["name"],
            "city": centre_row["city"],
            "link": centre_row["link"],
        }
        centre_is_sample = bool(centre_row["is_sample"])
    else:
        nearest_centre = {
            "name": "Pradhan Mantri Kaushal Kendra (PMKK)",
            "city": "New Delhi",
            "link": "https://www.skillindiadigital.gov.in",
        }
        centre_is_sample = True

    # 7. Fetch 2 to 3 schemes linked via role_schemes
    cursor.execute(
        """
        SELECT s.name, s.name_hi, s.reason, s.link, s.is_sample
        FROM schemes s
        JOIN role_schemes rs ON s.id = rs.scheme_id
        WHERE rs.role_id = ?
        ORDER BY s.id ASC
        LIMIT 3;
        """,
        (role_id,),
    )
    scheme_rows = cursor.fetchall()
    schemes = []
    schemes_is_sample = False
    for s_row in scheme_rows:
        schemes.append({
            "name": s_row["name_hi"] if is_hindi else s_row["name"],
            "reason": s_row["reason"],
            "link": s_row["link"],
        })
        if s_row["is_sample"]:
            schemes_is_sample = True

    conn.close()

    # 8. is_sample is True if any course, centre, or scheme is marked is_sample = 1
    is_sample = course_is_sample or centre_is_sample or schemes_is_sample

    # 9. Summary (Gemini or template fallback)
    summary = generate_gemini_summary(
        name=card_row["name"],
        role_name=role_name,
        role_name_hi=role_name_hi,
        worker_skills=worker_skills,
        skill_gap=skill_gap,
        next_course=next_course,
        schemes=schemes,
        is_hindi=is_hindi,
    )

    return {
        "skill_gap": skill_gap,
        "next_course": next_course,
        "nearest_centre": nearest_centre,
        "schemes": schemes,
        "summary": summary,
        "is_sample": is_sample,
    }
