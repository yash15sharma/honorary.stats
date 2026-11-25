import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env
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
# Each router import is wrapped in its own try/except ImportError so the app runs smoothly
# even if other teammates haven't created their files yet.

try:
    from app.ai import router as ai_router
    app.include_router(ai_router)
    print("[Router] Loaded app/ai.py router")
except ImportError:
    pass

try:
    from app.path import router as path_router
    app.include_router(path_router)
    print("[Router] Loaded app/path.py router")
except ImportError:
    pass

try:
    from app.card import router as card_router
    app.include_router(card_router)
    print("[Router] Loaded app/card.py router")
except ImportError:
    pass

try:
    from app.voice import router as voice_router
    app.include_router(voice_router)
    print("[Router] Loaded app/voice.py router")
except ImportError:
    pass


# Serve app/static/ at "/" AFTER API routes so API endpoints take priority
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Ensure placeholder index.html exists
index_file = STATIC_DIR / "index.html"
if not index_file.exists():
    index_file.write_text(
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>honorary.stats</title>
</head>
<body>
    <h1>honorary.stats</h1>
    <p>Voice-first skills recognition & career pathway for informal workers in India.</p>
</body>
</html>
""",
        encoding="utf-8",
    )

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
