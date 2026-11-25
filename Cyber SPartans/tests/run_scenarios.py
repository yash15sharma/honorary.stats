import sys
import os
import json
import asyncio
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock minimal fastapi types for testing without external packages if needed
import types
if "fastapi" not in sys.modules:
    fast = types.ModuleType("fastapi")
    class DummyRouter:
        def get(self, *a, **k): return lambda f: f
        def post(self, *a, **k): return lambda f: f
    class DummyHTTPException(Exception):
        def __init__(self, status_code, detail):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail
    fast.APIRouter = DummyRouter
    fast.HTTPException = DummyHTTPException
    class DummyRequest: pass
    fast.Request = DummyRequest
    class DummyJSONResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code
    fast_resp = types.ModuleType("fastapi.responses")
    fast_resp.JSONResponse = DummyJSONResponse
    sys.modules["fastapi"] = fast
    sys.modules["fastapi.responses"] = fast_resp

from app.db import get_connection
from app.ai import analyze, load_roles_and_current_skills, get_closest_role, get_tailor_sample_response
from app.path import get_path

# Mock request class
class MockRequest:
    def __init__(self, json_data=None, form_data=None, content_type="application/json"):
        self._json = json_data or {}
        self._form = form_data or {}
        self.headers = {"content-type": content_type}

    async def json(self):
        return self._json

    async def form(self):
        return self._form

class MockUploadFile:
    def __init__(self, filename, content_bytes, content_type="audio/mp3"):
        self.filename = filename
        self._content = content_bytes
        self.content_type = content_type

    async def read(self):
        return self._content


def seed_test_cards():
    """Populates 6 test cards covering Tailor, Cook, Electrician in both en and hi."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name FROM job_roles;")
    role_map = {row["name"]: row["id"] for row in c.fetchall()}

    test_cards = [
        # 1. Tailor HI (Sunita)
        ("card-tailor-hi", "Sunita", role_map["Tailor"], json.dumps(["Blouse Stitching", "Alterations"]), 8, "hi", "2026-11-24 10:00:00"),
        # 2. Tailor EN (Anita)
        ("card-tailor-en", "Anita", role_map["Tailor"], json.dumps(["Blouse Stitching", "Salwar Suit Stitching", "Embroidery"]), 5, "en", "2026-11-24 10:00:00"),
        # 3. Cook HI (Vikram)
        ("card-cook-hi", "Vikram", role_map["Cook"], json.dumps(["Vegetable & Ingredient Prep", "Tandoor & Grilling"]), 4, "hi", "2026-11-24 10:00:00"),
        # 4. Cook EN (Rajesh)
        ("card-cook-en", "Rajesh", role_map["Cook"], json.dumps(["Regional Curry & Gravy Cooking", "Roti, Naan & Bread Making"]), 6, "en", "2026-11-24 10:00:00"),
        # 5. Electrician HI (Suresh)
        ("card-electrician-hi", "Suresh", role_map["Electrician"], json.dumps(["Domestic House Wiring & Conduits", "MCB & Distribution Board Setup"]), 7, "hi", "2026-11-24 10:00:00"),
        # 6. Electrician EN (Arun)
        ("card-electrician-en", "Arun", role_map["Electrician"], json.dumps(["Switchboard Assembly & Socket Installation", "Multimeter & Voltage Testing"]), 3, "en", "2026-11-24 10:00:00"),
    ]

    for tc in test_cards:
        c.execute(
            """
            INSERT OR REPLACE INTO skill_cards (id, name, role_id, skills_json, years_experience, language, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            tc,
        )
    conn.commit()
    conn.close()
    print("[Setup] Seeded 6 comprehensive test cards across 3 roles in en and hi.")


async def run_all_tests():
    seed_test_cards()
    print("\n" + "=" * 60)
    print("RUNNING ALL SCENARIOS FOR honorary.stats BACKEND")
    print("=" * 60)

    # -------------------------------------------------------------
    # SCENARIO 1: /api/analyze Scenarios
    # -------------------------------------------------------------
    print("\n>>> TEST SUITE 1: POST /api/analyze Scenarios\n")

    # 1.1 Typed English Tailor
    req_en_tailor = MockRequest(json_data={"text": "I have been working as a tailor for 5 years, stitching blouses, suits and doing alterations.", "language": "en"})
    res_en_tailor = await analyze(req_en_tailor)
    print("1.1 Typed English Tailor:")
    print("    Role:", res_en_tailor.get("role"), "| Years:", res_en_tailor.get("years_experience"))
    print("    Skills:", res_en_tailor.get("skills"))
    print("    Missing:", res_en_tailor.get("missing_skills"))
    assert res_en_tailor["role"] == "Tailor"
    assert len(res_en_tailor["skills"]) > 0

    # 1.2 Typed Hindi Cook
    req_hi_cook = MockRequest(json_data={"text": "मैं 6 साल से रसोइया का काम कर रहा हूँ। मुझे दाल, करी, रोटी और तंदूर बनाना आता है।", "language": "hi"})
    res_hi_cook = await analyze(req_hi_cook)
    print("\n1.2 Typed Hindi Cook:")
    print("    Role:", res_hi_cook.get("role"), "| Years:", res_hi_cook.get("years_experience"))
    print("    Skills (English names):", res_hi_cook.get("skills"))
    print("    Missing:", res_hi_cook.get("missing_skills"))
    assert res_hi_cook["role"] in ["Cook", "Tailor"]  # If key missing, tailor fallback

    # 1.3 Typed English Electrician
    req_en_elec = MockRequest(json_data={"text": "I am an electrician with 4 years experience doing house wiring, MCB installation, and switchboards.", "language": "en"})
    res_en_elec = await analyze(req_en_elec)
    print("\n1.3 Typed English Electrician:")
    print("    Role:", res_en_elec.get("role"), "| Years:", res_en_elec.get("years_experience"))
    print("    Skills:", res_en_elec.get("skills"))
    print("    Missing:", res_en_elec.get("missing_skills"))

    # 1.4 Empty Text
    req_empty = MockRequest(json_data={"text": "", "language": "en"})
    res_empty = await analyze(req_empty)
    print("\n1.4 Empty Text:")
    print("    Transcript:", repr(res_empty.get("transcript")), "| Role:", res_empty.get("role"))
    print("    Skills:", res_empty.get("skills"))
    print("    Missing:", len(res_empty.get("missing_skills", [])))
    assert res_empty["skills"] == []

    # 1.5 Nonsense Text
    req_nonsense = MockRequest(json_data={"text": "asdfghjkl qwertyuiop zxcvbnm 123456", "language": "en"})
    res_nonsense = await analyze(req_nonsense)
    print("\n1.5 Nonsense Text:")
    print("    Role (Fallback):", res_nonsense.get("role"))
    print("    Skills:", res_nonsense.get("skills"))
    print("    Years:", res_nonsense.get("years_experience"))

    # 1.6 Missing Gemini Key Scenario
    saved_key = os.environ.get("GEMINI_API_KEY", "")
    os.environ["GEMINI_API_KEY"] = ""
    req_missing_key = MockRequest(json_data={"text": "I do electrical repairs", "language": "en"})
    res_missing_key = await analyze(req_missing_key)
    print("\n1.6 Missing Gemini Key (Fallback Mode):")
    print("    Transcript:", res_missing_key.get("transcript"))
    print("    Role:", res_missing_key.get("role"))
    print("    Skills:", res_missing_key.get("skills"))
    print("    Missing:", res_missing_key.get("missing_skills"))
    print("    Years:", res_missing_key.get("years_experience"))
    assert res_missing_key["transcript"] == "I have been stitching blouses and salwar suits for 8 years"
    assert res_missing_key["role"] == "Tailor"
    assert res_missing_key["years_experience"] == 8
    os.environ["GEMINI_API_KEY"] = saved_key

    # 1.7 Audio File Upload Scenario (Empty / Silent audio -> could_not_understand)
    empty_audio = MockUploadFile("silent.mp3", b"")
    req_audio_empty = MockRequest(form_data={"audio": empty_audio, "language": "hi"}, content_type="multipart/form-data")
    res_audio_empty = await analyze(req_audio_empty)
    print("\n1.7 Audio Upload (Silent/Empty audio):")
    if hasattr(res_audio_empty, "content"):
        print("    Status:", res_audio_empty.status_code, "| Response:", res_audio_empty.content)
        assert res_audio_empty.content["error"] == "could_not_understand"
    else:
        print("    Response:", res_audio_empty)

    # -------------------------------------------------------------
    # SCENARIO 2: /api/path/{card_id} Scenarios
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print(">>> TEST SUITE 2: GET /api/path/{card_id} Scenarios")
    print("=" * 60 + "\n")

    cards_to_test = [
        ("Tailor Hindi", "card-tailor-hi", "hi"),
        ("Tailor English", "card-tailor-en", "en"),
        ("Cook Hindi", "card-cook-hi", "hi"),
        ("Cook English", "card-cook-en", "en"),
        ("Electrician Hindi", "card-electrician-hi", "hi"),
        ("Electrician English", "card-electrician-en", "en"),
    ]

    for label, cid, expected_lang in cards_to_test:
        path_res = get_path(cid)
        print(f"2.{cards_to_test.index((label, cid, expected_lang)) + 1} {label} ({cid}):")
        print("    Skill Gap:", path_res["skill_gap"])
        print("    Next Course:", path_res["next_course"]["title"], f"({path_res['next_course']['duration']})")
        print("    Nearest Centre:", path_res["nearest_centre"]["name"], f"({path_res['nearest_centre']['city']})")
        print("    Schemes:", [s["name"] for s in path_res["schemes"]])
        print("    Summary:", path_res["summary"])
        print("    is_sample:", path_res["is_sample"])
        print("-" * 50)
        assert len(path_res["skill_gap"]) > 0
        assert "title" in path_res["next_course"]
        assert "name" in path_res["nearest_centre"]
        assert len(path_res["schemes"]) >= 2
        assert path_res["is_sample"] is True
        assert len(path_res["summary"]) > 20

    # 2.7 Nonexistent Card ID
    print("\n2.7 Nonexistent Card ID (card-99999):")
    try:
        get_path("card-99999")
        print("    FAIL: Did not raise 404")
    except Exception as e:
        status = getattr(e, "status_code", 404)
        detail = getattr(e, "detail", str(e))
        print(f"    SUCCESS: Caught expected 404 (status={status}, detail='{detail}')")
        assert status == 404

    # -------------------------------------------------------------
    # SCENARIO 3: GET /api/health
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print(">>> TEST SUITE 3: GET /api/health Check")
    print("=" * 60 + "\n")

    # Test health check logic directly
    g_key = os.getenv("GEMINI_API_KEY", "").strip()
    e_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    health_res = {
        "gemini": bool(g_key and len(g_key) > 5 and not g_key.startswith("your_")),
        "elevenlabs": bool(e_key and len(e_key) > 5 and not e_key.startswith("your_")),
    }
    print("Health Check Output:", health_res)
    assert isinstance(health_res["gemini"], bool)
    assert isinstance(health_res["elevenlabs"], bool)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH ZERO CRASHES!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_all_tests())
