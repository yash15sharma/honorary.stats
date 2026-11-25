import os
import sys
import re
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response

# Add repository root to sys.path so root modules (skill_card, extras_helper, etc.) import cleanly
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db import get_connection

try:
    import skill_card
except ImportError:
    skill_card = None

router = APIRouter()

GENERATED_CARDS_DIR = REPO_ROOT / "generated_cards"
GENERATED_CARDS_DIR.mkdir(parents=True, exist_ok=True)


def map_role_to_id(conn, role_str: str) -> int:
    """
    Maps an English, Hindi, or Kannada role string to a valid role_id in `job_roles`.
    If no match, returns a safe fallback role_id (e.g. 1) to avoid foreign key errors.
    """
    clean_role = (role_str or "").strip().lower()
    
    # Direct keyword matching
    if any(k in clean_role for k in ["tailor", "दर्जी", "ಟೈಲರ್", "दर्जि", "stitching", "sewing"]):
        role_name = "Tailor"
    elif any(k in clean_role for k in ["cook", "रसोइया", "अಡುಗೆ", "chef", "catering", "खाना"]):
        role_name = "Cook"
    elif any(k in clean_role for k in ["electric", "इलेक्ट्रीशियन", "ವಿದ್ಯುತ್", "ವೈರಿಂಗ್", "वायरिंग"]):
        role_name = "Electrician"
    else:
        role_name = None

    if role_name:
        row = conn.execute("SELECT id FROM job_roles WHERE name = ? LIMIT 1", (role_name,)).fetchone()
        if row:
            return row["id"]

    # Fallback: find closest role or default to 1
    first_row = conn.execute("SELECT id FROM job_roles LIMIT 1").fetchone()
    return first_row["id"] if first_row else 1


def is_safe_card_id(card_id: str) -> bool:
    """Validates that card_id contains only alphanumeric, hyphen, or underscore characters."""
    return bool(card_id and re.match(r"^[A-Za-z0-9_\-]+$", card_id))


@router.post("/api/card")
async def create_card(request: Request):
    """
    Creates or registers a verified skill card.
    Contract: { name, role, skills:[str], years_experience:int, language }
    Returns: { card_id, image_url, download_url, qr_data_uri, public_card_url, whatsapp_url }
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    name = str(body.get("name") or "Worker").strip()
    role = str(body.get("role") or "Tailor").strip()
    skills = body.get("skills")
    if not isinstance(skills, list):
        skills = [str(skills)] if skills else ["Vocational Skills"]
    
    years_exp = body.get("years_experience")
    try:
        years_exp = int(years_exp) if years_exp is not None else 5
    except (ValueError, TypeError):
        years_exp = 5

    language = str(body.get("language") or "en").strip().lower()
    if language not in ("en", "hi", "kn"):
        language = "en"

    # Generate unique card ID or use provided if valid
    provided_id = str(body.get("card_id") or "").strip()
    if is_safe_card_id(provided_id):
        card_id = provided_id
    else:
        card_id = f"WKR-{datetime.utcnow().strftime('%y%m')}-{uuid.uuid4().hex[:4].upper()}"

    # Connect to SQLite and persist the worker card
    conn = get_connection()
    try:
        role_id = map_role_to_id(conn, role)
        
        # Look up upskilling details for card rendering
        course_row = conn.execute("SELECT title FROM courses WHERE role_id = ? LIMIT 1", (role_id,)).fetchone()
        next_course = course_row["title"] if course_row else "Vocational Skill Certification"

        centre_row = conn.execute("SELECT name, city FROM centres WHERE role_id = ? LIMIT 1", (role_id,)).fetchone()
        if centre_row:
            nearest_centre = f"{centre_row['name']}, {centre_row['city']}"
        else:
            nearest_centre = "Pradhan Mantri Kaushal Kendra (PMKK)"

        # Upsert into skill_cards table
        conn.execute(
            """
            INSERT INTO skill_cards (id, name, role_id, skills_json, years_experience, language, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                role_id = excluded.role_id,
                skills_json = excluded.skills_json,
                years_experience = excluded.years_experience,
                language = excluded.language,
                created_at = excluded.created_at
            """,
            (
                card_id,
                name,
                role_id,
                json.dumps(skills, ensure_ascii=False),
                years_exp,
                language,
                datetime.utcnow().isoformat(),
            )
        )
        conn.commit()
    finally:
        conn.close()

    # Determine public card URL from environment or request base_url
    public_base = (os.getenv("SKILL_CARD_BASE_URL") or os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if not public_base:
        public_base = str(request.base_url).rstrip("/")
    public_card_url = f"{public_base}/verify/{card_id}"

    card_data = {
        "card_id": card_id,
        "worker_name": name,
        "language": language,
        "matched_role": role,  # Prints exact user typed role on PNG
        "confirmed_skills": skills,
        "next_course": next_course,
        "nearest_centre": nearest_centre,
        "public_card_url": public_card_url,
    }

    # Generate Image & QR using root skill_card.py if available
    qr_data_uri = ""
    whatsapp_url = ""

    if skill_card:
        try:
            skill_card.generate_skill_card_image(card_data, output_dir=str(GENERATED_CARDS_DIR))
        except Exception as e:
            print(f"[Card] Note on PNG card generation: {e}")

        try:
            qr_data_uri = skill_card.generate_qr_base64(public_card_url)
        except Exception as e:
            print(f"[Card] Note on QR generation: {e}")

        try:
            whatsapp_url = skill_card.create_whatsapp_share_link(card_data)
        except Exception as e:
            print(f"[Card] Note on WhatsApp link: {e}")

    if not whatsapp_url:
        import urllib.parse
        msg = f"honorary.stats Skill Card\nName: {name}\nRole: {role}\nVerify: {public_card_url}"
        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(msg)}"

    return {
        "card_id": card_id,
        "image_url": f"/api/card/{card_id}/image",
        "download_url": f"/api/card/{card_id}/download",
        "qr_data_uri": qr_data_uri,
        "public_card_url": public_card_url,
        "whatsapp_url": whatsapp_url,
    }


@router.get("/api/card/{card_id}")
def get_card(card_id: str, request: Request):
    """Returns saved worker card details."""
    if not is_safe_card_id(card_id):
        raise HTTPException(status_code=400, detail="Invalid card ID format")

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT c.*, r.name as role_name, r.name_hi as role_name_hi
            FROM skill_cards c
            LEFT JOIN job_roles r ON c.role_id = r.id
            WHERE c.id = ?
            LIMIT 1
            """,
            (card_id,)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Skill card not found")

        skills = json.loads(row["skills_json"]) if row["skills_json"] else []
        public_base = (os.getenv("SKILL_CARD_BASE_URL") or os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
        if not public_base:
            public_base = str(request.base_url).rstrip("/")
        public_url = f"{public_base}/verify/{card_id}"

        return {
            "card_id": row["id"],
            "name": row["name"],
            "role": row["role_name"] or "Informal Worker",
            "skills": skills,
            "years_experience": row["years_experience"],
            "language": row["language"],
            "image_url": f"/api/card/{card_id}/image",
            "download_url": f"/api/card/{card_id}/download",
            "public_card_url": public_url,
        }
    finally:
        conn.close()


@router.get("/api/card/{card_id}/image")
def get_card_image(card_id: str):
    """Serves generated PNG card image."""
    if not is_safe_card_id(card_id):
        raise HTTPException(status_code=400, detail="Invalid card ID")

    image_path = GENERATED_CARDS_DIR / f"{card_id}.png"
    if image_path.exists():
        return FileResponse(image_path, media_type="image/png")

    # If image does not exist yet, attempt to regenerate from DB
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM skill_cards WHERE id = ? LIMIT 1", (card_id,)).fetchone()
        if row and skill_card:
            skills = json.loads(row["skills_json"]) if row["skills_json"] else []
            card_data = {
                "card_id": card_id,
                "worker_name": row["name"],
                "language": row["language"] or "en",
                "matched_role": "Worker",
                "confirmed_skills": skills,
                "next_course": "Vocational Course",
                "nearest_centre": "Skill Hub",
                "public_card_url": f"https://honorary.stats/verify/{card_id}",
            }
            skill_card.generate_skill_card_image(card_data, output_dir=str(GENERATED_CARDS_DIR))
            if image_path.exists():
                return FileResponse(image_path, media_type="image/png")
    except Exception as e:
        print(f"[Card Image] Regenerate notice: {e}")
    finally:
        conn.close()

    raise HTTPException(status_code=404, detail="Skill card image not found")


@router.get("/api/card/{card_id}/download")
def download_card_image(card_id: str):
    """Downloads PNG card as an attachment."""
    if not is_safe_card_id(card_id):
        raise HTTPException(status_code=400, detail="Invalid card ID")

    image_path = GENERATED_CARDS_DIR / f"{card_id}.png"
    if image_path.exists():
        return FileResponse(
            image_path,
            media_type="image/png",
            filename=f"skill_card_{card_id}.png"
        )
    return get_card_image(card_id)


@router.get("/api/card/{card_id}/qr.png")
def get_card_qr(card_id: str, request: Request):
    """Returns raw PNG QR code image."""
    if not is_safe_card_id(card_id):
        raise HTTPException(status_code=400, detail="Invalid card ID")

    public_base = (os.getenv("SKILL_CARD_BASE_URL") or os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if not public_base:
        public_base = str(request.base_url).rstrip("/")
    public_url = f"{public_base}/verify/{card_id}"

    try:
        import qrcode
        import io
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(public_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception:
        raise HTTPException(status_code=500, detail="QR generation unavailable")


@router.get("/verify/{card_id}", response_class=HTMLResponse)
@router.get("/card/{card_id}", response_class=HTMLResponse)
def verify_card_html(card_id: str, request: Request):
    """Public verification and printable HTML card page."""
    if not is_safe_card_id(card_id):
        raise HTTPException(status_code=400, detail="Invalid card ID")

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT c.*, r.name as role_name, r.name_hi as role_name_hi
            FROM skill_cards c
            LEFT JOIN job_roles r ON c.role_id = r.id
            WHERE c.id = ?
            LIMIT 1
            """,
            (card_id,)
        ).fetchone()

        if not row:
            return HTMLResponse(
                f"""<!DOCTYPE html>
                <html><head><title>honorary.stats - Verification</title></head>
                <body style="font-family:sans-serif; text-align:center; padding:40px;">
                    <h2>Skill Card Not Found</h2>
                    <p>Card ID: {card_id} is not registered.</p>
                    <a href="/">Back to honorary.stats</a>
                </body></html>""",
                status_code=404
            )

        name = row["name"]
        role = row["role_name"] or "Informal Worker"
        skills = json.loads(row["skills_json"]) if row["skills_json"] else []
        years = row["years_experience"] or 5
        date_str = (row["created_at"] or "")[:10]
        image_url = f"/api/card/{card_id}/image"

        skills_pills = "".join(
            f'<span style="display:inline-block; background:#EEF5EF; color:#5E8A68; padding:6px 12px; margin:4px; border-radius:99px; font-weight:600; font-size:14px;">{s}</span>'
            for s in skills
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>honorary.stats - Verified Profile: {name}</title>
    <style>
        body {{
            background-color: #FAF7F2;
            color: #26292B;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .card-container {{
            max-width: 480px;
            width: 100%;
            background: #FFFFFF;
            border-radius: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.08);
            border: 1px solid rgba(0,0,0,0.06);
            padding: 24px;
            box-sizing: border-box;
            text-align: center;
        }}
        .badge {{
            display: inline-block;
            background: #EEF5EF;
            color: #5E8A68;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 99px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        .worker-name {{ font-size: 24px; font-weight: 800; margin: 12px 0 4px 0; }}
        .worker-role {{ font-size: 16px; color: #C36145; font-weight: 700; margin-bottom: 16px; }}
        .skills-list {{ text-align: left; margin: 16px 0; }}
        .disclaimer {{
            font-size: 12px;
            color: #838A91;
            margin-top: 16px;
            border-top: 1px dashed rgba(0,0,0,0.1);
            padding-top: 12px;
        }}
        .btn {{
            display: inline-block;
            background: #5E8A68;
            color: #FFFFFF;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 12px;
            font-weight: 700;
            margin-top: 16px;
        }}
    </style>
</head>
<body>
    <div class="card-container">
        <span class="badge">✓ Verified Profile</span>
        <div style="font-size:12px; color:#838A91; margin-top:6px;">ID: {card_id}</div>
        <h1 class="worker-name">{name}</h1>
        <div class="worker-role">{role} • {years} Years Experience</div>
        
        <div class="skills-list">
            <div style="font-size:14px; font-weight:700; margin-bottom:6px;">Verified Skills:</div>
            {skills_pills}
        </div>

        <div>
            <img src="{image_url}" alt="Skill Card PNG" style="max-width:100%; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.08);" onerror="this.style.display='none'" />
        </div>

        <div class="disclaimer">
            Self-declared skills, confirmed by the worker. Verified via honorary.stats.
        </div>

        <div style="margin-top:20px;">
            <a href="/" class="btn">Create Your Own Skill Card</a>
        </div>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html)
    finally:
        conn.close()
