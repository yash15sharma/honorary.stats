import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 1. Add REPO_ROOT to sys.path before importing any root modules
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# 2. Load root .env by absolute path
root_env = REPO_ROOT / ".env"
if root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

# App title must strictly be 'honorary.stats'
app = FastAPI(
    title="honorary.stats",
    description="honorary.stats: Voice-first skills verification and career pathway generator for informal workers in India.",
    version="0.1.0",
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """
    Health check endpoint verifying API configuration.
    API contract: { "gemini": bool, "elevenlabs": bool }
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "").strip()

    gemini_ok = bool(gemini_key and len(gemini_key) > 5 and not gemini_key.startswith("your_"))
    elevenlabs_ok = bool(elevenlabs_key and len(elevenlabs_key) > 5 and not elevenlabs_key.startswith("your_"))

    return {
        "gemini": gemini_ok,
        "elevenlabs": elevenlabs_ok,
    }


# Include routers from app/ai.py, app/path.py, app/card.py, app/voice.py
try:
    from app.ai import router as ai_router
    app.include_router(ai_router)
    print("[Router] Loaded app/ai.py router")
except ImportError as e:
    print(f"[Router] Notice loading app/ai.py: {e}")

try:
    from app.path import router as path_router
    app.include_router(path_router)
    print("[Router] Loaded app/path.py router")
except ImportError as e:
    print(f"[Router] Notice loading app/path.py: {e}")

try:
    from app.card import router as card_router
    app.include_router(card_router)
    print("[Router] Loaded app/card.py router")
except ImportError as e:
    print(f"[Router] Notice loading app/card.py: {e}")

try:
    from app.voice import router as voice_router
    app.include_router(voice_router)
    print("[Router] Loaded app/voice.py router")
except ImportError as e:
    print(f"[Router] Notice loading app/voice.py: {e}")


# 3. Mount Cyber SPartans/app/static at /legacy
LEGACY_STATIC_DIR = Path(__file__).resolve().parent / "static"
if LEGACY_STATIC_DIR.exists():
    app.mount("/legacy", StaticFiles(directory=str(LEGACY_STATIC_DIR), html=True), name="legacy_static")

# 4. Mount frontend/app/static at "/" LAST (after all API routes so routes take priority)
FRONTEND_STATIC_DIR = REPO_ROOT / "frontend" / "app" / "static"
if FRONTEND_STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_STATIC_DIR), html=True), name="frontend_static")
else:
    app.mount("/", StaticFiles(directory=str(LEGACY_STATIC_DIR), html=True), name="static")
